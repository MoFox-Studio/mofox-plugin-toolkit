"""
插件市场相关命令实现
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from rich.table import Table

from mpdt.commands.build import build_plugin
from mpdt.utils.color_printer import console, print_error, print_info, print_success, print_warning
from mpdt.utils.managers.config_manager import get_or_init_mpdt_config
from mpdt.utils.managers.git_manager import GitManager
from mpdt.utils.managers.github_manager import GitHubError, GitHubManager
from mpdt.utils.managers.manifest_manager import ManifestManager
from mpdt.utils.managers.market_manager import MarketError, MarketManager


def _resolve_github_token(token_arg: str | None) -> str:
    """解析 GitHub Token
    
    Args:
        token_arg: 命令行传入的 token
        
    Returns:
        GitHub Token
        
    Raises:
        SystemExit: 如果无法获取 token
    """
    # 优先级：命令行参数>配置文件
    token = (
        token_arg
        or get_or_init_mpdt_config().github_token
    )
    
    if not token:
        print_error("未找到 GitHub Token")
        print_info("请通过以下方式之一提供 GitHub Token：")
        print_info("  1. 使用 --github-token 参数")
        print_info("  2. 设置环境变量 GITHUB_TOKEN")
        print_info("  3. 运行 'mpdt config set-github-token' 保存到配置文件")
        print_warning("提示：GitHub Token 需要有仓库创建和 Release 写入权限")
        sys.exit(1)
    
    return token


def _run_async(coro):
    """运行异步函数"""
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt:
        print_warning("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        print_error(f"操作失败: {e}")
        sys.exit(1)


def market_publish(
    plugin_path: str = ".",
    token: str | None = None,
    github_token: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    private: bool = False,
    output_dir: str = "dist",
    with_docs: bool = False,
    release_notes: str | None = None,
    skip_push: bool = False,
    save_token: bool | None = None,
) -> None:
    """一键发布插件到市场
    
    完整流程：
    1. 构建插件包
    2. 创建/确认 GitHub 仓库
    3. 提交代码并创建 tag
    4. 推送到 GitHub
    5. 创建 Release 并上传资产
    6. 注册/更新市场插件信息
    7. 提交版本到市场
    """
    
    async def run() -> None:
        plugin_dir = Path(plugin_path).resolve()
        
        # 1. 加载 manifest
        print_info("正在加载插件信息...")
        manifest_mgr = ManifestManager(plugin_dir)
        manifest = manifest_mgr.load()
        if not manifest:
            print_error("无法加载 manifest.json")
            return
        
        plugin_id = manifest_mgr.get_plugin_id()
        version = manifest_mgr.get_version()
        print_success(f"插件: {plugin_id} v{version}")
        
        # 2. 构建插件包
        print_info("正在构建插件包...")
        package = build_plugin(
            plugin_path=str(plugin_dir),
            output_dir=output_dir,
            with_docs=with_docs,
            fmt="mfp",
        )
        if not package:
            print_error("插件包构建失败")
            return
        print_success(f"插件包已构建: {package.package_path.name}")
        
        # 3. 处理 GitHub Token
        resolved_github_token = _resolve_github_token(github_token)
        
        # 保存 token（如果需要）
        if github_token and save_token is True:
            config = get_or_init_mpdt_config()
            config.github_token = github_token
            config.save()
            print_success("GitHub Token 已保存到配置文件")
        elif github_token and save_token is None:
            # 询问是否保存
            try:
                from rich.prompt import Confirm
                if Confirm.ask("是否保存 GitHub Token 到配置文件以便下次使用？", default=False):
                    config = get_or_init_mpdt_config()
                    config.github_token = github_token
                    config.save()
                    print_success("GitHub Token 已保存")
            except Exception:
                pass
        
        # 4. 初始化 GitHub 客户端
        github = GitHubManager(resolved_github_token)
        user = await github.get_current_user()
        resolved_owner = owner or manifest.get("github_owner") or user["login"]
        resolved_repo = repo or manifest.get("github_repo") or plugin_id
        
        print_info(f"GitHub 仓库: {resolved_owner}/{resolved_repo}")
        
        # 5. 确保 GitHub 仓库存在
        print_info("正在检查 GitHub 仓库...")
        repository = await github.ensure_repo(
            resolved_owner,
            resolved_repo,
            description=str(
                manifest.get("summary") or manifest.get("description") or f"{plugin_id} 插件"
            ),
            private=private,
        )
        repo_url = repository["html_url"]
        clone_url = repository["clone_url"]
        print_success(f"仓库地址: {repo_url}")
        
        # 6. Git 操作
        git_mgr = GitManager(plugin_dir)
        if not git_mgr.is_git_repo():
            print_info("正在初始化 Git 仓库...")
            git_mgr.init_repository(initial_commit=False)
        
        # 设置远程仓库
        git_mgr.set_remote(clone_url)
        
        # 确保有提交
        print_info("正在提交代码...")
        git_mgr.ensure_commit(f"Release {version}")
        
        # 创建 tag
        tag = manifest_mgr.build_release_tag(version)
        print_info(f"正在创建标签: {tag}")
        git_mgr.ensure_tag(tag, f"Release {version}")
        
        # 推送（除非跳过）
        if not skip_push:
            print_info("正在推送到 GitHub...")
            branch = git_mgr.get_current_branch() or "main"
            
            # 使用带 token 的 URL 推送
            push_url = GitManager.build_github_push_url(
                resolved_owner, resolved_repo, resolved_github_token
            )
            git_mgr.set_remote(push_url, "origin_temp")
            
            success, msg = git_mgr.push("origin_temp", branch)
            if not success:
                print_warning(f"推送分支失败: {msg}")
            
            success, msg = git_mgr.push_tag(tag, "origin_temp")
            if not success:
                print_warning(f"推送标签失败: {msg}")
            
            # 恢复原始远程 URL
            git_mgr.set_remote(clone_url)
            
            print_success("代码已推送")
        else:
            print_info("跳过 Git 推送（--skip-push）")
        
        # 7. 创建 GitHub Release
        release_title = f"{plugin_id} {version}"
        release_body = (
            release_notes
            or manifest.get("release_notes")
            or f"Release {version}"
        )
        is_prerelease = "-" in version
        
        print_info(f"正在创建 Release: {tag}")
        release = await github.ensure_release(
            resolved_owner,
            resolved_repo,
            tag,
            release_title,
            release_body,
            is_prerelease,
        )
        print_success(f"Release 已创建")
        
        # 8. 上传资产
        print_info(f"正在上传资产: {package.package_path.name}")
        asset = await github.upload_asset(release, package.package_path)
        print_success("资产已上传")
        
        release_url = release.get("html_url") or manifest_mgr.build_default_release_url()
        asset_url = asset.get("browser_download_url") or manifest_mgr.build_default_asset_url(package.package_path.name)
        
        # 9. 注册/更新市场插件
        market = MarketManager(token or resolved_github_token)
        
        print_info("正在注册插件到市场...")
        plugin_payload = manifest_mgr.build_market_plugin_payload(repository_url=repo_url)
        
        try:
            result = await market.register_plugin(plugin_payload)
            print_success(f"插件已注册: {result.get('plugin_id')} ({result.get('status')})")
        except MarketError as e:
            if "PLUGIN_ALREADY_EXISTS" in str(e):
                # 更新插件信息
                update_payload = dict(plugin_payload)
                update_payload.pop("plugin_id", None)
                result = await market.update_plugin(plugin_id, update_payload)
                print_success(f"插件信息已更新: {result.get('plugin_id')}")
            else:
                raise
        
        # 10. 提交版本
        print_info("正在提交版本到市场...")
        version_payload = manifest_mgr.build_market_version_payload(
            asset_name=package.package_path.name,
            asset_download_url=asset_url,
            release_url=release_url,
            sha256=package.sha256,
            file_size=package.package_size,
        )
        
        try:
            result = await market.submit_version(plugin_id, version_payload)
            print_success(f"版本已提交: {plugin_id}@{result.get('version')} ({result.get('status')})")
        except MarketError as e:
            if "VERSION_ALREADY_EXISTS" in str(e):
                # 同步版本信息
                sync_payload = {
                    "version": version,
                    "release_url": release_url,
                    "release_title": release_title,
                    "asset_name": package.package_path.name,
                    "asset_download_url": asset_url,
                    "checksum_sha256": package.sha256,
                    "file_size": package.package_size,
                }
                result = await market.sync_version(plugin_id, sync_payload)
                print_success(f"版本信息已同步: {plugin_id}@{result.get('version')}")
            else:
                raise
        
        print_success(f"\n发布完成！")
        print_info(f"Release 地址: {release_url}")
        print_info(f"下载地址: {asset_url}")
    
    _run_async(run())


def market_search(
    query: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    limit: int = 20,
) -> None:
    """搜索市场中的公开插件并显示结果"""
    
    async def run() -> None:
        market = MarketManager(None)
        result = await market.search_plugins(query, category, tag, limit)
        
        # API 返回 PluginListResponse: {"items": [...], "total": N}
        plugins = result.get("items", [])
        total = result.get("total", 0)
        
        if not plugins:
            print_info("未找到匹配的插件")
            return
        
        table = Table(title="搜索结果")
        table.add_column("插件 ID", style="cyan")
        table.add_column("名称", style="green")
        table.add_column("描述", style="white")
        
        for plugin in plugins:
            table.add_row(
                str(plugin.get("plugin_id", "")),
                str(plugin.get("display_name", "")),
                str(plugin.get("summary", ""))[:50],
            )
        
        console.print(table)
        print_info(f"共找到 {total} 个插件（显示 {len(plugins)} 个）")
    
    _run_async(run())


def market_info(plugin_id: str) -> None:
    """查看插件的详细信息"""
    
    async def run() -> None:
        market = MarketManager(None)
        result = await market.get_plugin_detail(plugin_id)
        
        table = Table(title=f"插件详情: {plugin_id}")
        table.add_column("字段", style="cyan")
        table.add_column("值", style="green")
        
        for key, value in result.items():
            if isinstance(value, (list, dict)):
                value = str(value)[:100]
            table.add_row(str(key), str(value))
        
        console.print(table)
    
    _run_async(run())

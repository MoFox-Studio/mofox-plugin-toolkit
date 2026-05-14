"""
CLI 主入口
"""

import click
from rich.console import Console

from mpdt import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="MPDT - Neo-MoFox 插件开发工具")
@click.option("--verbose", "-v", is_flag=True, help="详细输出模式")
@click.option("--no-color", is_flag=True, help="禁用彩色输出")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, no_color: bool) -> None:
    """
    MoFox Plugin Dev Toolkit - Neo-MoFox 插件开发工具

    一个类似 Vite 的开发工具，用于快速创建、开发和测试 Neo-MoFox 插件。
    """
    # 设置上下文对象
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["no_color"] = no_color

    # 禁用彩色输出
    if no_color:
        console._color_system = None

    if verbose:
        console.print(f"[bold green]MPDT v{__version__}[/bold green]")


@cli.command()
@click.argument("plugin_name", required=False)
@click.option("--template", "-t", type=click.Choice(["basic", "action", "tool", "collection", "router", "plus_command", "event_handler", "full", "adapter", "chatter"]),
              default="basic", help="插件模板类型")
@click.option("--author", "-a", help="作者名称")
@click.option("--email", "-e", help="作者电子邮箱")
@click.option("--license", "-l", type=click.Choice(["GPL-v3.0", "MIT", "Apache-2.0", "BSD-3-Clause"]),
              default="GPL-v3.0", help="开源协议")
@click.option("--with-docs", is_flag=True, help="创建文档文件")
@click.option("--init-git/--no-init-git", default=None, help="是否初始化 Git 仓库")
@click.option("--output", "-o", type=click.Path(), help="输出目录")
@click.pass_context
def init(ctx: click.Context, plugin_name: str | None, template: str,email: str|  None, author: str | None,
         license: str, with_docs: bool, init_git: bool | None, output: str | None) -> None:
    """初始化新插件项目"""
    from mpdt.commands.init import init_plugin

    try:
        init_plugin(
            plugin_name=plugin_name,
            template=template,
            author=author,
            license_type=license,
            email = email,
            with_docs=with_docs,
            init_git=init_git,
            output_dir=output,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 初始化失败: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("component_type", type=click.Choice(["action", "tool", "collection", "event", "adapter", "plus-command", "router", "chatter", "service", "config"]), required=False)
@click.argument("component_name", required=False)
@click.option("--description", "-d", help="组件描述")
@click.option("--output", "-o", type=click.Path(), help="插件根目录路径（默认为当前目录）")
@click.option("--force", "-f", is_flag=True, help="覆盖已存在的文件")
@click.option("--root", is_flag=True, help="在插件根目录生成组件文件，而不是 components/ 文件夹")
@click.pass_context
def generate(ctx: click.Context, component_type: str | None, component_name: str | None, description: str | None,
             output: str | None, force: bool, root: bool) -> None:
    """生成插件组件(始终生成异步方法)

    如果不提供参数，将进入交互式问答模式
    """
    from mpdt.commands.generate import generate_component

    try:
        generate_component(
            component_type=component_type,
            component_name=component_name,
            description=description,
            output_dir=output,
            force=force,
            use_components_folder=not root,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 生成失败: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("path", type=click.Path(exists=True), required=False, default=".")
@click.option("--level", "-l", type=click.Choice(["error", "warning", "info"]), default="warning",
              help="显示的最低级别")
@click.option("--fix", is_flag=True, help="自动修复可修复的问题")
@click.option("--report", type=click.Choice(["console","markdown","json"]), default="console",
              help="输出报告的格式")
@click.option("--output", "-o", type=click.Path(), help="报告输出路径")
@click.option("--no-structure", is_flag=True, help="跳过结构检查")
@click.option("--no-metadata", is_flag=True, help="跳过元数据检查")
@click.option("--no-component", is_flag=True, help="跳过组件检查")
@click.option("--no-type", is_flag=True, help="跳过类型检查")
@click.option("--no-style", is_flag=True, help="跳过代码风格检查")
@click.pass_context
def check(ctx: click.Context, path: str, level: str, fix: bool, report: str, output: str | None,
          no_structure: bool, no_metadata: bool, no_component: bool, no_type: bool,
          no_style: bool) -> None:
    """对插件进行静态检查"""
    from mpdt.commands.check import check_plugin

    try:
        check_plugin(
            plugin_path=path,
            level=level,
            auto_fix=fix,
            report_format=report,
            output_path=output,
            skip_structure=no_structure,
            skip_metadata=no_metadata,
            skip_component=no_component,
            skip_type=no_type,
            skip_style=no_style,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 检查失败: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--output", "-o", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
@click.option("--format", "fmt", type=click.Choice(["mfp", "zip"]), default="mfp", help="构建格式（mfp 为推荐格式）")
@click.option("--bump", type=click.Choice(["major", "minor", "patch"]), help="自动升级版本号")
@click.pass_context
def build(ctx: click.Context, plugin_path: str, output: str, with_docs: bool, fmt: str, bump: str | None) -> None:
    """构建并打包插件为 .mfp 文件

    PLUGIN_PATH 为插件根目录（含 manifest.json），默认为当前目录。
    """
    from mpdt.commands.build import build_plugin

    try:
        build_plugin(
            plugin_path=plugin_path,
            output_dir=output,
            with_docs=with_docs,
            fmt=fmt,
            bump=bump,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 构建失败: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.option("--neo-mofox-path", type=click.Path(exists=True), help="Neo-MoFox 主程序路径")
@click.option("--plugin-path", type=click.Path(exists=True), help="插件路径（默认当前目录）")
@click.pass_context
def dev(ctx: click.Context, neo_mofox_path: str | None, plugin_path: str | None) -> None:
    """启动开发模式，支持热重载"""
    from pathlib import Path

    from mpdt.commands.dev import dev_command

    try:
        dev_command(
            plugin_path=Path(plugin_path) if plugin_path else None,
            mofox_path=Path(neo_mofox_path) if neo_mofox_path else None
        )
    except Exception as e:
        console.print(f"[bold red]❌ 启动失败: {e}[/bold red]")
        if ctx.obj.get("verbose"):
            import traceback
            traceback.print_exc()
        raise click.Abort()


@cli.group()
def market() -> None:
    """插件市场命令"""
    pass


@market.command("doctor")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
def market_doctor_cmd(market_url: str | None, token: str | None) -> None:
    """检查中心服务器连通性"""
    from mpdt.commands.market import market_doctor

    market_doctor(market_url=market_url, token=token)


@market.command("register")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
@click.option("--repository-url", help="插件 GitHub 仓库地址")
def market_register_cmd(plugin_path: str, market_url: str | None, token: str | None, repository_url: str | None) -> None:
    """注册插件到中心服务器"""
    from mpdt.commands.market import market_register

    market_register(plugin_path=plugin_path, market_url=market_url, token=token, repository_url=repository_url)


@market.command("update")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
@click.option("--repository-url", help="插件 GitHub 仓库地址")
def market_update_cmd(plugin_path: str, market_url: str | None, token: str | None, repository_url: str | None) -> None:
    """更新中心服务器插件元数据"""
    from mpdt.commands.market import market_update

    market_update(plugin_path=plugin_path, market_url=market_url, token=token, repository_url=repository_url)


@market.command("package")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--output", "output_dir", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
def market_package_cmd(plugin_path: str, output_dir: str, with_docs: bool) -> None:
    """生成市场发布产物元数据"""
    from mpdt.commands.market import market_package

    market_package(plugin_path=plugin_path, output_dir=output_dir, with_docs=with_docs)


@market.command("submit-version")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
@click.option("--asset-url", help="Release 资产下载地址")
@click.option("--release-url", help="GitHub Release 页面地址")
@click.option("--output", "output_dir", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
def market_submit_version_cmd(
    plugin_path: str,
    market_url: str | None,
    token: str | None,
    asset_url: str | None,
    release_url: str | None,
    output_dir: str,
    with_docs: bool,
) -> None:
    """打包并提交插件版本"""
    from mpdt.commands.market import market_submit_version

    market_submit_version(
        plugin_path=plugin_path,
        market_url=market_url,
        token=token,
        asset_url=asset_url,
        release_url=release_url,
        output_dir=output_dir,
        with_docs=with_docs,
    )


@market.command("sync")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
@click.option("--asset-url", help="Release 资产下载地址")
@click.option("--release-url", help="GitHub Release 页面地址")
@click.option("--output", "output_dir", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
def market_sync_cmd(
    plugin_path: str,
    market_url: str | None,
    token: str | None,
    asset_url: str | None,
    release_url: str | None,
    output_dir: str,
    with_docs: bool,
) -> None:
    """同步插件版本元数据"""
    from mpdt.commands.market import market_sync

    market_sync(
        plugin_path=plugin_path,
        market_url=market_url,
        token=token,
        asset_url=asset_url,
        release_url=release_url,
        output_dir=output_dir,
        with_docs=with_docs,
    )


@market.command("publish")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
@click.option("--github-token", help="GitHub token；也可使用 GITHUB_TOKEN 或 GH_TOKEN")
@click.option("--owner", help="GitHub 用户或组织名；默认使用当前 GitHub token 用户")
@click.option("--repo", help="GitHub 仓库名；默认使用插件 ID")
@click.option("--private", is_flag=True, help="新建私有仓库")
@click.option("--output", "output_dir", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
@click.option("--release-notes", help="GitHub Release 说明")
@click.option("--skip-push", is_flag=True, help="跳过 git push，仅创建/复用 Release 并同步市场")
@click.option("--save-github-token/--no-save-github-token", default=None, help="是否保存本次传入的 GitHub token")
def market_publish_cmd(
    plugin_path: str,
    market_url: str | None,
    token: str | None,
    github_token: str | None,
    owner: str | None,
    repo: str | None,
    private: bool,
    output_dir: str,
    with_docs: bool,
    release_notes: str | None,
    skip_push: bool,
    save_github_token: bool | None,
) -> None:
    """一键发布：建仓库、推送 tag、创建 Release、上传产物并同步市场"""
    from mpdt.commands.market import market_publish

    market_publish(
        plugin_path=plugin_path,
        market_url=market_url,
        token=token,
        github_token=github_token,
        owner=owner,
        repo=repo,
        private=private,
        output_dir=output_dir,
        with_docs=with_docs,
        release_notes=release_notes,
        skip_push=skip_push,
        save_token=save_github_token,
    )


@market.command("status")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--plugin-id", help="插件 ID，不提供则读取 manifest.json")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
def market_status_cmd(plugin_path: str, plugin_id: str | None, market_url: str | None, token: str | None) -> None:
    """查询插件市场状态"""
    from mpdt.commands.market import market_status

    market_status(plugin_path=plugin_path, plugin_id=plugin_id, market_url=market_url, token=token)


@market.command("yank")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--version", help="插件版本，不提供则读取 manifest.json")
@click.option("--market-url", help="中心服务器地址")
@click.option("--token", help="中心服务器访问令牌")
@click.option("--reason", help="撤回原因")
def market_yank_cmd(plugin_path: str, version: str | None, market_url: str | None, token: str | None, reason: str | None) -> None:
    """撤回插件版本"""
    from mpdt.commands.market import market_yank

    market_yank(plugin_path=plugin_path, version=version, market_url=market_url, token=token, reason=reason)


@market.command("search")
@click.argument("query", required=False)
@click.option("--category", help="分类过滤")
@click.option("--tag", help="标签过滤")
@click.option("--limit", type=int, default=20, help="返回数量")
@click.option("--market-url", help="中心服务器地址")
def market_search_cmd(query: str | None, category: str | None, tag: str | None, limit: int, market_url: str | None) -> None:
    """搜索公开插件"""
    from mpdt.commands.market import market_search

    market_search(query=query, category=category, tag=tag, limit=limit, market_url=market_url)


@market.command("info")
@click.argument("plugin_id")
@click.option("--market-url", help="中心服务器地址")
def market_info_cmd(plugin_id: str, market_url: str | None) -> None:
    """查看公开插件详情"""
    from mpdt.commands.market import market_info

    market_info(plugin_id=plugin_id, market_url=market_url)


@market.command("install-info")
@click.argument("plugin_id")
@click.option("--market-url", help="中心服务器地址")
@click.option("--host-version", help="当前 Neo-MoFox 宿主版本")
@click.option("--plugin-api-version", help="插件 API 版本")
@click.option("--platform", help="目标平台，例如 windows/linux/macos")
@click.option("--include-prerelease", is_flag=True, help="允许推荐预发布版本")
def market_install_info_cmd(
    plugin_id: str,
    market_url: str | None,
    host_version: str | None,
    plugin_api_version: str | None,
    platform: str | None,
    include_prerelease: bool,
) -> None:
    """查看推荐安装版本元数据"""
    from mpdt.commands.market import market_install_info

    market_install_info(
        plugin_id=plugin_id,
        market_url=market_url,
        host_version=host_version,
        plugin_api_version=plugin_api_version,
        platform=platform,
        include_prerelease=include_prerelease,
    )


@cli.group()
def config() -> None:
    """配置管理"""
    pass


@config.command("init")
def config_init() -> None:
    """交互式配置向导"""
    from mpdt.utils.config_manager import interactive_config

    try:
        interactive_config()
    except Exception as e:
        console.print(f"[bold red]❌ 配置失败: {e}[/bold red]")
        raise click.Abort()


@config.command("show")
def config_show() -> None:
    """显示当前配置"""
    from rich.table import Table

    from mpdt.utils.config_manager import MPDTConfig

    try:
        config = MPDTConfig()

        if not config.is_configured():
            console.print("[yellow]⚠️  未找到配置文件[/yellow]")
            console.print("请运行 [cyan]mpdt config init[/cyan] 进行配置")
            return

        table = Table(title="MPDT 配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        table.add_row("配置文件", str(config.config_path))
        table.add_row("Neo-MoFox 路径", str(config.mofox_path) if config.mofox_path else "[red]未配置[/red]")
        table.add_row("自动重载", "是" if config.auto_reload else "否")
        table.add_row("重载延迟", f"{config.reload_delay}秒")

        console.print(table)

        # 显示 Python 命令
        console.print("\n[bold]Python 命令:[/bold]")
        console.print(f"  {' '.join(config.get_python_command())}")

    except Exception as e:
        console.print(f"[bold red]❌ 读取配置失败: {e}[/bold red]")
        raise click.Abort()


@config.command("test")
def config_test() -> None:
    """测试配置是否有效"""
    from mpdt.utils.config_manager import MPDTConfig

    try:
        config = MPDTConfig()

        if not config.is_configured():
            console.print("[yellow]⚠️  未找到配置文件[/yellow]")
            console.print("请运行 [cyan]mpdt config init[/cyan] 进行配置")
            return

        console.print("[cyan]正在验证配置...[/cyan]\n")

        valid, errors = config.validate()

        if valid:
            console.print("[bold green]✓ 配置有效！[/bold green]")
            console.print(f"\nNeo-MoFox 路径: {config.mofox_path}")
            console.print(f"Python 命令: {' '.join(config.get_python_command())}")
        else:
            console.print("[bold red]✗ 配置验证失败：[/bold red]")
            for error in errors:
                console.print(f"  - {error}")
            console.print("\n请运行 [cyan]mpdt config init[/cyan] 重新配置")

    except Exception as e:
        console.print(f"[bold red]❌ 测试失败: {e}[/bold red]")
        raise click.Abort()


@config.command("set-mofox")
@click.argument("path", type=click.Path(exists=True))
def config_set_mofox(path: str) -> None:
    """设置 Neo-MoFox 主程序路径"""
    from pathlib import Path

    from mpdt.utils.config_manager import MPDTConfig

    try:
        config = MPDTConfig()
        config.mofox_path = Path(path)
        config.save()

        console.print(f"[green]✓ Neo-MoFox 路径已设置: {path}[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ 设置失败: {e}[/bold red]")
        raise click.Abort()


def main() -> None:
    """主入口函数"""
    cli(obj={})


if __name__ == "__main__":
    main()

"""
CLI 主入口
"""

import click
from rich.console import Console

from mpdt import __version__
from mpdt.utils.color_printer import (
    console,
    print_colored,
    print_error,
    print_info,
    print_success,
    print_warning,
)


@click.group()
@click.version_option(version=__version__, prog_name="MPDT - Neo-MoFox 插件开发工具")
@click.option("--no-color", is_flag=True, help="禁用彩色输出")
@click.pass_context
def cli(ctx: click.Context, no_color: bool) -> None:
    """
    MoFox Plugin Dev Toolkit - Neo-MoFox 插件开发工具

    一个类似 Vite 的开发工具，用于快速创建、开发和测试 Neo-MoFox 插件。
    """
    # 设置上下文对象
    ctx.ensure_object(dict)
    ctx.obj["no_color"] = no_color

    # 禁用彩色输出
    if no_color:
        console._color_system = None


@cli.group()
def plugin() -> None:
    """插件开发工具"""
    pass


@plugin.command("init")
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
def plugin_init(ctx: click.Context, plugin_name: str | None, template: str,email: str|  None, author: str | None,
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
        )
    except Exception as e:
        print_error(f"初始化失败: {e}")
        raise click.Abort()


@plugin.command("generate")
@click.argument("component_type", type=click.Choice(["action", "tool", "collection", "event", "adapter", "plus-command", "router", "chatter", "service", "config"]), required=False)
@click.argument("component_name", required=False)
@click.argument("path", type=click.Path(), required=False, default=".")
@click.option("--description", "-d", help="组件描述")
@click.option("--force", "-f", is_flag=True, help="覆盖已存在的文件")
@click.option("--root", is_flag=True, help="在插件根目录生成组件文件，而不是 components/ 文件夹")
@click.pass_context
def plugin_generate(ctx: click.Context, component_type: str | None, component_name: str | None, path: str,
             description: str | None, force: bool, root: bool) -> None:
    """生成插件组件(始终生成异步方法)

    PATH 为插件根目录路径，默认为当前目录。
    
    如果不提供参数，将进入交互式问答模式
    """
    from mpdt.commands.generate import generate_component

    try:
        generate_component(
            component_type=component_type,
            component_name=component_name,
            description=description,
            output_dir=path,
            force=force,
            use_components_folder=not root,
        )
    except Exception as e:
        print_error(f"生成失败: {e}")
        raise click.Abort()


@plugin.command("check")
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
@click.option("--no-import", is_flag=True, help="跳过导入检查")
@click.option("--no-config", is_flag=True, help="跳过配置检查")
@click.option("--no-style", is_flag=True, help="跳过代码风格检查")
@click.pass_context
def plugin_check(ctx: click.Context, path: str, level: str, fix: bool, report: str, output: str | None,
          no_structure: bool, no_metadata: bool, no_component: bool, no_type: bool,no_import: bool, no_config: bool,
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
            skip_import=no_import,
            skip_config=no_config,
        )
    except Exception as e:
        print_error(f"检查失败: {e}")
        raise click.Abort()


@plugin.command("bump")
@click.argument("path", type=click.Path(), required=False, default=".")
@click.option("--type", "-t", "bump_type", type=click.Choice(["major", "minor", "patch"]), default="patch", help="版本升级类型")
@click.pass_context
def plugin_bump(ctx: click.Context, path: str, bump_type: str) -> None:
    """提升插件版本号

    PLUGIN_PATH 为插件根目录（含 manifest.json），默认为当前目录。
    
    版本升级类型：
    - major: 主版本号 (1.0.0 -> 2.0.0)
    - minor: 次版本号 (1.0.0 -> 1.1.0)  
    - patch: 修订号 (1.0.0 -> 1.0.1)
    """
    from mpdt.commands.bump import bump_plugin_version

    try:
        bump_plugin_version(
            plugin_path=path,
            bump_type=bump_type,
        )
    except Exception as e:
        print_error(f"版本升级失败: {e}")
        raise click.Abort()


@plugin.command("build")
@click.argument("path", type=click.Path(), required=False, default=".")
@click.option("--output", "-o", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
@click.option("--format", "fmt", type=click.Choice(["mfp", "zip"]), default="mfp", help="构建格式（mfp 为推荐格式）")
@click.pass_context
def plugin_build(ctx: click.Context, path: str, output: str, with_docs: bool, fmt: str) -> None:
    """构建并打包插件为 .mfp 文件

    PLUGIN_PATH 为插件根目录（含 manifest.json），默认为当前目录。
    """
    from mpdt.commands.build import build_plugin

    try:
        build_plugin(
            plugin_path=path,
            output_dir=output,
            with_docs=with_docs,
            fmt=fmt,
        )
    except Exception as e:
        print_error(f"构建失败: {e}")
        raise click.Abort()


@plugin.command("dev")
@click.argument("path", type=click.Path(exists=True), required=False)
@click.option("--neo-mofox-path", type=click.Path(exists=True), help="Neo-MoFox 主程序路径")
@click.pass_context
def plugin_dev(ctx: click.Context, path: str | None, neo_mofox_path: str | None) -> None:
    """启动开发模式，支持热重载
    
    PATH 为插件路径，默认为当前目录。
    """
    from pathlib import Path

    from mpdt.commands.dev import dev_command

    try:
        dev_command(
            plugin_path=Path(path) if path else None,
            mofox_path=Path(neo_mofox_path) if neo_mofox_path else None
        )
    except Exception as e:
        print_error(f"启动失败: {e}")
        raise click.Abort()


@cli.group()
def market() -> None:
    """插件市场管理"""
    pass


@market.command("publish")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--owner", help="GitHub 用户或组织名")
@click.option("--repo", help="GitHub 仓库名（默认使用插件 ID）")
@click.option("--private", is_flag=True, help="创建私有仓库")
@click.option("--output", "output_dir", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
@click.option("--release-notes", help="Release 说明")
@click.option("--skip-push", is_flag=True, help="跳过 Git 推送")
def market_publish_cmd(
    plugin_path: str,
    owner: str | None,
    repo: str | None,
    private: bool,
    output_dir: str,
    with_docs: bool,
    release_notes: str | None,
    skip_push: bool,
) -> None:
    """一键发布插件到市场
    
    完整流程：构建 -> GitHub 仓库 -> Release -> 市场注册
    """
    from mpdt.commands.market import market_publish

    try:
        market_publish(
            plugin_path=plugin_path,
            owner=owner,
            repo=repo,
            private=private,
            output_dir=output_dir,
            with_docs=with_docs,
            release_notes=release_notes,
            skip_push=skip_push,
        )
    except Exception as e:
        print_error(f"发布失败: {e}")
        raise click.Abort()


@market.command("search")
@click.argument("query", required=False)
@click.option("--category", help="分类过滤")
@click.option("--tag", help="标签过滤")
@click.option("--limit", type=int, default=20, help="返回数量")
def market_search_cmd(
    query: str | None, category: str | None, tag: str | None, limit: int
) -> None:
    """搜索公开插件"""
    from mpdt.commands.market import market_search

    try:
        market_search(
            query=query,
            category=category,
            tag=tag,
            limit=limit,
        )
    except Exception as e:
        print_error(f"搜索失败: {e}")
        raise click.Abort()


@market.command("info")
@click.argument("plugin_id")
def market_info_cmd(plugin_id: str) -> None:
    """查看公开插件详情"""
    from mpdt.commands.market import market_info

    try:
        market_info(plugin_id=plugin_id)
    except Exception as e:
        print_error(f"查询失败: {e}")
        raise click.Abort()


@market.command("package-update")
@click.argument("plugin_path", type=click.Path(), required=False, default=".")
@click.option("--owner", help="GitHub 用户或组织名")
@click.option("--repo", help="GitHub 仓库名（默认使用插件 ID）")
@click.option("--with-docs", is_flag=True, help="包含文档")
@click.option("--release-notes", help="Release 说明")
@click.option("--skip-push", is_flag=True, help="跳过 Git 推送")
def market_package_new_version_cmd(
    plugin_path: str,
    owner: str | None,
    repo: str | None,
    with_docs: bool,
    release_notes: str | None,
    skip_push: bool,
) -> None:
    """打包并发布插件的新版本
    
    前置检查：
    - 插件是否已在市场注册
    - 仓库是否存在且有权限
    - 版本是否已存在
    
    通过后：构建 -> Release -> 市场提交
    """
    from mpdt.commands.market import market_package_new_version

    try:
        market_package_new_version(
            plugin_path=plugin_path,
            owner=owner,
            repo=repo,
            with_docs=with_docs,
            release_notes=release_notes,
            skip_push=skip_push,
        )
    except Exception as e:
        print_error(f"打包失败: {e}")
        raise click.Abort()


@market.command("delete")
@click.argument("plugin_id")
def market_delete_cmd(plugin_id: str) -> None:
    """删除插件
    
    ⚠️  警告：删除插件是不可逆的操作！
    
    前置检查：
    - 检查插件是否存在
    - 检查是否有删除权限（owner/maintainer）
    
    需要用户二次确认
    """
    from mpdt.commands.market import market_delete_plugin

    try:
        market_delete_plugin(plugin_id=plugin_id)
    except Exception as e:
        print_error(f"删除失败: {e}")
        raise click.Abort()


@market.command("yank")
@click.argument("plugin_id")
@click.argument("version")
@click.option("--reason", "-r", help="废弃原因")
def market_yank_cmd(
    plugin_id: str, version: str, reason: str | None
) -> None:
    """废弃插件版本
    
    废弃后，用户将无法再安装此版本，但已安装的不受影响。
    
    前置检查：
    - 检查插件是否存在
    - 检查版本是否存在
    - 检查是否有废弃权限（owner/maintainer）
    
    需要用户二次确认
    """
    from mpdt.commands.market import market_yank_version

    try:
        market_yank_version(
            plugin_id=plugin_id, version=version, reason=reason
        )
    except Exception as e:
        print_error(f"废弃失败: {e}")
        raise click.Abort()


@cli.group()
def config() -> None:
    """配置管理"""
    pass


@config.command("init")
def config_init() -> None:
    """交互式配置向导"""
    from mpdt.utils.managers.config_manager import interactive_config

    try:
        interactive_config()
    except Exception as e:
        print_error(f"配置失败: {e}")
        raise click.Abort()


@config.command("show")
def config_show() -> None:
    """显示当前配置"""
    from rich.table import Table

    from mpdt.utils.managers.config_manager import get_or_init_mpdt_config

    try:
        config = get_or_init_mpdt_config()

        if not config.is_configured():
            print_warning("未找到配置文件")
            print_info("请运行 mpdt config init 进行配置")
            return

        table = Table(title="MPDT 配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        table.add_row("配置文件", str(config.config_path))
        table.add_row("Neo-MoFox 路径", str(config.mofox_path) if config.mofox_path else "[red]未配置[/red]")
        table.add_row("市场地址", config.market_url)
        table.add_row("GitHub Token", "已配置" if config.github_token else "[yellow]未配置[/yellow]")
        table.add_row("自动重载", "是" if config.auto_reload else "否")
        table.add_row("重载延迟", f"{config.reload_delay}秒")

        console.print(table)

    except Exception as e:
        print_error(f"读取配置失败: {e}")
        raise click.Abort()


@config.command("open")
def config_open() -> None:
    """打开配置文件"""
    import os
    import subprocess
    from pathlib import Path

    from mpdt.utils.managers.config_manager import get_or_init_mpdt_config

    try:
        config = get_or_init_mpdt_config()
        config_path = config.config_path

        if not config_path.exists():
            print_warning("配置文件不存在")
            print_info("请运行 mpdt config init 进行配置")
            return

        # 优先级：
        # 1. 配置文件中的 editor.command
        # 2. 环境变量 EDITOR
        # 3. 系统默认编辑器
        if config.editor_command:
            # 使用配置的编辑器命令
            subprocess.run([config.editor_command, str(config_path)])
        elif os.environ.get("EDITOR"):
            # 使用环境变量 EDITOR
            subprocess.run([os.environ["EDITOR"], str(config_path)])
        elif os.name == "posix":
            # Linux/macOS - 使用系统默认编辑器
            subprocess.run(["xdg-open", str(config_path)])
        elif os.name == "nt":
            # Windows - 使用系统默认编辑器
            os.startfile(config_path)
        else:
            # fallback: 只显示路径
            print_info(f"配置文件路径: {config_path}")

    except Exception as e:
        print_error(f"打开失败: {e}")
        # 显示配置文件路径作为后备方案
        try:
            print_info(f"配置文件路径: {config.config_path}")
        except:
            pass
        raise click.Abort()


@config.command("edit")
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--unset", is_flag=True, help="删除配置项")
def config_edit(key: str | None, value: str | None, unset: bool) -> None:
    """编辑配置项（类似 git config）
    
    支持的配置键：
      - mofox.path: Neo-MoFox 主程序路径
      - github.token: GitHub Personal Access Token
      - market.url: 插件市场地址
      - pypi.index_url: PyPI 镜像源地址
      - editor.command: 编辑器命令（code/pycharm/subl/vim 等）
      - dev.auto_reload: 自动重载（true/false）
      - dev.reload_delay: 重载延迟（秒）
    
    示例：
      mpdt config edit mofox.path /path/to/mofox
      mpdt config edit github.token ghp_xxxxx
      mpdt config edit editor.command code
      mpdt config edit --unset github.token
      mpdt config edit --list
    """
    from rich.table import Table

    from mpdt.utils.managers.config_manager import get_or_init_mpdt_config

    try:
        config = get_or_init_mpdt_config()

        # 检查参数
        if not key:
            print_error("请提供配置键")
            print_info("使用 mpdt config edit --list 查看所有配置")
            print_info("使用 mpdt config edit <key> <value> 设置配置")
            raise click.Abort()

        # 删除配置
        if unset:
            if config.unset_config(key):
                config.save()
                print_success(f"已删除配置: {key}")
            else:
                print_warning(f"配置项不存在: {key}")
            return

        # 设置配置
        if value is None:
            # 只提供了 key，显示当前值
            current_value = config.get_config(key)
            if current_value is None:
                print_warning(f"配置项未设置: {key}")
            else:
                # 隐藏敏感信息
                if "token" in key.lower():
                    display_value = "***" + current_value[-4:] if len(current_value) > 4 else "***"
                else:
                    display_value = current_value
                print_info(f"{key} = {display_value}")
            return

        # 设置配置值
        config.set_config(key, value)
        config.save()
        
        # 显示成功消息
        if "token" in key.lower():
            print_success(f"已设置: {key} = ***")
        else:
            print_success(f"已设置: {key} = {value}")

    except ValueError as e:
        print_error(f"配置错误: {e}")
        raise click.Abort()
    except Exception as e:
        print_error(f"编辑配置失败: {e}")
        raise click.Abort()





@cli.group()
def depend() -> None:
    """依赖管理工具"""
    pass


@depend.command("add")
@click.argument("dependency")
@click.argument("path", type=click.Path(), required=False, default=".")
@click.option("--type", "dep_type", type=click.Choice(["auto", "plugin", "python"]), default="auto", 
              help="依赖类型（auto=自动判断，plugin=插件，python=Python包）")
def depend_add_cmd(
    dependency: str,
    path: str,
    dep_type: str,
) -> None:
    """添加依赖到插件
    
    PATH 为插件根目录，默认为当前目录。
    
    示例：
      mpdt depend add 'requests>=2.28.0'
      mpdt depend add 'some-plugin>=1.0.0' . --type plugin
      mpdt depend add 'aiohttp~=3.8'
    """
    from mpdt.commands.depend import depend_add

    try:
        depend_add(
            plugin_path=path,
            dependency=dependency,
            dep_type=dep_type,
        )
    except Exception as e:
        print_error(f"添加依赖失败: {e}")
        raise click.Abort()


@depend.command("search")
@click.argument("query")
@click.option("--type", "dep_type", type=click.Choice(["all", "plugin", "python"]), default="all",
              help="搜索类型（all=全部，plugin=仅插件，python=仅Python包）")
@click.option("--limit", type=int, default=20, help="返回结果数量")
def depend_search_cmd(query: str, dep_type: str, limit: int) -> None:
    """搜索插件或 Python 包
    
    示例：
      mpdt depend search requests
      mpdt depend search utility --type plugin
    """
    from mpdt.commands.depend import depend_search

    try:
        depend_search(query=query, dep_type=dep_type, limit=limit)
    except Exception as e:
        print_error(f"搜索失败: {e}")
        raise click.Abort()


@depend.command("info")
@click.argument("dependency")
@click.option("--type", "dep_type", type=click.Choice(["auto", "plugin", "python"]), default="auto",
              help="依赖类型（auto=自动判断）")
def depend_info_cmd(dependency: str, dep_type: str) -> None:
    """查看依赖的详细信息和可用版本
    
    示例：
      mpdt depend info requests
      mpdt depend info some-plugin --type plugin
    """
    from mpdt.commands.depend import depend_info

    try:
        depend_info(dependency=dependency, dep_type=dep_type)
    except Exception as e:
        print_error(f"获取信息失败: {e}")
        raise click.Abort()


@depend.command("remove")
@click.argument("dependency")
@click.argument("path", type=click.Path(), required=False, default=".")
@click.option("--type", "dep_type", type=click.Choice(["auto", "plugin", "python"]), default="auto",
              help="依赖类型（auto=自动判断）")
def depend_remove_cmd(dependency: str, path: str, dep_type: str) -> None:
    """从插件中移除依赖
    
    PATH 为插件根目录，默认为当前目录。
    
    示例：
      mpdt depend remove requests
      mpdt depend remove some-plugin . --type plugin
    """
    from mpdt.commands.depend import depend_remove

    try:
        depend_remove(plugin_path=path, dependency=dependency, dep_type=dep_type)
    except Exception as e:
        print_error(f"移除依赖失败: {e}")
        raise click.Abort()


@depend.command("list")
@click.argument("path", type=click.Path(), required=False, default=".")
@click.option("--type", "dep_type", type=click.Choice(["all", "plugin", "python"]), default="all",
              help="依赖类型（all=全部，plugin=仅插件，python=仅Python包）")
def depend_list_cmd(path: str, dep_type: str) -> None:
    """列出插件的所有依赖
    
    PATH 为插件根目录，默认为当前目录。
    
    示例：
      mpdt depend list
      mpdt depend list . --type python
    """
    from mpdt.commands.depend import depend_list

    try:
        depend_list(plugin_path=path, dep_type=dep_type)
    except Exception as e:
        print_error(f"列出依赖失败: {e}")
        raise click.Abort()


def main() -> None:
    """主入口函数"""
    cli(obj={})


if __name__ == "__main__":
    main()

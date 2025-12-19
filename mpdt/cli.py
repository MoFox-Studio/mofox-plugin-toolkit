"""
CLI 主入口
"""

import click
from rich.console import Console

from mpdt import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="MPDT - MoFox-Bot 插件开发工具")
@click.option("--verbose", "-v", is_flag=True, help="详细输出模式")
@click.option("--no-color", is_flag=True, help="禁用彩色输出")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, no_color: bool) -> None:
    """
    MoFox Plugin Dev Toolkit - MoFox-Bot 插件开发工具

    一个类似 Vite 的开发工具，用于快速创建、开发和测试 MoFox-Bot 插件。
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
@click.option("--template", "-t", type=click.Choice(["basic", "action", "tool", "plus_command", "full", "adapter"]),
              default="basic", help="插件模板类型")
@click.option("--author", "-a", help="作者名称")
@click.option("--license", "-l", type=click.Choice(["GPL-v3.0", "MIT", "Apache-2.0", "BSD-3-Clause"]),
              default="GPL-v3.0", help="开源协议")
@click.option("--with-examples", is_flag=True, help="包含示例代码")
@click.option("--with-docs", is_flag=True, help="创建文档文件")
@click.option("--init-git/--no-init-git", default=None, help="是否初始化 Git 仓库")
@click.option("--output", "-o", type=click.Path(), help="输出目录")
@click.pass_context
def init(ctx: click.Context, plugin_name: str | None, template: str, author: str | None,
         license: str, with_examples: bool, with_docs: bool, init_git: bool | None, output: str | None) -> None:
    """初始化新插件项目"""
    from mpdt.commands.init import init_plugin

    try:
        init_plugin(
            plugin_name=plugin_name,
            template=template,
            author=author,
            license_type=license,
            with_examples=with_examples,
            with_docs=with_docs,
            init_git=init_git,
            output_dir=output,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 初始化失败: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("component_type", type=click.Choice(["action", "tool", "event", "adapter", "prompt", "plus-command","router","chatter"]), required=False)
@click.argument("component_name", required=False)
@click.option("--description", "-d", help="组件描述")
@click.option("--output", "-o", type=click.Path(), help="输出目录")
@click.option("--force", "-f", is_flag=True, help="覆盖已存在的文件")
@click.pass_context
def generate(ctx: click.Context, component_type: str | None, component_name: str | None, description: str | None,
             output: str | None, force: bool) -> None:
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
@click.option("--report", type=click.Choice(["console","markdown"]), default="console",
              help="报告格式")
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
@click.option("--output", "-o", type=click.Path(), default="dist", help="输出目录")
@click.option("--with-docs", is_flag=True, help="包含文档")
@click.option("--format", type=click.Choice(["zip", "tar.gz", "wheel"]), default="zip", help="构建格式")
@click.option("--bump", type=click.Choice(["major", "minor", "patch"]), help="自动升级版本号")
@click.pass_context
def build(ctx: click.Context, output: str, with_docs: bool, format: str, bump: str | None) -> None:
    """构建和打包插件"""
    console.print("[yellow]⚠️  构建命令尚未实现[/yellow]")


@cli.command()
@click.option("--mmc-path", type=click.Path(exists=True), help="mmc 主程序路径")
@click.option("--plugin-path", type=click.Path(exists=True), help="插件路径（默认当前目录）")
@click.pass_context
def dev(ctx: click.Context, mmc_path: str | None, plugin_path: str | None) -> None:
    """启动开发模式，支持热重载"""
    import asyncio
    from pathlib import Path

    from mpdt.commands.dev import dev_command

    try:
        asyncio.run(dev_command(
            plugin_path=Path(plugin_path) if plugin_path else None,
            mmc_path=Path(mmc_path) if mmc_path else None
        ))
    except Exception as e:
        console.print(f"[bold red]❌ 启动失败: {e}[/bold red]")
        if ctx.obj.get("verbose"):
            import traceback
            traceback.print_exc()
        raise click.Abort()


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
        table.add_row("MoFox-Bot 路径", str(config.mmc_path) if config.mmc_path else "[red]未配置[/red]")
        table.add_row("虚拟环境类型", config.venv_type)
        table.add_row("虚拟环境路径", str(config.venv_path) if config.venv_path else "[dim]无[/dim]")
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
            console.print(f"\nmmc 路径: {config.mmc_path}")
            console.print(f"Python 命令: {' '.join(config.get_python_command())}")
        else:
            console.print("[bold red]✗ 配置验证失败：[/bold red]")
            for error in errors:
                console.print(f"  - {error}")
            console.print("\n请运行 [cyan]mpdt config init[/cyan] 重新配置")

    except Exception as e:
        console.print(f"[bold red]❌ 测试失败: {e}[/bold red]")
        raise click.Abort()


@config.command("set-mmc")
@click.argument("path", type=click.Path(exists=True))
def config_set_mmc(path: str) -> None:
    """设置 mmc 主程序路径"""
    from pathlib import Path

    from mpdt.utils.config_manager import MPDTConfig

    try:
        config = MPDTConfig()
        config.mmc_path = Path(path)
        config.save()

        console.print(f"[green]✓ mmc 路径已设置: {path}[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ 设置失败: {e}[/bold red]")
        raise click.Abort()


@config.command("set-venv")
@click.argument("path", type=click.Path(exists=True), required=False)
@click.option("--type", "venv_type", type=click.Choice(["venv", "uv", "conda", "poetry", "none"]),
              default="venv", help="虚拟环境类型")
def config_set_venv(path: str | None, venv_type: str) -> None:
    """设置虚拟环境"""
    from pathlib import Path

    from mpdt.utils.config_manager import MPDTConfig

    try:
        config = MPDTConfig()
        config.venv_type = venv_type

        if venv_type == "none":
            config.venv_path = None
            console.print("[green]✓ 已设置为使用系统 Python[/green]")
        elif path:
            config.venv_path = Path(path)
            console.print(f"[green]✓ 虚拟环境已设置: {path} (类型: {venv_type})[/green]")
        else:
            console.print("[red]❌ 请提供虚拟环境路径[/red]")
            raise click.Abort()

        config.save()

    except Exception as e:
        console.print(f"[bold red]❌ 设置失败: {e}[/bold red]")
        raise click.Abort()


def main() -> None:
    """主入口函数"""
    cli(obj={})


if __name__ == "__main__":
    main()

"""
CLI 主入口
"""

import click
from rich.console import Console

from mpdt import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="MPDT")
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
@click.option("--template", "-t", type=click.Choice(["basic", "action", "tool", "command", "full", "adapter"]),
              default="basic", help="插件模板类型")
@click.option("--author", "-a", help="作者名称")
@click.option("--license", "-l", type=click.Choice(["GPL-v3.0", "MIT", "Apache-2.0", "BSD-3-Clause"]),
              default="GPL-v3.0", help="开源协议")
@click.option("--with-examples", is_flag=True, help="包含示例代码")
@click.option("--with-docs", is_flag=True, help="创建文档文件")
@click.option("--output", "-o", type=click.Path(), help="输出目录")
@click.pass_context
def init(ctx: click.Context, plugin_name: str | None, template: str, author: str | None,
         license: str, with_examples: bool, with_docs: bool, output: str | None) -> None:
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
            output_dir=output,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 初始化失败: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("component_type", type=click.Choice(["action", "tool", "event", "adapter", "prompt", "plus-command"]))
@click.argument("component_name")
@click.option("--description", "-d", help="组件描述")
@click.option("--output", "-o", type=click.Path(), help="输出目录")
@click.option("--force", "-f", is_flag=True, help="覆盖已存在的文件")
@click.pass_context
def generate(ctx: click.Context, component_type: str, component_name: str, description: str | None,
             output: str | None, force: bool) -> None:
    """生成插件组件(始终生成异步方法)"""
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
@click.option("--report", type=click.Choice(["console", "json", "html", "markdown"]), default="console",
              help="报告格式")
@click.option("--output", "-o", type=click.Path(), help="报告输出路径")
@click.option("--no-structure", is_flag=True, help="跳过结构检查")
@click.option("--no-metadata", is_flag=True, help="跳过元数据检查")
@click.option("--no-component", is_flag=True, help="跳过组件检查")
@click.option("--no-type", is_flag=True, help="跳过类型检查")
@click.option("--no-style", is_flag=True, help="跳过代码风格检查")
@click.option("--no-security", is_flag=True, help="跳过安全检查")
@click.pass_context
def check(ctx: click.Context, path: str, level: str, fix: bool, report: str, output: str | None,
          no_structure: bool, no_metadata: bool, no_component: bool, no_type: bool,
          no_style: bool, no_security: bool) -> None:
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
            skip_security=no_security,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 检查失败: {e}[/bold red]")
        raise click.Abort()


@cli.command()
@click.argument("test_path", type=click.Path(exists=True), required=False)
@click.option("--coverage", "-c", is_flag=True, help="生成覆盖率报告")
@click.option("--min-coverage", type=int, default=80, help="最低覆盖率要求")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.option("--markers", "-m", help="只运行特定标记的测试")
@click.option("--keyword", "-k", help="只运行匹配关键词的测试")
@click.option("--parallel", "-n", type=int, default=1, help="并行运行测试的进程数")
@click.pass_context
def test(ctx: click.Context, test_path: str | None, coverage: bool, min_coverage: int,
         verbose: bool, markers: str | None, keyword: str | None, parallel: int) -> None:
    """运行插件测试"""
    console.print("[yellow]⚠️  测试命令尚未实现[/yellow]")


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
@click.option("--port", "-p", type=int, default=8080, help="开发服务器端口")
@click.option("--host", default="127.0.0.1", help="绑定的主机地址")
@click.option("--no-reload", is_flag=True, help="禁用自动重载")
@click.option("--debug", is_flag=True, help="启用调试模式")
@click.pass_context
def dev(ctx: click.Context, port: int, host: str, no_reload: bool, debug: bool) -> None:
    """启动开发模式"""
    console.print("[yellow]⚠️  开发模式命令尚未实现[/yellow]")


def main() -> None:
    """主入口函数"""
    cli(obj={})


if __name__ == "__main__":
    main()

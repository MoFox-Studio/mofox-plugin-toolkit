"""
彩色输出工具
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

console = Console()


def print_success(message: str) -> None:
    """打印成功消息"""
    console.print(f"[bold green]✅ {message}[/bold green]")


def print_error(message: str) -> None:
    """打印错误消息"""
    console.print(f"[bold red]❌ {message}[/bold red]")


def print_warning(message: str) -> None:
    """打印警告消息"""
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")


def print_info(message: str) -> None:
    """打印信息消息"""
    console.print(f"[bold blue]ℹ️  {message}[/bold blue]")


def print_step(message: str) -> None:
    """打印步骤消息"""
    console.print(f"[bold cyan]🔸 {message}[/bold cyan]")


def print_panel(title: str, content: str, style: str = "green") -> None:
    """打印面板"""
    console.print(Panel(content, title=title, style=style))


def print_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    """打印表格"""
    table = Table(title=title)

    for col in columns:
        table.add_column(col, style="cyan")

    for row in rows:
        table.add_row(*row)

    console.print(table)


def print_tree(root_label: str, tree_data: dict[str, Any]) -> None:
    """
    打印树形结构
    
    Args:
        root_label: 根节点标签
        tree_data: 树形数据（字典或列表）
    """
    tree = Tree(f"[bold blue]{root_label}[/bold blue]")

    def add_branch(parent: Tree, data: Any) -> None:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    branch = parent.add(f"[cyan]{key}/[/cyan]")
                    add_branch(branch, value)
                else:
                    parent.add(f"[green]{key}[/green]")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    parent.add(f"[green]{item}[/green]")
                else:
                    add_branch(parent, item)

    add_branch(tree, tree_data)
    console.print(tree)


def create_progress() -> Progress:
    """创建进度条"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    )


def print_divider(char: str = "━", length: int = 80) -> None:
    """打印分割线"""
    console.print(char * length, style="dim")

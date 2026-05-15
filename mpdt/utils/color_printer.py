"""
彩色输出工具
"""

import time
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.table import Table
from rich.tree import Tree

console = Console()


class FitPanel:
    """动态自适应面板
    
    支持动态更新内容的面板，可以用于实时显示进度信息。
    """
    
    def __init__(
        self, 
        title: str, 
        style: str = "green", 
        rgb: tuple[int, int, int] | None = None, 
        border_style: str | None = None,
        delay: float = 0.3
    ):
        """初始化动态面板
        
        Args:
            title: 面板标题
            style: 面板样式（颜色名称）
            rgb: RGB 颜色元组，优先级高于 style
            border_style: 边框样式
            delay: 每次更新后的延迟时间（秒），默认 0.3 秒，让用户能看清每一步进度
        """
        self.title = title
        self.style = style
        self.rgb = rgb
        self.border_style = border_style
        self.content = ""
        self._live = None
        self.delay = delay
    
    def start(self) -> None:
        """启动实时更新"""
        self._live = Live(self._create_panel(), console=console, refresh_per_second=4)
        self._live.start()
    
    def update(self, content: str) -> None:
        """更新面板内容
        
        Args:
            content: 新的内容
        """
        self.content = content
        if self._live:
            self._live.update(self._create_panel())
            if self.delay > 0:
                time.sleep(self.delay)
    
    def append(self, content: str) -> None:
        """追加内容
        
        Args:
            content: 要追加的内容
        """
        if self.content:
            self.content += "\n" + content
        else:
            self.content = content
        if self._live:
            self._live.update(self._create_panel())
            if self.delay > 0:
                time.sleep(self.delay)
    
    def stop(self) -> None:
        """停止实时更新"""
        if self._live:
            self._live.stop()
            self._live = None
    
    def _create_panel(self):
        """创建面板对象
        
        Returns:
            Panel 对象
        """
        if self.rgb:
            hex_color = _rgb_to_hex(*self.rgb)
            return Panel.fit(
                self.content, 
                title=self.title, 
                style=hex_color, 
                border_style=self.border_style or hex_color, 
                highlight=False
            )
        else:
            return Panel.fit(
                self.content, 
                title=self.title, 
                style=self.style, 
                border_style=self.border_style or self.style, 
                highlight=False
            )
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """将 RGB 值转换为十六进制颜色代码
    
    Args:
        r: 红色值 (0-255)
        g: 绿色值 (0-255)
        b: 蓝色值 (0-255)
        
    Returns:
        十六进制颜色代码
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def print_colored(
    message: str,
    rgb: tuple[int, int, int] | None = None,
    color: str | None = None,
    bold: bool = False,
    dim: bool = False,
    italic: bool = False,
    underline: bool = False,
    icon: str | None = None,
) -> None:
    """打印彩色消息（通用函数）
    
    Args:
        message: 消息内容
        rgb: RGB 颜色元组 (r, g, b)，优先级高于 color
        color: 颜色名称（如 "red", "green"）
        bold: 是否加粗
        dim: 是否暗淡
        italic: 是否斜体
        underline: 是否下划线
        icon: 可选的图标前缀
    """
    # 移除消息中的所有富文本标记
    import re
    cleaned_message = re.sub(r'\[/?[^\]]+\]', '', message)
    
    if icon:
        formatted_message = f"{icon} {cleaned_message}"
    else:
        formatted_message = cleaned_message
    
    # 使用 Style 对象来组合样式
    style_kwargs = {}
    
    if rgb:
        hex_color = _rgb_to_hex(*rgb)
        style_kwargs['color'] = hex_color
    elif color:
        style_kwargs['color'] = color
    
    if bold:
        style_kwargs['bold'] = True
    if dim:
        style_kwargs['dim'] = True
    if italic:
        style_kwargs['italic'] = True
    if underline:
        style_kwargs['underline'] = True
    
    if style_kwargs:
        from rich.style import Style
        style = Style(**style_kwargs)
        console.print(formatted_message, style=style)
    else:
        console.print(formatted_message)


def print_success(
    message: str,
    rgb: tuple[int, int, int] | None = None,
    icon: str = "✅"
) -> None:
    """打印成功消息
    
    Args:
        message: 消息内容
        rgb: 自定义 RGB 颜色，默认使用绿色
        icon: 图标，默认为 ✅
    """
    if rgb:
        print_colored(message, rgb=rgb, bold=True, icon=icon)
    else:
        console.print(f"[bold green]{icon} {message}[/bold green]")


def print_error(
    message: str,
    rgb: tuple[int, int, int] | None = None,
    icon: str = "❌"
) -> None:
    """打印错误消息
    
    Args:
        message: 消息内容
        rgb: 自定义 RGB 颜色，默认使用红色
        icon: 图标，默认为 ❌
    """
    if rgb:
        print_colored(message, rgb=rgb, bold=True, icon=icon)
    else:
        console.print(f"[bold red]{icon} {message}[/bold red]")


def print_warning(
    message: str,
    rgb: tuple[int, int, int] | None = None,
    icon: str = "⚠️ "
) -> None:
    """打印警告消息
    
    Args:
        message: 消息内容
        rgb: 自定义 RGB 颜色，默认使用黄色
        icon: 图标，默认为 ⚠️
    """
    if rgb:
        print_colored(message, rgb=rgb, bold=True, icon=icon)
    else:
        console.print(f"[bold yellow]{icon} {message}[/bold yellow]")


def print_info(
    message: str,
    rgb: tuple[int, int, int] | None = None,
    icon: str = "ℹ️ "
) -> None:
    """打印信息消息
    
    Args:
        message: 消息内容
        rgb: 自定义 RGB 颜色，默认使用蓝色
        icon: 图标，默认为 ℹ️
    """
    if rgb:
        print_colored(message, rgb=rgb, bold=True, icon=icon)
    else:
        console.print(f"[bold blue]{icon} {message}[/bold blue]")


def print_step(
    message: str,
    rgb: tuple[int, int, int] | None = None,
    icon: str = "🔸"
) -> None:
    """打印步骤消息
    
    Args:
        message: 消息内容
        rgb: 自定义 RGB 颜色，默认使用青色
        icon: 图标，默认为 🔸
    """
    if rgb:
        print_colored(message, rgb=rgb, bold=True, icon=icon)
    else:
        console.print(f"[bold cyan]{icon} {message}[/bold cyan]")


def print_panel(
    title: str,
    content: str,
    style: str = "green",
    rgb: tuple[int, int, int] | None = None,
    border_style: str | None = None,
) -> None:
    """打印面板
    
    Args:
        title: 面板标题
        content: 面板内容
        style: 面板样式（颜色名称）
        rgb: RGB 颜色元组，优先级高于 style
        border_style: 边框样式
    """
    if rgb:
        hex_color = _rgb_to_hex(*rgb)
        console.print(Panel(content, title=title, style=hex_color, border_style=border_style or hex_color, highlight=False), markup=False, highlight=False)
    else:
        console.print(Panel(content, title=title, style=style, border_style=border_style or style, highlight=False), markup=False, highlight=False)


def print_fit_panel(
    title: str,
    content: str,
    style: str = "green",
    rgb: tuple[int, int, int] | None = None,
    border_style: str | None = None,
) -> None:
    """打印自适应大小的面板
    
    Args:
        title: 面板标题
        content: 面板内容
        style: 面板样式（颜色名称）
        rgb: RGB 颜色元组，优先级高于 style
        border_style: 边框样式
    """
    if rgb:
        hex_color = _rgb_to_hex(*rgb)
        console.print(Panel.fit(content, title=title, style=hex_color, border_style=border_style or hex_color, highlight=False), markup=False, highlight=False)
    else:
        console.print(Panel.fit(content, title=title, style=style, border_style=border_style or style, highlight=False), markup=False, highlight=False)


def get_fit_panel(
    title: str,
    style: str = "green",
    rgb: tuple[int, int, int] | None = None,
    border_style: str | None = None,
    delay: float = 0.3
) -> FitPanel:
    """获取动态自适应面板实例
    
    Args:
        title: 面板标题
        style: 面板样式（颜色名称）
        rgb: RGB 颜色元组，优先级高于 style
        border_style: 边框样式
        delay: 每次更新后的延迟时间（秒），默认 0.3 秒，设置为 0 禁用延迟
        
    Returns:
        FitPanel 实例
        
    Example:
        >>> panel = get_fit_panel("进度", border_style="blue")
        >>> with panel:
        ...     panel.update("正在处理...")
        ...     # 做一些工作
        ...     panel.update("处理完成")
        >>> 
        >>> # 禁用延迟以获得最快速度
        >>> panel = get_fit_panel("快速进度", delay=0)
    """
    return FitPanel(title, style, rgb, border_style, delay)


def print_table(
    title: str,
    columns: list[str],
    rows: list[list[str]],
    title_rgb: tuple[int, int, int] | None = None,
    column_rgb: tuple[int, int, int] | None = None,
) -> None:
    """打印表格
    
    Args:
        title: 表格标题
        columns: 列名列表
        rows: 行数据列表
        title_rgb: 标题的 RGB 颜色
        column_rgb: 列的 RGB 颜色
    """
    table = Table(title=title)

    column_style = "cyan"
    if column_rgb:
        column_style = _rgb_to_hex(*column_rgb)

    for col in columns:
        table.add_column(col, style=column_style)

    for row in rows:
        table.add_row(*row)

    console.print(table)


def print_tree(
    root_label: str,
    tree_data: dict[str, Any],
    label_rgb: tuple[int, int, int] | None = None,
) -> None:
    """
    打印树形结构
    
    Args:
        root_label: 根节点标签
        tree_data: 树形数据（字典或列表）
        label_rgb: 根节点标签的 RGB 颜色
    """
    if label_rgb:
        hex_color = _rgb_to_hex(*label_rgb)
        tree = Tree(f"[bold {hex_color}]{root_label}[/bold {hex_color}]")
    else:
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


def print_divider(
    char: str = "━",
    length: int = 80,
    rgb: tuple[int, int, int] | None = None,
    style: str = "dim",
) -> None:
    """打印分割线
    
    Args:
        char: 分割线字符
        length: 分割线长度
        rgb: RGB 颜色元组
        style: 样式名称
    """
    if rgb:
        hex_color = _rgb_to_hex(*rgb)
        console.print(char * length, style=hex_color)
    else:
        console.print(char * length, style=style)


def print_empty_line(count: int = 1) -> None:
    """打印空行
    
    Args:
        count: 空行数量
    """
    for _ in range(count):
        console.print()

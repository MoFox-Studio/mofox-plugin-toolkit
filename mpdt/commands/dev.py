"""
mpdt dev 命令实现
启动开发模式：注入开发插件到主程序，由开发插件负责文件监控和热重载
"""

import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from mpdt.utils.managers.config_manager import MPDTConfig, get_or_init_mpdt_config, interactive_config
from mpdt.utils.plugin_parser import extract_plugin_name

console = Console()


class DevServer:
    """开发服务器 - 注入开发插件并启动主程序"""

    def __init__(self, plugin_path: Path, config: MPDTConfig, mofox_path: Path | None = None):
        self.plugin_path = plugin_path.absolute()
        self.config = config

        resolved_path = mofox_path or config.mofox_path
        if not resolved_path:
            raise ValueError("未配置 Neo-MoFox 主程序路径")
        self.mofox_path: Path = resolved_path

        self.plugin_name: str | None = None
        self.process: subprocess.Popen[str] | None = None

    def start(self):
        """启动开发模式（同步方法）"""
        try:
            # 1. 解析插件名称
            self._parse_plugin_info()

            # 2. 注入目标开发插件
            self._inject_target_plugin()

            # 4. 注入 DevBridge 插件（包含配置）
            self._inject_bridge_plugin()

            # 5. 启动主程序
            self._start_main_process()

            console.print("\n[bold green]✨ 开发模式已启动！[/bold green]")
            console.print("[dim]主程序窗口中会显示文件监控和重载信息[/dim]")
            console.print("[dim]DevBridge 插件会在主程序退出时自动清理[/dim]\n")

            # 启动完成，直接退出，让插件自己管理生命周期
            console.print("[green]✓ 开发服务器启动完成，此窗口将关闭[/green]")

        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            import traceback
            traceback.print_exc()



    def _parse_plugin_info(self):
        """解析插件信息"""
        console.print(
            Panel.fit(
                f"[bold cyan]🚀 Neo-MoFox Plugin Dev Server[/bold cyan]\n\n"
                f"📂 目录: {self.plugin_path.name}\n"
                f"📍 路径: {self.plugin_path}"
            )
        )

        # 提取插件名称
        self.plugin_name = extract_plugin_name(self.plugin_path)

        if not self.plugin_name:
            console.print("[red]❌ 无法读取插件名称[/red]")
            console.print("\n请确保 plugin.py 中有：")
            console.print("```python")
            console.print("class YourPlugin(BasePlugin):")
            console.print('    plugin_name = "your_plugin"')
            console.print("```")
            raise ValueError("无法解析插件名称")

        console.print(f"[green]✓ 插件名: {self.plugin_name}[/green]")

    def _inject_target_plugin(self):
        """将目标插件复制到 mofox 的 plugins 目录"""
        assert self.plugin_name is not None, "plugin_name 未初始化"
        plugins_dir = self.mofox_path / "plugins"
        target_dir = plugins_dir / self.plugin_name

        # 检查插件是否已经在 plugins 目录下
        if self.plugin_path.parent.resolve() == plugins_dir.resolve():
            console.print("[dim]📦 插件已在 plugins 目录下，跳过复制[/dim]")
            return

        console.print("[cyan]📦 注入目标插件...[/cyan]")

        # 如果已存在，先删除
        if target_dir.exists():
            shutil.rmtree(target_dir)

        # 复制插件
        shutil.copytree(self.plugin_path, target_dir)

        console.print(f"[green]✓ 目标插件已注入: {target_dir}[/green]")

    def _inject_bridge_plugin(self):
        """注入 DevBridge 插件到主程序，并修改配置常量"""
        console.print("[cyan]🔗 注入开发模式插件...[/cyan]")

        # DevBridge 插件源路径
        bridge_source = Path(__file__).parent.parent / "dev" / "bridge_plugin"

        if not bridge_source.exists():
            raise FileNotFoundError(f"DevBridge 插件源不存在: {bridge_source}")

        # 目标路径
        bridge_target = self.mofox_path / "plugins" / "dev_bridge"

        # 如果已存在，先删除
        if bridge_target.exists():
            shutil.rmtree(bridge_target)

        # 复制插件
        shutil.copytree(bridge_source, bridge_target)

        # 动态修改 dev_config.py 中的常量
        self._update_dev_config(bridge_target)

        console.print(f"[green]✓ DevBridge 插件已注入: {bridge_target}[/green]")
        console.print(f"[dim]  目标插件: {self.plugin_name}[/dim]")
        console.print(f"[dim]  监控路径: {self.plugin_path}[/dim]")

    def _update_dev_config(self, bridge_target: Path):
        """更新开发插件的配置文件"""
        config_file = bridge_target / "dev_config.py"

        # 生成新的配置内容
        config_content = f'''"""
开发模式配置文件
此文件由 mpdt dev 自动生成，请勿手动修改
"""

# ==================== 开发目标插件配置 ====================

# 目标插件的绝对路径
TARGET_PLUGIN_PATH: str = r"{self.plugin_path}"

# 目标插件名称
TARGET_PLUGIN_NAME: str = "{self.plugin_name}"

# 是否启用文件监控
ENABLE_FILE_WATCHER: bool = True

# 文件监控防抖延迟（秒）
DEBOUNCE_DELAY: float = 0.3

# ==================== 其他配置 ====================

# 发现服务器端口（保留，暂未使用）
DISCOVERY_PORT: int = 12318
'''

        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        console.print("[dim]  配置已写入 dev_config.py[/dim]")



    def _start_main_process(self):
        """启动主程序"""
        console.print(f"[cyan]🚀 启动主程序: {self.mofox_path / 'bot.py'}[/cyan]")

        try:
            import os
            import sys

            # Windows 下打开新窗口
            if os.name == "nt":
                cmd = ["cmd", "/c", f"chcp 65001 && cd /d {self.mofox_path} && uv run main.py"]
                console.print("[dim]命令: 使用 Python 启动[/dim]")

                self.process = subprocess.Popen(
                    cmd, creationflags=subprocess.CREATE_NEW_CONSOLE, encoding="utf-8", errors="ignore"
                )
            else:
                # Linux/Mac
                shell_cmd = f"cd {self.mofox_path} && uv run bot.py"
                console.print("[dim]命令: 使用 Python 启动[/dim]")

                if sys.platform == "darwin":
                    cmd = ["osascript", "-e", f'tell application "Terminal" to do script "{shell_cmd}"']
                else:
                    terminals = [
                        ("gnome-terminal", ["gnome-terminal", "--", "bash", "-c", shell_cmd]),
                        ("konsole", ["konsole", "-e", "bash", "-c", shell_cmd]),
                        ("xfce4-terminal", ["xfce4-terminal", "-e", f"bash -c '{shell_cmd}'"]),
                        ("xterm", ["xterm", "-e", f"bash -c '{shell_cmd}'"]),
                    ]

                    cmd = None
                    for term_name, term_cmd in terminals:
                        if (
                            subprocess.run(
                                ["which", term_name], capture_output=True, encoding="utf-8", errors="ignore"
                            ).returncode
                            == 0
                        ):
                            cmd = term_cmd
                            break

                    if cmd is None:
                        console.print("[yellow]警告: 未找到支持的终端模拟器，使用后台启动[/yellow]")
                        cmd = ["bash", "-c", shell_cmd]
                        self.process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            encoding="utf-8",
                            errors="ignore",
                        )
                        console.print("[green]✓ 主程序已启动（后台）[/green]")
                        return

                self.process = subprocess.Popen(cmd, encoding="utf-8", errors="ignore")
            console.print("[green]✓ 主程序已启动（新窗口）[/green]")
        except Exception as e:
            raise RuntimeError(f"启动主程序失败: {e}")




def dev_command(
    plugin_path: Path | None = None,
    mofox_path: Path | None = None,
):
    """启动开发模式

    Args:
        plugin_path: 插件路径，默认为当前目录
        mofox_path: Neo-MoFox 主程序路径，默认从配置读取
    """
    # 确定插件路径
    if plugin_path is None:
        plugin_path = Path.cwd()

    # 加载配置
    config = get_or_init_mpdt_config()

    # 如果未配置，运行配置向导
    if not config.is_configured() and mofox_path is None:
        console.print("[yellow]未找到配置，启动配置向导...[/yellow]\n")
        config = interactive_config()

    # 如果提供了 mofox_path，使用它
    if mofox_path:
        config.mofox_path = mofox_path

    # 验证配置
    valid, errors = config.validate()
    if not valid:
        console.print("[red]配置验证失败：[/red]")
        for error in errors:
            console.print(f"  - {error}")
        console.print("\n请运行 [cyan]mpdt config init[/cyan] 重新配置")
        return

    # 创建并启动开发服务器（同步方法）
    server = DevServer(plugin_path, config, mofox_path)
    server.start()

"""
mpdt dev 命令实现
启动开发模式：注入开发插件到主程序，由开发插件负责文件监控和热重载
"""

import atexit
import os
import signal
import subprocess
import shutil
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from mpdt.utils.config_manager import MPDTConfig, interactive_config
from mpdt.utils.plugin_parser import extract_plugin_name

console = Console()

# 全局引用，用于信号处理器访问
_current_server: "DevServer | None" = None


def _cleanup_on_exit():
    """退出时的清理函数"""
    global _current_server
    if _current_server:
        _current_server._user_exit = True  # 标记为用户主动退出
        _current_server.stop()
        _current_server = None


def _signal_handler(signum, frame):
    """信号处理器"""
    console.print("\n[yellow]收到退出信号，正在清理...[/yellow]")
    _cleanup_on_exit()
    exit(0)


def _setup_signal_handlers():
    """设置信号处理器"""
    # 注册 SIGINT (Ctrl+C) 和 SIGTERM
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Windows 特殊处理：捕获控制台关闭事件
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32

            # 定义回调函数类型
            HANDLER_ROUTINE = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_ulong)

            def console_handler(ctrl_type):
                """Windows 控制台事件处理器"""
                # CTRL_C_EVENT = 0, CTRL_BREAK_EVENT = 1, CTRL_CLOSE_EVENT = 2
                # CTRL_LOGOFF_EVENT = 5, CTRL_SHUTDOWN_EVENT = 6
                if ctrl_type in (0, 1, 2, 5, 6):
                    _cleanup_on_exit()
                    return True
                return False

            # 保存引用防止被垃圾回收
            global _win_handler
            _win_handler = HANDLER_ROUTINE(console_handler)
            kernel32.SetConsoleCtrlHandler(_win_handler, True)
        except Exception:
            pass  # 如果失败，仍然有 atexit 作为备份


class DevServer:
    """开发服务器 - 注入开发插件并启动主程序"""

    def __init__(self, plugin_path: Path, config: MPDTConfig, mofox_path: Path | None = None):
        self.plugin_path = plugin_path.absolute()
        self.config = config
        self.mofox_path = mofox_path or config.mofox_path
        assert self.mofox_path is not None

        if not self.mofox_path:
            raise ValueError("未配置 mmc 主程序路径")

        self.plugin_name: str | None = None
        self.process: subprocess.Popen | None = None
        self._stopped = False  # 防止重复清理
        self._user_exit = False  # 用户主动退出标志

    def start(self):
        """启动开发服务器（同步方法）"""
        global _current_server
        _current_server = self

        # 注册退出清理
        atexit.register(_cleanup_on_exit)

        # 设置信号处理器（包括 Windows 控制台事件）
        _setup_signal_handlers()

        try:
            # 1. 解析插件名称
            self._parse_plugin_info()

            # 2. 注入 DevBridge 插件（包含配置）
            self._inject_bridge_plugin()

            # 3. 启动主程序
            self._start_main_process()

            console.print("\n[bold green]✨ 开发模式已启动！[/bold green]")
            console.print("[dim]主程序窗口中会显示文件监控和重载信息[/dim]")
            console.print("[dim]关闭主程序窗口或按 Ctrl+C 退出[/dim]\n")

            # 4. 等待主程序退出
            self._wait_for_exit()

        except KeyboardInterrupt:
            self._user_exit = True
            console.print("\n[yellow]正在退出...[/yellow]")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            import traceback
            traceback.print_exc()
        finally:
            self.stop()

    def stop(self):
        """停止开发服务器"""
        # 防止重复清理
        if self._stopped:
            return
        self._stopped = True

        # 停止主程序 - 仅当进程还在运行时才尝试关闭
        if self.process and self.process.poll() is None:
            # poll() 返回 None 表示进程还在运行
            console.print("[cyan]🛑 正在关闭主程序...[/cyan]")
            try:
                import os

                # Windows: 使用 taskkill 杀死整个进程树
                if os.name == "nt":
                    try:
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                            capture_output=True,
                            timeout=5,
                            encoding="utf-8",
                            errors="ignore",
                        )
                        console.print("[green]✓ 主程序及所有子进程已关闭[/green]")
                    except Exception as e:
                        console.print(f"[yellow]taskkill 失败: {e}，尝试其他方法...[/yellow]")
                        self.process.terminate()
                        try:
                            self.process.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            self.process.kill()
                            self.process.wait()
                else:
                    # Linux/Mac: 尝试优雅终止
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=3)
                        console.print("[green]✓ 主程序已优雅关闭[/green]")
                    except subprocess.TimeoutExpired:
                        console.print("[yellow]主程序未响应，强制关闭...[/yellow]")
                        try:
                            os.killpg(os.getpgid(self.process.pid), 9)
                        except Exception:
                            self.process.kill()
                        self.process.wait()
                        console.print("[green]✓ 主程序已强制关闭[/green]")
            except Exception as e:
                console.print(f"[yellow]警告: 关闭主程序时出错: {e}[/yellow]")
                try:
                    self.process.kill()
                    self.process.wait()
                except Exception:
                    pass

        # 清理 DevBridge 插件
        self._cleanup_bridge_plugin()

        console.print("[green]已停止[/green]")

    def _parse_plugin_info(self):
        """解析插件信息"""
        console.print(
            Panel.fit(
                f"[bold cyan]🚀 MoFox Plugin Dev Server[/bold cyan]\n\n"
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

    def _cleanup_bridge_plugin(self):
        """清理 DevBridge 插件"""
        bridge_target = self.mofox_path / "plugins" / "dev_bridge"

        if bridge_target.exists():
            try:
                shutil.rmtree(bridge_target)
                console.print("[cyan]🧹 DevBridge 插件已清理[/cyan]")
            except Exception as e:
                console.print(f"[yellow]警告: 清理 DevBridge 插件失败: {e}[/yellow]")

    def _start_main_process(self):
        """启动主程序"""
        console.print(f"[cyan]🚀 启动主程序: {self.mofox_path / 'bot.py'}[/cyan]")

        # 获取 Python 命令
        venv_type = self.config.venv_type
        venv_path = self.config.venv_path

        try:
            import os
            import sys

            # Windows 下打开新窗口
            if os.name == "nt":
                if venv_type in ["venv", "uv"] and venv_path:
                    activate_script = venv_path / "Scripts" / "activate.bat"
                    if activate_script.exists():
                        cmd = [
                            "cmd",
                            "/c",
                            f"chcp 65001 && cd /d {self.mofox_path} && {activate_script} && python bot.py",
                        ]
                        console.print(f"[dim]命令: 激活 {venv_type} 环境并启动[/dim]")
                    else:
                        python_cmd = self.config.get_python_command()
                        cmd = ["cmd", "/c", f"chcp 65001 && cd /d {self.mofox_path} && {python_cmd[0]} bot.py"]
                        console.print("[yellow]警告: 未找到激活脚本，使用直接启动[/yellow]")
                elif venv_type == "conda" and venv_path:
                    cmd = [
                        "cmd",
                        "/c",
                        f"chcp 65001 && cd /d {self.mofox_path} && conda activate {venv_path} && python bot.py",
                    ]
                    console.print("[dim]命令: 激活 conda 环境并启动[/dim]")
                elif venv_type == "poetry":
                    cmd = ["cmd", "/c", f"chcp 65001 && cd /d {self.mofox_path} && poetry run python bot.py"]
                    console.print("[dim]命令: 使用 poetry run 启动[/dim]")
                else:
                    cmd = ["cmd", "/c", f"chcp 65001 && cd /d {self.mofox_path} && python bot.py"]
                    console.print("[dim]命令: 使用系统 Python 启动[/dim]")

                self.process = subprocess.Popen(
                    cmd, creationflags=subprocess.CREATE_NEW_CONSOLE, encoding="utf-8", errors="ignore"
                )
            else:
                # Linux/Mac
                if venv_type in ["venv", "uv"] and venv_path:
                    activate_script = venv_path / "bin" / "activate"
                    if activate_script.exists():
                        shell_cmd = f"cd {self.mofox_path} && source {activate_script} && python bot.py"
                    else:
                        python_cmd = self.config.get_python_command()
                        shell_cmd = f"cd {self.mofox_path} && {python_cmd[0]} bot.py"
                        console.print("[yellow]警告: 未找到激活脚本，使用直接启动[/yellow]")
                    console.print(f"[dim]命令: 激活 {venv_type} 环境并启动[/dim]")
                elif venv_type == "conda" and venv_path:
                    shell_cmd = f"cd {self.mofox_path} && conda activate {venv_path} && python bot.py"
                    console.print("[dim]命令: 激活 conda 环境并启动[/dim]")
                elif venv_type == "poetry":
                    shell_cmd = f"cd {self.mofox_path} && poetry run python bot.py"
                    console.print("[dim]命令: 使用 poetry run 启动[/dim]")
                else:
                    shell_cmd = f"cd {self.mofox_path} && python bot.py"
                    console.print("[dim]命令: 使用系统 Python 启动[/dim]")

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

    def _wait_for_exit(self):
        """等待主程序退出或用户中断"""
        import time

        if not self.process:
            return

        try:
            # 使用轮询而不是阻塞等待，这样可以响应 Ctrl+C
            while True:
                exit_code = self.process.poll()
                if exit_code is not None:
                    # 进程已退出，仅在非用户主动退出时显示异常
                    if exit_code != 0 and not self._user_exit:
                        console.print(f"[yellow]⚠️  主程序异常退出 (退出码: {exit_code})[/yellow]")
                    break
                # 短暂睡眠，减少 CPU 占用
                time.sleep(0.5)
        except KeyboardInterrupt:
            self._user_exit = True
            console.print("\n[yellow]检测到 Ctrl+C，正在退出...[/yellow]")


def dev_command(
    plugin_path: Path | None = None,
    mofox_path: Path | None = None,
):
    """启动开发模式

    Args:
        plugin_path: 插件路径，默认为当前目录
        mofox_path: mmc 主程序路径，默认从配置读取
    """
    # 确定插件路径
    if plugin_path is None:
        plugin_path = Path.cwd()

    # 加载配置
    config = MPDTConfig()

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

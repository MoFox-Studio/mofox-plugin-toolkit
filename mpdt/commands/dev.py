"""
mpdt dev 命令实现
提供热重载开发模式
"""

import asyncio
import json
import shutil
import subprocess
import time
from pathlib import Path

import aiohttp
import websockets
from rich.console import Console
from rich.panel import Panel
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from mpdt.utils.config_manager import MPDTConfig, interactive_config
from mpdt.utils.plugin_parser import extract_plugin_name

console = Console()

# 发现服务器固定端口
DISCOVERY_PORT = 12318


class PluginFileWatcher(FileSystemEventHandler):
    """插件文件监控"""

    def __init__(self, plugin_path: Path, callback, loop):
        self.plugin_path = plugin_path
        self.callback = callback
        self.loop = loop  # 主事件循环
        self.last_modified = {}
        self.debounce_delay = 0.3  # 防抖延迟（秒）

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return

        # 只监控 Python 文件
        if not event.src_path.endswith(".py"):
            return

        # 防抖处理
        now = time.time()
        if event.src_path in self.last_modified:
            if now - self.last_modified[event.src_path] < self.debounce_delay:
                return

        self.last_modified[event.src_path] = now

        # 获取相对路径
        rel_path = Path(event.src_path).relative_to(self.plugin_path)

        # 在主事件循环中调度协程
        asyncio.run_coroutine_threadsafe(self.callback(str(rel_path)), self.loop)

    def on_created(self, event: FileSystemEvent):
        self.on_modified(event)


class DevServer:
    """开发服务器 - 监控文件并通过 WebSocket 控制主程序"""

    def __init__(self, plugin_path: Path, config: MPDTConfig, mmc_path: Path | None = None):
        self.plugin_path = plugin_path.absolute()
        self.config = config
        self.mmc_path = mmc_path or config.mmc_path

        if not self.mmc_path:
            raise ValueError("未配置 mmc 主程序路径")

        self.plugin_name: str | None = None
        self.process: subprocess.Popen | None = None
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self.observer: Observer | None = None
        self.main_host = "127.0.0.1"
        self.main_port = 8000
        self.running = False

    async def start(self):
        """启动开发服务器"""
        try:
            # 1. 解析插件名称
            await self._parse_plugin_info()

            # 2. 注入 DevBridge 插件
            await self._inject_bridge_plugin()

            # 3. 启动主程序
            await self._start_main_process()

            # 4. 等待主程序启动
            await asyncio.sleep(3)

            # 5. 发现主程序端口
            await self._discover_main_server()

            # 6. 连接 WebSocket
            await self._connect_websocket()

            # 7. 等待插件加载通知
            await self._wait_for_plugin_loaded()

            # 8. 启动文件监控
            await self._start_file_watcher()

            console.print("\n[bold green]✨ 开发服务器就绪！[/bold green]")
            console.print("监控文件变化中... (Ctrl+C 退出)\n")

            self.running = True

            # 保持运行
            await self._keep_alive()

        except KeyboardInterrupt:
            console.print("\n[yellow]正在退出...[/yellow]")
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            import traceback

            traceback.print_exc()
        finally:
            await self.stop()

    async def stop(self):
        """停止开发服务器"""
        self.running = False

        # 停止文件监控
        if self.observer:
            self.observer.stop()
            self.observer.join()

        # 关闭 WebSocket
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass

        # 停止主程序 - 确保一定被关闭（包括所有子进程）
        if self.process:
            console.print("[cyan]🛑 正在关闭主程序...[/cyan]")
            try:
                import os

                # Windows: 使用 taskkill 杀死整个进程树
                if os.name == "nt":
                    try:
                        # /F 强制终止 /T 终止子进程树 /PID 指定进程ID
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(self.process.pid)],
                            capture_output=True,
                            timeout=5
                        )
                        console.print("[green]✓ 主程序及所有子进程已关闭[/green]")
                    except Exception as e:
                        console.print(f"[yellow]taskkill 失败: {e}，尝试其他方法...[/yellow]")
                        # 降级到常规方法
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
                        # 超时则强制杀死进程组
                        console.print("[yellow]主程序未响应，强制关闭...[/yellow]")
                        try:
                            # 杀死整个进程组
                            os.killpg(os.getpgid(self.process.pid), 9)
                        except Exception:
                            self.process.kill()
                        self.process.wait()
                        console.print("[green]✓ 主程序已强制关闭[/green]")
            except Exception as e:
                console.print(f"[yellow]警告: 关闭主程序时出错: {e}[/yellow]")
                # 最后的尝试：直接 kill
                try:
                    self.process.kill()
                    self.process.wait()
                except Exception:
                    pass

        # 清理 DevBridge 插件
        await self._cleanup_bridge_plugin()

        console.print("[green]开发服务器已停止[/green]")

    async def _parse_plugin_info(self):
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

    async def _inject_bridge_plugin(self):
        """注入 DevBridge 插件到主程序"""
        console.print("[cyan]🔗 注入开发模式插件...[/cyan]")

        # DevBridge 插件源路径
        bridge_source = Path(__file__).parent.parent / "dev" / "bridge_plugin"

        if not bridge_source.exists():
            raise FileNotFoundError(f"DevBridge 插件源不存在: {bridge_source}")

        # 目标路径
        bridge_target = self.mmc_path / "plugins" / "dev_bridge"

        # 如果已存在，先删除
        if bridge_target.exists():
            shutil.rmtree(bridge_target)

        # 复制插件
        shutil.copytree(bridge_source, bridge_target)

        console.print(f"[green]✓ DevBridge 插件已注入: {bridge_target}[/green]")

    async def _cleanup_bridge_plugin(self):
        """清理 DevBridge 插件"""
        bridge_target = self.mmc_path / "plugins" / "dev_bridge"

        if bridge_target.exists():
            try:
                shutil.rmtree(bridge_target)
                console.print("[cyan]🧹 DevBridge 插件已清理[/cyan]")
            except Exception as e:
                console.print(f"[yellow]警告: 清理 DevBridge 插件失败: {e}[/yellow]")

    async def _start_main_process(self):
        """启动主程序"""
        console.print(f"[cyan]🚀 启动主程序: {self.mmc_path / 'bot.py'}[/cyan]")

        # 获取 Python 命令
        python_cmd = self.config.get_python_command()
        venv_type = self.config.venv_type
        venv_path = self.config.venv_path

        # 启动进程
        try:
            import os
            import sys

            # Windows 下打开新窗口
            if os.name == "nt":
                # 根据虚拟环境类型构建启动命令
                if venv_type in ["venv", "uv"] and venv_path:
                    # venv/uv: 先激活环境再启动
                    activate_script = venv_path / "Scripts" / "activate.bat"
                    if activate_script.exists():
                        # 使用 cmd /k 保持窗口打开，先设置编码再激活和启动
                        cmd = ["cmd", "/k", f"chcp 65001 && cd /d {self.mmc_path} && {activate_script} && python bot.py"]
                        console.print(f"[dim]命令: 激活 {venv_type} 环境并启动[/dim]")
                    else:
                        # 降级到直接使用 Python 可执行文件
                        cmd = ["cmd", "/k", f"chcp 65001 && cd /d {self.mmc_path} && {python_cmd[0]} bot.py"]
                        console.print("[yellow]警告: 未找到激活脚本，使用直接启动[/yellow]")
                elif venv_type == "conda" and venv_path:
                    # conda: 使用 conda activate
                    cmd = ["cmd", "/k", f"chcp 65001 && cd /d {self.mmc_path} && conda activate {venv_path} && python bot.py"]
                    console.print("[dim]命令: 激活 conda 环境并启动[/dim]")
                elif venv_type == "poetry":
                    # poetry: 使用 poetry run
                    cmd = ["cmd", "/k", f"chcp 65001 && cd /d {self.mmc_path} && poetry run python bot.py"]
                    console.print("[dim]命令: 使用 poetry run 启动[/dim]")
                else:
                    # 无虚拟环境或其他情况
                    cmd = ["cmd", "/k", f"chcp 65001 && cd /d {self.mmc_path} && python bot.py"]
                    console.print("[dim]命令: 使用系统 Python 启动[/dim]")

                self.process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # Linux/Mac 打开新终端窗口
                if venv_type in ["venv", "uv"] and venv_path:
                    # venv/uv: 先激活环境再启动
                    activate_script = venv_path / "bin" / "activate"
                    if activate_script.exists():
                        shell_cmd = f"cd {self.mmc_path} && source {activate_script} && python bot.py; exec $SHELL"
                    else:
                        # 降级到直接使用 Python 可执行文件
                        shell_cmd = f"cd {self.mmc_path} && {python_cmd[0]} bot.py; exec $SHELL"
                        console.print("[yellow]警告: 未找到激活脚本，使用直接启动[/yellow]")
                    console.print(f"[dim]命令: 激活 {venv_type} 环境并启动[/dim]")
                elif venv_type == "conda" and venv_path:
                    # conda: 使用 conda activate
                    shell_cmd = f"cd {self.mmc_path} && conda activate {venv_path} && python bot.py; exec $SHELL"
                    console.print("[dim]命令: 激活 conda 环境并启动[/dim]")
                elif venv_type == "poetry":
                    # poetry: 使用 poetry run
                    shell_cmd = f"cd {self.mmc_path} && poetry run python bot.py; exec $SHELL"
                    console.print("[dim]命令: 使用 poetry run 启动[/dim]")
                else:
                    # 无虚拟环境
                    shell_cmd = f"cd {self.mmc_path} && python bot.py; exec $SHELL"
                    console.print("[dim]命令: 使用系统 Python 启动[/dim]")

                # 检测桌面环境并使用相应的终端
                if sys.platform == "darwin":
                    # macOS: 使用 osascript 打开 Terminal.app
                    cmd = [
                        "osascript",
                        "-e",
                        f'tell application "Terminal" to do script "{shell_cmd}"',
                    ]
                else:
                    # Linux: 尝试常见的终端模拟器
                    terminals = [
                        ("gnome-terminal", ["gnome-terminal", "--", "bash", "-c", shell_cmd]),
                        ("konsole", ["konsole", "-e", "bash", "-c", shell_cmd]),
                        ("xfce4-terminal", ["xfce4-terminal", "-e", f"bash -c '{shell_cmd}'"]),
                        ("xterm", ["xterm", "-e", f"bash -c '{shell_cmd}'"]),
                    ]

                    cmd = None
                    for term_name, term_cmd in terminals:
                        # 检查终端是否可用
                        if subprocess.run(["which", term_name], capture_output=True).returncode == 0:
                            cmd = term_cmd
                            break

                    if cmd is None:
                        # 降级到不打开新窗口
                        console.print("[yellow]警告: 未找到支持的终端模拟器，使用后台启动[/yellow]")
                        cmd = ["bash", "-c", f"cd {self.mmc_path} && source {activate_script} && python bot.py" if venv_type in ["venv", "uv"] and activate_script.exists() else f"cd {self.mmc_path} && python bot.py"]
                        self.process = subprocess.Popen(
                            cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        console.print("[green]✓ 主程序已启动（后台）[/green]")
                        return

                self.process = subprocess.Popen(cmd)
            console.print("[green]✓ 主程序已启动（新窗口）[/green]")
        except Exception as e:
            raise RuntimeError(f"启动主程序失败: {e}")

    async def _discover_main_server(self):
        """通过发现服务器获取主程序端口"""
        console.print("[cyan]⏳ 等待主程序就绪...[/cyan]")

        max_retries = 10
        retry_delay = 1.0

        await asyncio.sleep(10)
        for i in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://127.0.0.1:{DISCOVERY_PORT}/api/server-info", timeout=aiohttp.ClientTimeout(total=2)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self.main_host = data["host"]
                            self.main_port = data["port"]
                            console.print(f"[green]✓ 发现主程序: http://{self.main_host}:{self.main_port}[/green]")
                            return
            except Exception as e:
                if i < max_retries - 1:
                    console.print(f"[dim]重试 {i + 1}/{max_retries}...[/dim]")
                    await asyncio.sleep(retry_delay)
                else:
                    raise RuntimeError(f"无法连接到发现服务器: {e}")

    async def _connect_websocket(self):
        """连接 WebSocket"""
        console.print("[cyan]🔌 连接开发模式接口...[/cyan]")

        ws_url = f"ws://{self.main_host}:{self.main_port}/plugins/dev_bridge/dev_bridge_router/ws"

        max_retries = 5
        retry_delay = 1.0

        for i in range(max_retries):
            try:
                self.websocket = await websockets.connect(ws_url)
                console.print("[green]✓ 已连接到主程序[/green]")
                return
            except Exception as e:
                if i < max_retries - 1:
                    console.print(f"[dim]重试 {i + 1}/{max_retries}...[/dim]")
                    await asyncio.sleep(retry_delay)
                else:
                    raise RuntimeError(f"无法连接到 WebSocket: {e}")

    async def _wait_for_plugin_loaded(self):
        """等待插件加载通知"""
        console.print("[cyan]⏳ 等待插件加载...[/cyan]")

        try:
            # 设置超时
            async with asyncio.timeout(10):
                while True:
                    message = await self.websocket.recv()
                    data = json.loads(message)

                    if data.get("type") == "plugins_loaded":
                        loaded = data.get("loaded", [])
                        failed = data.get("failed", [])

                        if self.plugin_name in loaded:
                            console.print(f"[green]✓ 插件已加载: {self.plugin_name}[/green]")
                            return
                        elif self.plugin_name in failed:
                            console.print(f"[red]❌ 插件加载失败: {self.plugin_name}[/red]")
                            raise RuntimeError(f"插件加载失败: {self.plugin_name}")
                        else:
                            console.print(f"[yellow]⚠️  插件未找到: {self.plugin_name}[/yellow]")
                            raise RuntimeError(f"插件未找到: {self.plugin_name}")
        except TimeoutError:
            console.print("[yellow]⚠️  等待插件加载超时[/yellow]")
            raise RuntimeError("等待插件加载超时")

    async def _start_file_watcher(self):
        """启动文件监控"""
        console.print(f"[cyan]👀 开始监控: {self.plugin_path}[/cyan]")

        handler = PluginFileWatcher(
            self.plugin_path,
            self._on_file_changed,
            asyncio.get_running_loop()  # 传递当前事件循环
        )

        self.observer = Observer()
        self.observer.schedule(handler, str(self.plugin_path), recursive=True)
        self.observer.start()

    async def _on_file_changed(self, rel_path: str):
        """文件变化回调"""
        if not self.running or not self.websocket:
            return

        console.print(f"[yellow]📝 检测到变化: {rel_path}[/yellow]")
        console.print(f"[cyan]🔄 重新加载 {self.plugin_name}...[/cyan]")

        try:
            # 只发送重载命令，不等待响应
            # 响应将由 _keep_alive 统一处理
            await self.websocket.send(json.dumps({"command": "reload", "plugin_name": self.plugin_name}))

        except Exception as e:
            console.print(f"[red]❌ 发送重载命令失败: {e}[/red]\n")

    async def _keep_alive(self):
        """保持运行并处理 WebSocket 消息"""
        try:
            while self.running:
                try:
                    # 接收 WebSocket 消息
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)

                    # 处理消息
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type == "reload_result":
                        # 重载结果
                        plugin_name = data.get("plugin_name")
                        if data.get("success"):
                            console.print(f"[green]✅ 插件 {plugin_name} 重载成功[/green]\n")
                        else:
                            console.print(f"[red]❌ 插件重载失败: {data.get('message')}[/red]\n")
                    elif msg_type == "plugin_reloaded":
                        # 广播的重载消息
                        pass
                    elif msg_type == "pong":
                        # 心跳响应
                        pass

                except TimeoutError:
                    # 超时是正常的，继续循环
                    continue
                except websockets.exceptions.ConnectionClosed:
                    console.print("[red]WebSocket 连接已断开[/red]")
                    break

        except KeyboardInterrupt:
            pass


async def dev_command(
    plugin_path: Path | None = None,
    mmc_path: Path | None = None,
):
    """启动开发模式

    Args:
        plugin_path: 插件路径，默认为当前目录
        mmc_path: mmc 主程序路径，默认从配置读取
    """
    # 确定插件路径
    if plugin_path is None:
        plugin_path = Path.cwd()

    # 加载配置
    config = MPDTConfig()

    # 如果未配置，运行配置向导
    if not config.is_configured() and mmc_path is None:
        console.print("[yellow]未找到配置，启动配置向导...[/yellow]\n")
        config = interactive_config()

    # 如果提供了 mmc_path，使用它
    if mmc_path:
        config.mmc_path = mmc_path

    # 验证配置
    valid, errors = config.validate()
    if not valid:
        console.print("[red]配置验证失败：[/red]")
        for error in errors:
            console.print(f"  - {error}")
        console.print("\n请运行 [cyan]mpdt config init[/cyan] 重新配置")
        return

    # 创建并启动开发服务器
    server = DevServer(plugin_path, config, mmc_path)
    await server.start()

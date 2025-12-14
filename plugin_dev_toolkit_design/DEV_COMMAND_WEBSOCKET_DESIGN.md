# mpdt dev 命令终极方案 - WebSocket Bridge

## 核心思路 🎯

**使用插件系统的 Router 组件建立 WebSocket 桥接**，让 mpdt dev 通过 WS 控制主程序的插件重载。

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│           mpdt dev 进程                              │
│  ┌──────────────────────────────────────────────┐  │
│  │      DevServer                                │  │
│  │  1. 连接发现服务器获取主程序端口              │  │
│  │  2. 通过 WebSocket 连接主程序                │  │
│  │  3. 监控插件文件变化 (watchdog)               │  │
│  │  4. 发送重载指令，接收状态反馈                │  │
│  └──────────────────────────────────────────────┘  │
│             │ HTTP Client (发现)                    │
│             │ WebSocket Client (控制)               │
└─────────────┼─────────────────────────────────────┘
              │
              │ 1. GET http://localhost:12318/api/server-info
              │    → {"host": "127.0.0.1", "port": 8000}
              │
              │ 2. WS ws://127.0.0.1:8000/plugin-api/dev_bridge/dev_bridge_router/ws
              │
┌─────────────┼─────────────────────────────────────┐
│             ↓                                        │
│  ┌──────────────────────────────────────────────┐  │
│  │   DiscoveryServer (固定端口 12318)           │  │
│  │  - GET /api/server-info                      │  │
│  │    → 返回主程序动态端口                       │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │  DevBridgePlugin (临时注入)                  │  │
│  │  - DevBridgeRouter (BaseRouterComponent)    │  │
│  │    component_name = "dev_bridge_router"     │  │
│  │    └─ /ws (WebSocket 端点)                  │  │
│  │       完整路径: /plugin-api/dev_bridge/     │  │
│  │                 dev_bridge_router/ws         │  │
│  │    └─ /status (状态查询)                    │  │
│  │    └─ /reload/{plugin} (重载接口)           │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │      PluginManager (主程序)                   │  │
│  │  - reload_registered_plugin() ✅             │  │
│  │  - 处理重载请求                               │  │
│  │  - 发送加载完成通知                          │  │
│  └──────────────────────────────────────────────┘  │
│              主程序 (mmc)                            │
└─────────────────────────────────────────────────────┘
```

## 实现细节

### 0. 发现服务器 (DiscoveryServer)

主程序内置的固定端口服务器，用于提供动态端口信息。

```python
# mpdt/dev/bridge_plugin/discovery_server.py

"""
开发模式发现服务器
固定端口 12318，用于 mpdt dev 获取主程序的动态端口
"""

import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.common.logger import get_logger

    
    完整路径: /plugin-api/dev_bridge/dev_bridge_router/*
    WebSocket: ws://{host}:{port}/plugin-api/dev_bridge/dev_bridge_router/ws
    
logger = get_logger("dev_discovery")

# 发现服务器固定端口
DISCOVERY_PORT = 12318

# 全局变量
_server_instance: Optional[uvicorn.Server] = None


class ServerInfo(BaseModel):
    """主程序服务器信息"""
    host: str
    port: int


def create_discovery_app(main_host: str, main_port: int) -> FastAPI:
    """创建发现服务的 FastAPI 应用"""
    app = FastAPI(
        title="MoFox Dev Discovery Service",
        description="开发模式端口发现服务",
        version="1.0.0"
    )
    
    # 添加 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_header
                    elif command == "get_loaded_plugins":
                        # 获取已加载插件列表
                        await self._handle_status(websocket)
                        
            except WebSocketDisconnect:
                logger.info("🔌 开发工具已断开")
            finally:
                self.active_connections.discard(websocket)
        
        @self.router.post("/notify-loaded")
        async def notify_plugins_loaded():
            """主程序启动完成后调用，通知开发工具插件加载状态"""
            from src.plugin_system.core.plugin_manager import plugin_manager
            
            loaded_plugins = plugin_manager.list_loaded_plugins()
            failed_plugins = list(plugin_manager.failed_plugins.keys())
            
            # 广播给所有连接的开发工具
            await self.broadcast({
                "type": "plugins_loaded",
                "loaded_plugins": loaded_plugins,
                "failed_plugins": failed_plugins,
            })
            
            return {"status": "ok", "notified": len(self.active_connections)}
        """健康检查"""
        return {"status": "ok", "service": "MoFox Dev Discovery"}
    
    @app.get("/api/server-info", response_model=ServerInfo)
    def get_server_info():
        """获取主程序动态端口"""
        return ServerInfo(host=main_host, port=main_port)
    
    return app


async def start_discovery_server(
    main_host: str,
    main_port: int,
    discovery_host: str = "127.0.0.1"
) -> None:
    """启动发现服务器"""
    global _server_instance
    
    app = create_discovery_app(main_host, main_port)
    
    config = uvicorn.Config(
        app=app,
        host=discovery_host,
        port=DISCOVERY_PORT,
        log_level="warning",
        access_log=False
    )
    
    _server_instance = uvicorn.Server(config)
    
    logger.info(f"📡 开发模式发现服务器启动: http://{discovery_host}:{DISCOVERY_PORT}")
    logger.info(f"   主程序地址: http://{main_host}:{main_port}")
    
    try:
        await _server_instance.serve()
    except Exception as e:
        logger.error(f"发现服务器运行出错: {e}")


async def stop_discovery_server() -> None:
    """停止发现服务器"""
    global _server_instance
    
    if _server_instance:
        logger.info("停止发现服务器...")
        _server_instance.should_exit = True
        _server_instance = None
```

### 1. DevBridge 插件 (注入到主程序)

这是一个特殊的插件，在开发模式下临时注入到主程序。

```python
# mpdt/dev/bridge_plugin/plugin.py

from typing import ClassVar, Set
from fastapi import WebSocket, WebSocketDisconnect
from src.plugin_system import (
    BasePlugin,
    BaseRouterComponent,
    ComponentInfo,
    register_plugin,
)
from src.common.logger import get_logger

loggasync def on_plugin_loaded(self):
        """插件加载完成后启动发现服务器"""
        # 从环境变量或配置获取主程序端口
        from src.config import get_config
        config = get_config()
        
        main_host = config.HOST
        main_port = config.PORT
        
        # 启动发现服务器
        from .discovery_server import start_discovery_server
        import asyncio
        
        asyncio.create_task(start_discovery_server(main_host, main_port))
    
    er = get_logger("dev_bridge")


class DevBridgeRouter(BaseRouterComponent):
    """开发模式 WebSocket 路由组件"""
    
    component_name = "dev_bridge_router"
    component_description = "开发模式 WebSocket 控制接口"
    
    # WebSocket 连接池
    active_connections: ClassVar[Set[WebSocket]] = set()
    
    def register_endpoints(self) -> None:
        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket 端点 - 接收开发工具的控制指令"""
            await websocket.accept()
            self.active_connections.add(websocket)
            logger.info("🔌 开发工具已连接")
            
            try:
                while True:
                    # 接收消息
                    data = await websocket.receive_json()
                    command = data.get("command")
                    
                    if command == "reload":
                        # 重载插件
                        plugin_name = data.get("plugin_name")
                        await self._handle_reload(websocket, plugin_name)
                        
                    elif command == "status":
                        # 查询状态
                        await self._handle_status(websocket)
                        
                    elif command == "ping":
                        # 心跳
                        await websocket.send_json({"type": "pong"})
                        
            except WebSocketDisconnect:
                logger.info("🔌 开发工具已断开")
            finally:
                self.active_connections.discard(websocket)
        
        @self.router.post("/reload/{plugin_name}")
        async def reload_plugin(plugin_name: str):
            """HTTP 重载接口（备用）"""
            return await self._do_reload(plugin_name)
        
        @self.router.get("/status")
        async def get_status():
            """状态查询接口"""
            from src.plugin_system.core.plugin_manager import plugin_manager
            return {
                "loaded_plugins": plugin_manager.list_loaded_plugins(),
                "failed_plugins": list(plugin_manager.failed_plugins.keys()),
            }
    
    async def _handle_reload(self, websocket: WebSocket, plugin_name: str):
        """处理重载请求"""
        logger.info(f"🔄 收到重载请求: {plugin_name}")
        
        result = await self._do_reload(plugin_name)
    DISCOVERY_PORT = 12318  # 发现服务器固定端口
    
    def __init__(
        self,
        plugin_path: Path,
        plugin_name: str,
        mmc_path: Path,
    ):
        self.plugin_path = plugin_path
        self.plugin_name = plugin_name
        self.mmc_path = mmc_path
        
        # 动态获取的端口信息
        self.main_host: Optional[str] = None
        self.main_port: Optional[int] = None
        self.ws_url: Optional[str] = None
        
        self.observer: Optional[Observer] = None
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.mmc_process: Optional[subprocess.Popen] = None
        self.plugin_load_failed = Falslugins(),
            "failed_plugins": list(plugin_manager.failed_plugins.keys()),
        })
    
    async def _do_reload(self, plugin_name: str) -> dict:
        """执行重载"""
        from src.plugin_system.core.plugin_manager import plugin_manager
        
        try:
            success = await plugin_manager.reload_registered_plugin(plugin_name)
            
            if success:
                message = f"插件 {plugin_name} 重载成功"
                logger.info(f"✅ {message}")
            else:并获取端口
            await self._discover_main_server()
            
            # 4. 连接 WebSocket
            await self._connect_websocket()
            
            # 5. 等待插件加载通知
            await self._wait_for_load_notification()
            
            # 6 "message": message,
            }
            
        except Exception as e:
            message = f"重载插件时出错: {e}"
            logger.error(f"❌ {message}")
            return {
                "success": False,
                "message": message,
            }
    
    @classmethod
    async def broadcast(cls, message: dict):
        """广播消息到所有连接"""
        for connection in cls.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")


@register_plugin
class DevBridgePlugin(BasePlugin):
    """开发模式桥接插件
    
    临时注入到主程序，提供 WebSocket 控制接口
    """
    
    plugin_name = "dev_bridge"
    enable_plugin = True
    dependencies: ClassVar = []
    python_dependencies: ClassVar = []
    
    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        return [
            (DevBridgeRouter.get_router_info(), DevBridgeRouter)
        ]
```

```python
# mpdt/dev/bridge_plugin/__init__.py

"""开发模式桥接插件"""

from src.plugin_system.base.plugin_metadata import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="dev_bridge",
    version="1.0.0",
    description="开发模式 WebSocket 桥接",
    author="MoFox Dev Team",
    license="MIT",
    dependencies=[],
    python_dependencies=[],
)
```

### 2. mpdt dev 命令实现

```python
# mpdt/commands/dev.py

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import websockets
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

console = Console()


class PluginFileWatcher(FileSystemEventHandler):
    """插件文件监控"""
    
    def __init__(self, callback):
        self.callback = callback
        self._pending_task: Optional[asyncio.Task] = None
    
    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        
        # 只关注相关文件
        if not event.src_path.endswith(('.py', '.toml')):
            return
        
        # 防抖
        if self._pending_task and not self._pending_task.done():
            self._pending_task.cancel()
        
        self._pending_task = asyncio.create_task(
            self._debounced_callback(event.src_path)
        )
    
    async def _debounced_callback(self, file_path: str):
        await asyncio.sleep(0.3)
        await self.callback(file_path)


class DevServer:
    """开发服务器 - 监控文件并通过 WebSocket 控制主程序"""
    
    def __init__(
        self,
        plugin_path: Path,
        plugin_name: str,
        mmc_path: Path,
        ws_port: int = 8765,
    ):
        self.plugin_path = plugin_path
        self.plugin_name = plugin_name
        self.mmc_path = mmc_path
        self.ws_port = ws_port
        self.ws_url = f"ws://localhost:{ws_port}/dev/ws"
        
        self.observer: Optional[Observer] = None
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.mmc_process: Optional[subprocess.Popen] = None
        
    async def start(self):
        """启动开发服务器"""
        console.print(Panel(
            f"[bold green]🚀 MoFox Plugin Dev Server[/bold green]\n\n"
            f"📦 插件: [cyan]{self.plugin_name}[/cyan]\n"
            f"📂 路径: [dim]{self.plugin_path}[/dim]\n"
            f"🎯 主程序: [dim]{self.mmc_path}[/dim]",
            border_style="green"
        ))
        
        try:
            # 1. 注入 DevBridge 插件
            await self._inject_bridge_plugin()
            
            # 2. 启动主程序
            await self._start_mmc()
            
            # 3. 等待主程序就绪
            await asyncio.sleep(3)
            
            # 4. 连接 WebSocket
            await self._connect_websocket()
            
            # 5. 启动文件监控
            self._start_file_watcher()
            
            condiscover_main_server(self):
        """从发现服务器获取主程序端口"""
        console.print("[cyan]📡 查询主程序端口...[/cyan]")
        
        import aiohttp
        
        max_retries = 10
        discovery_url = f"http://127.0.0.1:{self.DISCOVERY_PORT}/api/server-info"
        
        for i in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(discovery_url, timeout=2) as response:
                        if response.status == 200:
                            data = await response.json()
                            self.main_host = data["host"]
                            self.main_port = data["port"]
                            
                            # 构建 WebSocket URL
                            # 格式: ws://{host}:{port}/plugin-api/dev_bridge/dev_bridge_router/ws
                            self.ws_url = (
                                f"ws://{self.main_host}:{self.main_port}"
                                f"/plugin-api/dev_bridge/dev_bridge_router/ws"
                            )
                            
                            console.print(f"[green]✅ 主程序地址: {self.main_host}:{self.main_port}[/green]")
                            return
            except Exception as e:
                if i < max_retries - 1:
                    console.print(f"[dim]等待发现服务器... ({i+1}/{max_retries})[/dim]")
                    await asyncio.sleep(1)
                else:
                    raise Exception(f"无法连接到发现服务器: {e}")
    
    async def _connect_websocket(self):
        """连接到主程序的 WebSocket"""
        console.print("[cyan]🔌 连接开发模式接口...[/cyan]")
        console.print(f"[dim]URL: {self.ws_url}[/dim]")
        
        max_retries = 10
        for i in range(max_retries):
            try:
                self.websocket = await websockets.connect(self.ws_url)
                console.print("[green]✅ 已连接到主程序[/green]")
                return
            except Exception as e:
                if i < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise Exception(f"无法连接到 WebSocket: {e}")
    
    async def _wait_for_load_notification(self):
        """等待主程序发送插件加载完成通知"""
        console.print("[cyan]⏳ 等待插件加载...[/cyan]")
        
        try:
            # 等待 plugins_loaded 消息
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            data = json.loads(response)
            
            if data.get("type") == "plugins_loaded":
                loaded_plugins = data.get("loaded_plugins", [])
                failed_plugins = data.get("failed_plugins", [])
                
                if self.plugin_name in loaded_plugins:
                    console.print(f"[green]✅ 插件已加载: {self.plugin_name}[/green]")
                    self.plugin_load_failed = False
                elif self.plugin_name in failed_plugins:
                    console.print(f"[red]❌ 插件加载失败: {self.plugin_name}[/red]")
                    console.print("[yellow]请检查插件代码和主程序日志[/yellow]")
                    self.plugin_load_failed = True
                else:
                    console.print(f"[yellow]⚠️  插件未找到: {self.plugin_name}[/yellow]")
                    console.print(f"[dim]已加载: {', '.join(loaded_plugins[:5])}...[/dim]")
                    console.print(f"[dim]加载失败: {', '.join(failed_plugins)}[/dim]")
                    self.plugin_load_failed = True
                
                # 询问是否继续
                if self.plugin_load_failed:
                    console.print("\n[yellow]插件未成功加载，但你仍然可以继续开发[/yellow]")
                    console.print("[yellow]修复代码后保存将触发重载[/yellow]\n")
        except asyncio.TimeoutError:
            console.print("[yellow]⚠️  未收到加载通知，将继续监控[/yellow] "bridge_plugin"
        target_dir = self.mmc_path / "plugins" / "dev_bridge"
        
        # 创建软链接
        if not target_dir.exists():
            console.print("[cyan]🔗 注入开发模式插件...[/cyan]")
            try:
                target_dir.symlink_to(bridge_plugin_dir, target_is_directory=True)
            except Exception as e:
                console.print(f"[yellow]⚠️  创建软链接失败，尝试复制: {e}[/yellow]")
                import shutil
                shutil.copytree(bridge_plugin_dir, target_dir)
    
    async def _start_mmc(self):
        """启动主程序"""
        console.print("[cyan]🚀 启动主程序...[/cyan]")
        
        # 构建启动命令
        cmd = [
            sys.executable,
            str(self.mmc_path / "main.py"),
        ]
        
        # 启动进程
        self.mmc_process = subprocess.Popen(
            cmd,
            cwd=str(self.mmc_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        console.print("[green]✅ 主程序已启动[/green]")
    
    async def _connect_websocket(self):
        """连接到主程序的 WebSocket"""
        console.print("[cyan]🔌 连接开发模式接口...[/cyan]")
        
        max_retries = 10
        for i in range(max_retries):
            try:
                self.websocket = await websockets.connect(self.ws_url)
                console.print("[green]✅ 已连接到主程序[/green]")
                return
            except Exception as e:
                if i < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise Exception(f"无法连接到主程序: {e}")
    
    def _start_file_watcher(self):
        """启动文件监控"""
        handler = PluginFileWatcher(self._on_file_changed)
        
        self.observer = Observer()
        self.observer.schedule(handler, str(self.plugin_path), recursive=True)
        self.observer.start()
        
        console.print(f"[green]👀 开始监控: {self.plugin_path}[/green]")
    
    async def _on_file_changed(self, file_path: str):
        """文件变化回调"""
        file_name = Path(file_path).name
        console.print(f"\n[yellow]📝 检测到变化: {file_name}[/yellow]")
        console.print(f"[cyan]🔄 重新加载 {self.plugin_name}...[/cyan]")
        
        if self.websocket:
            try:
                # 发送重载指令
                await self.websocket.send(json.dumps({
                    "command": "reload",
                    "plugin_name": self.plugin_name,
                }))
                
                # 接收结果
                response = await self.websocket.recv()
                result = json.loads(response)
                
                if result.get("success"):
                    console.print(f"[green]✅ {result.get('message')}[/green]\n")
                else:
                    console.print(f"[red]❌ {result.get('message')}[/red]\n")
                    
            except Exception as e:
                console.print(f"[red]❌ 重载失败: {e}[/red]\n")
    
    async def _main_loop(self):
        """主循环 - 保持连接"""
        try:
            while True:
                # 发送心跳
                if self.websocket:
                    await self.websocket.send(json.dumps({"command": "ping"}))
                    await self.websocket.recv()
                
                await asyncio.sleep(5)
                
        except websockets.exceptions.ConnectionClosed:
            console.print("[yellow]⚠️  与主程序的连接已断开[/yellow]")
    
    async def stop(self):
        """停止开发服务器"""
        console.print("\n[yellow]⏳ 正在停止...[/yellow]")
        
        # 停止文件监控
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # 关闭 WebSocket
        if self.websocket:
            await self.websocket.close()
        
        # 停止主程序
        if self.mmc_process:
            self.mmc_process.terminate()
            self.mmc_process.wait(timeout=5)
        
   路由规则说明

### WebSocket 端点完整路径

主程序的路由规则：
```
http://{host}:{port}/plugin-api/{plugin_name}/{component_name}{endpoint_path}
```

对于 DevBridge 插件：
- `plugin_name`: `dev_bridge`
- `component_name`: `dev_bridge_router`
- `endpoint_path`: `/ws` (WebSocket), `/status`, `/reload/{plugin}`

**完整示例：**
```
WebSocket: ws://127.0.0.1:8000/plugin-api/dev_bridge/dev_bridge_router/ws
状态查询: http://127.0.0.1:8000/plugin-api/dev_bridge/dev_bridge_router/status
重载接口: http://127.0.0.1:8000/plugin-api/dev_bridge/dev_bridge_router/reload/my_plugin
```

### 发现服务器

固定端口：`12318`

**端点：**
```
GET http://127.0.0.1:12318/api/health
    → {"status": "ok", "service": "MoFox Dev Discovery"}

GET http://127.0.0.1:12318/api/server-info
    → {"host": "127.0.0.1", "port": 8000}
```

### 动态端口处理

主程序启动时如果端口被占用，会自动切换到其他端口（例如 8000 → 8001）。

mpdt dev 通过发现服务器（固定 12318）动态获取实际端口，确保正确连接。

## 依赖管理

```toml
# mpdt/pyproject.toml

[project]
dependencies = [
    "click>=8.0.0",
    "rich>=13.0.0",
    "watchdog>=3.0.0",
    "websockets>=12.0",
    "aiohttp>=3.9.0",  # 用于连接发现服务器ne = None,
):
    """启动开发模式"""
    
    # 1. 检测插件名称
    plugin_name = plugin_path.name
    
    # 2. 查找主程序
    if not mmc_path:
        mmc_path = _find_mmc_path()
        if not mmc_path:
            console.print("[red]❌ 无法找到 mmc 主程序[/red]")
            console.print("[yellow]提示: 使用 --mmc-path 指定路径[/yellow]")
            return
    
    # 3. 启动开发服务器
    server = DevServer(
        plugin_path=plugin_path,
        plugin_name=plugin_name,
        mmc_path=mmc_path,
    )
    await server.start()


def _find_mmc_path() -> Path | None:
    """自动查找 mmc 路径"""
    search_paths = [
        Path.cwd() / "mmc",
        Path.cwd().parent / "mmc",
        Path(__file__).parent.parent.parent / "mmc",
    ]
    
    for path in search_paths:
        if path.exists() and (path / "main.py").exists():
            return path
    
    return None
```

### 3. CLI 集成

```python
# mpdt/cli.py

@cli.command()
@click.option("--mmc-path", type=click.Path(exists=True), help="mmc 主程序路径")
@click.pass_context
def dev(ctx: click.Context, mmc_path: str | None) -> None:
    """启动开发模式，支持热重载"""
    
    plugin_path = Path.cwd()
    
    if not (plugin_path / "plugin.py").exists():
        console.print("[red]❌ 当前目录不是有效的插件目录[/red]")
        return
    
    import asyncio
    from mpdt.commands.dev import dev_command
    
    asyncio.run(dev_command(
        plugin_path=plugin_path,
        mmc_path=Path(mmc_path) if mmc_path else None,
    ))
```

## 使用流程

```bash
# 在插件目录中
cd my_awesome_plugin

# 启动开发模式
mpdt dev

# 或指定主程序路径
mpdt dev --mmc-path /path/to/mmc
```

**mpdt dev 会自动：**
1. ✅ 注入 DevBridge 插件到主程序
2. ✅ 启动主程序
3. ✅ 通过 WebSocket 连接
4. ✅ 监控文件变化
5. ✅ 自动发送重载指令
6. ✅ 显示实时状态

## 优势分析

### ✅ 核心优势

1. **利用插件系统** - BaseRouterComponent 提供 WebSocket 支持
2. **完全独立** - mpdt dev 独立进程，不需要修改主程序
3. **临时注入** - DevBridge 插件在开发时才存在
4. **双向通信** - 可以获取主程序状态、日志等
5. **优雅清理** - 退出时自动移除 DevBridge

### 📊 技术特点

| 特性 | 实现方式 |
|-----|---------|
| 文件监控 | watchdog |
| 通信协议 | WebSocket |
| 插件注入 | 软链接到 plugins/ |
| 重载机制 | 复用 reload_registered_plugin() |
| 进程管理 | subprocess.Popen |

## 依赖管理

```toml
# mpdt/pyproject.toml

[project]
dependencies = [
    "click>=8.0.0",
    "rich>=13.0.0",
    "watchdog>=3.0.0",
    "websockets>=12.0",
]
```

## 高级功能（可选）

### 1. 实时日志流

```python
# 在 DevBridgeRouter 中添加日志推送
@self.router.websocket("/logs")
async def log_stream(websocket: WebSocket):
    """实时日志流"""
    # 推送主程序日志到 mpdt dev
```

### 2. 多插件开发

```bash
mpdt dev --plugins plugin1,plugin2
```

### 3. 断点调试

```python
# 支持 debugpy
mpdt dev --debug --debug-port 5678
```

## 配置管理系统

### 为什么需要配置？

开发者环境各不相同：
- 主程序路径可能在不同位置
- 虚拟环境类型多样（venv、uv、conda、poetry）
- 启动文件是 `bot.py`，不是 `main.py`

**解决方案：** 配置服务 + 一次配置，终身使用

### 配置文件结构

```toml
# ~/.mpdt/config.toml

[mmc]
path = "E:/delveoper/mmc010/mmc"
venv_path = "E:/delveoper/mmc010/venv"
venv_type = "venv"  # venv | uv | conda | poetry | none

[dev]
ws_port = 8765
auto_reload = true
reload_delay = 0.3  # 防抖延迟（秒）
```

### 配置管理器实现

```python
# mpdt/utils/config_manager.py

class MPDTConfig:
    """配置管理器"""
    
    def __init__(self):
        # 配置文件位置: ~/.mpdt/config.toml
        self.config_path = Path.home() / ".mpdt" / "config.toml"
        self.config_data = self._load_config()
    
    # === 主程序配置 ===
    
    def set_mmc_path(self, mmc_path: Path):
        """设置主程序路径"""
        # 验证路径
        bot_file = mmc_path / "bot.py"
        if not bot_file.exists():
            raise ValueError(f"未找到 bot.py: {mmc_path}")
        
        self.config_data["mmc"]["path"] = str(mmc_path)
        self._save_config()
    
    def get_mmc_path(self) -> Path | None:
        """获取主程序路径"""
        return Path(self.config_data["mmc"]["path"])
    
    # === 虚拟环境配置 ===
    
    def set_venv(self, venv_path: Path, venv_type: str):
        """设置虚拟环境
        
        Args:
            venv_path: 虚拟环境路径
            venv_type: venv | uv | conda | poetry | none
        """
        self.config_data["mmc"]["venv_path"] = str(venv_path)
   连接发现服务器获取主程序端口（新增）
   ├─ GET http://127.0.0.1:12318/api/server-info
   ├─ 返回: {"host": "127.0.0.1", "port": 8000}
   ├─ 主程序端口可能因占用而动态切换
   └─ 重试 10 次，每次间隔 1 秒
    ↓
5. 建立 WebSocket 连接（更新）
   ├─ 构建路径: ws://{host}:{port}/plugin-api/dev_bridge/dev_bridge_router/ws
   └─ 例如: ws://127.0.0.1:8000/plugin-api/dev_bridge/dev_bridge_router/ws
    ↓
6. 等待插件加载通知（新增）
   ├─ 主程序加载完成后推送消息:
   │  {"type": "plugins_loaded", "loaded_plugins": [...], "failed_plugins": [...]}
   ├─ 检查 plugin_name 是否在 loaded_plugins 中
   ├─ 如果在 failed_plugins 中:
   │  ├─ 显示: ❌ 插件加载失败
   │  ├─ 提示检查代码和日志
   │  └─ 询问是否继续监控（默认 Yes）
   └─ 如果不在任何列表中:
      ├─ 显示: ⚠️ 插件未找到
      └─ 显示已加载和失败的插件列表
    ↓
7. 启动文件监控
   └─ 监控插件目录（即使插件加载失败也继续）
    ↓
8. 文件变化 → 发送重载指令
   ├─ WebSocket.send({"command": "reload", "plugin_name": plugin_name})
   ├─ 使用解析出的 plugin_name（不是目录名）
   ├─ 主程序重载插件（失败不影响主程序）
   └─ 接收结果: {"success": true/false, "message": "..."}
        if venv_type == "none":
            return ["python"]
        
        elif venv_type == "venv":
            # 直接使用虚拟环境中的 Python
            if os.name == "nt":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            return [str(python_exe)]
        
        elif venv_type == "uv":
            # uv 的虚拟环境结构同 venv
            if os.name == "nt":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            return [str(python_exe)]
        
        elif venv_type == "conda":
            return ["conda", "run", "-p", str(venv_path), "python"]
        
        elif venv_type == "poetry":
            return ["poetry", "run", "python"]
        
        return ["python"]
    
    # === 交互式配置 ===
    
    def interactive_setup(self):
        """交互式配置向导"""
        console.print("[bold cyan]🔧 MPDT 配置向导[/bold cyan]\n")
        
        # 1. 主程序路径
        mmc_path = Prompt.ask("主程序路径 (包含 bot.py 的目录)")
        self.set_mmc_path(Path(mmc_path))
        
        # 2. 虚拟环境类型
        venv_type = Prompt.ask(
            "虚拟环境类型",
            choices=["venv", "uv", "conda", "poetry", "none"],
            default="venv"
        )
        
        # 3. 虚拟环境路径
        if venv_type != "none":
            venv_path = Prompt.ask("虚拟环境路径")
            self.set_venv(Path(venv_path), venv_type)
        
        console.print("\n[green]✅ 配置完成！[/green]")
```

### CLI 命令

```bash
# 交互式配置向导
mpdt config init

# 设置主程序路径
mpdt config set-mmc E:/delveoper/mmc010/mmc

# 设置虚拟环境
mpdt config set-venv E:/delveoper/mmc010/venv --type venv
mpdt config set-venv E:/delveoper/mmc010/.venv --type uv
mpdt config set-venv --type none  # 使用系统 Python

# 查看配置
mpdt config show

# 测试配置
mpdt config test
```

## 插件注入与启动流程

### 完整启动流程（更新）

```
mpdt dev (在插件目录中)
    ↓
0. 解析插件名称
   ├─ 读取 plugin.py
   ├─ AST 解析找到 BasePlugin 子类
   ├─ 提取 plugin_name 字段
   └─ 如果失败 → 降级使用目录名 + 警告
    ↓
1. 检查配置
   └─ 如果未配置 → 运行 config init
    ↓
2. 注入 DevBridge 插件
   ├─ 复制 bridge_plugin/ → mmc/plugins/dev_bridge/
   └─ 或创建软链接
    ↓
3. 启动主程序
   ├─ 读取配置获取 Python 命令
   ├─ python_cmd = config.get_python_command()
   ├─ 执行: python_cmd + ["bot.py"]
   └─ 工作目录: mmc_path
    ↓
4. 等待主程序启动 (3秒)
    ↓
5. 建立 WebSocket 连接
   └─ ws://localhost:8765/dev/ws
    ↓
6. 验证插件已加载
   ├─ WebSocket.send({"command": "status"})
   ├─ 检查 plugin_name 是否在已加载列表中
   └─ 如果不在 → 显示警告和已加载插件列表
    ↓
7. 启动文件监控
   └─ 监控插件目录
    ↓
8. 文件变化 → 发送重载指令
   ├─ WebSocket.send({"command": "reload", "plugin_name": plugin_name})
   ├─ 使用解析出的 plugin_name（不是目录名）
   └─ 接收结果并显示
    ↓
9. Ctrl+C 退出
   ├─ 停止文件监控
   ├─ 关闭 WebSocket
   ├─ 终止主程序
   └─ 清理 dev_bridge 插件
```

### 插件名称解析

**关键问题：** 插件目录名 ≠ 插件运行时名称

```python
# 目录结构
my_awesome_plugin/
├── plugin.py
│   └── class MyPlugin:
│           plugin_name = "awesome_plugin"  # 这个才是真实的插件名
└── __init__.py

# 重载时需要使用 "awesome_plugin" 而不是 "my_awesome_plugin"
```

### 插件名称提取器

```python
# mpdt/utils/plugin_parser.py

import ast
from pathlib import Path
from typing import Optional

def extract_plugin_name(plugin_path: Path) -> str | None:
    """从插件目录提取运行时插件名称
    
    Args:
        plugin_path: 插件目录路径
        
    Returns:
        插件名称，如果无法提取则返回 None
    """
    plugin_file = plugin_path / "plugin.py"
    
    if not plugin_file.exists():
        return None
    
    try:
        with open(plugin_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        # 查找继承自 BasePlugin 的类
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否继承 BasePlugin
                for base in node.bases:
                    base_name = None
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr
                    
                    if base_name == "BasePlugin":
                        # 找到插件类，查找 plugin_name 字段
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign):
                                # plugin_name: str = "xxx"
                                if isinstance(item.target, ast.Name):
                                    if item.target.id == "plugin_name":
                                        if isinstance(item.value, ast.Constant):
                                            return item.value.value
                            
                            elif isinstance(item, ast.Assign):
                                # plugin_name = "xxx"
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        if target.id == "plugin_name":
                                            if isinstance(item.value, ast.Constant):
                                                return item.value.value
        
        return None
        
    except Exception as e:
        print(f"解析插件文件失败: {e}")
        return None


def get_plugin_info(plugin_path: Path) -> dict:
    """获取插件详细信息
    
    Args:
        plugin_path: 插件目录路径
        
    Returns:
        插件信息字典: {
            'plugin_name': str,  # 运行时名称
            'dir_name': str,     # 目录名称
            'class_name': str,   # 类名
        }
    """
    plugin_file = plugin_path / "plugin.py"
    
    if not plugin_file.exists():
        return {
            'plugin_name': None,
            'dir_name': plugin_path.name,
            'class_name': None,
        }
    
    try:
        with open(plugin_file, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = None
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr
                    
                    if base_name == "BasePlugin":
                        plugin_name = None
                        
                        # 提取 plugin_name
                        for item in node.body:
                            if isinstance(item, (ast.AnnAssign, ast.Assign)):
                                target_name = None
                                if isinstance(item, ast.AnnAssign):
                                    if isinstance(item.target, ast.Name):
                                        target_name = item.target.id
                                else:
                                    for target in item.targets:
                                        if isinstance(target, ast.Name):
                                            target_name = target.id
                                            break
                                
                                if target_name == "plugin_name":
                                    if isinstance(item.value, ast.Constant):
                                        plugin_name = item.value.value
                                        break
                        
                        return {
                            'plugin_name': plugin_name,
                            'dir_name': plugin_path.name,
                            'class_name': node.name,
                        }
        
        return {
            'plugin_name': None,
            'dir_name': plugin_path.name,
            'class_name': None,
        }
        
    except Exception as e:
        return {
            'plugin_name': None,
            'dir_name': plugin_path.name,
            'class_name': None,
            'error': str(e),
        }
```

### DevServer 启动实现（更新）

```python
# mpdt/commands/dev.py

from mpdt.utils.plugin_parser import extract_plugin_name, get_plugin_info

class DevServer:
    def __init__(self, plugin_path: Path, config: MPDTConfig):
        self.plugin_path = plugin_path
        self.dir_name = plugin_path.name
        
        # 解析插件运行时名称
        self.plugin_name = extract_plugin_name(plugin_path)
      加载失败

```python
# 收到 plugins_loaded 通知后
if self.plugin_name in failed_plugins:
    console.print(f"[red]❌ 插件加载失败: {self.plugin_name}[/red]")
    console.print("\n[yellow]可能的原因：[/yellow]")
    console.print("  1. 语法错误或导入错误")
    console.print("  2. 依赖缺失")
    console.print("  3. BasePlugin 未正确继承")
    console.print("  4. plugin_name 字段错误")
    console.print("\n[yellow]建议操作：[/yellow]")
    console.print("  1. 查看主程序日志获取详细错误")
    console.print("  2. 修复代码后保存，将自动重载")
    console.print("  3. 确保 enable_plugin = True")
    
    console.print("\n[cyan]你仍然可以继续开发，修复后保存即可重载[/cyan]")
    
    if not Confirm.ask("是否继续监控?", default=True):
        await self.stop()
        return

elif self.plugin_name not in loaded_plugins:
    console.print(f"[yellow]⚠️  插件未找到: {self.plugin_name}[/yellow]")
    console.print("\n[yellow]可能的原因：[/yellow]")
    console.print("  1. 插件名称不匹配")
    console.print(f"     - 解析出的名称: {self.plugin_name}")
    console.print(f"     - 目录名: {self.dir_name}")
    console.print("  2. 插件目录不在主程序的 plugins/ 下")
    console.print("  3. plugin.py 文件有问题")
    
    console.print(f"\n[dim]已加载的插件: {', '.join(loaded_plugins[:10])}...[/dim]")
    console.print(f"[dim]加载失败的插件: {', '.join(failed_plugins)}[/dim]")
    
    if not Confirm.ask("是否继续监控?", default=False):
        await self.stop()
        return
```

### 主程序端口被占用

```python
# 发现服务器会自动处理端口切换
# 如果 8000 被占用，主程序会切换到 8001
# mpdt dev 通过发现服务器动态获取实际端口

# 如果发现服务器无法启动（12318 被占用）
try:
    await start_discovery_server(main_host, main_port)
except Exception as e:
    logger.error(f"发现服务器启动失败（端口 12318 可能被占用）: {e}")
    logger.warning("开发模式将不可用")
```

### 连接超时处理

```python
# 发现服务器连接超时
try:
    await self._discover_main_server()
except Exception as e:
    console.print(f"[red]❌ 无法连接到发现服务器: {e}[/red]")
    console.print("\n[yellow]可能的原因：[/yellow]")
    console.print("  1. 主程序未成功启动")
    console.print("  2. DevBridge 插件未加载")
    console.print("  3. 发现服务器端口 12318 被占用")
    console.print("\n[yellow]请检查：[/yellow]")
    console.print("  - 主程序日志")
    console.print("  - plugins/dev_bridge 是否存在")
    return

# WebSocket 连接超时
try:
    await self._connect_websocket()
except Exception as e:
    console.print(f"[red]❌ 无法连接到 WebSocket: {e}[/red]")
    console.print(f"[dim]URL: {self.ws_url}[/dim]")
    console.print("\n[yellow]请检查：[/yellow]")
    console.print("  - 主程序是否正常运行")
    console.print("  - DevBridge 路由组件是否正确注册")
async def start(self):
        """启动开发服务器"""
        # 0. 显示插件信息
        console.print(Panel(
            f"[bold green]🚀 MoFox Plugin Dev Server[/bold green]\n\n"
            f"📂 目录名: [dim]{self.dir_name}[/dim]\n"
            f"📦 插件名: [cyan]{self.plugin_name}[/cyan]\n"
            f"📍 路径: [dim]{self.plugin_path}[/dim]",
            border_style="green"
        ))
        
        # 1. 检查配置
        if not self.mmc_path:
            console.print("[red]❌ 未配置主程序路径[/red]")
            console.print("[yellow]请运行: mpdt config init[/yellow]")
            return
        
        # 2. 验证插件名称
        if not self.plugin_name:
            console.print("[red]❌ 无法确定插件名称[/red]")
            console.print("[yellow]请检查 plugin.py 中是否正确定义了 plugin_name[/yellow]")
            return
        
        # 3. 注入 DevBridge 插件
        await self._inject_bridge_plugin()
        
        # 4. 启动主程序
        await self._start_mmc()
        
        # 5. 连接 WebSocket
        await self._connect_websocket()
        
        # 6. 验证插件已加载
        if not await self._verify_plugin_loaded():
            console.print("[yellow]⚠️  插件可能未正确加载，请检查主程序日志[/yellow]")
            console.print(f"[dim]插件名称: {self.plugin_name}[/dim]")
        
        # 7. 启动文件监控
        self._start_file_watcher()
        
        # 8. 主循环
        await self._main_loop()
    
    async def _verify_plugin_loaded(self) -> bool:
        """验证插件是否已加载到主程序"""
        if not self.websocket:
            return False
        
        try:
            # 查询主程序状态
            await self.websocket.send(json.dumps({"command": "status"}))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            result = json.loads(response)
            
            loaded_plugins = result.get("loaded_plugins", [])
            
            if self.plugin_name in loaded_plugins:
                console.print(f"[green]✅ 插件已加载: {self.plugin_name}[/green]")
                return True
            else:
                console.print(f"[yellow]⚠️  插件未找到: {self.plugin_name}[/yellow]")
                console.print(f"[dim]已加载的插件: {', '.join(loaded_plugins)}[/dim]")
                return False
                
        except Exception as e:
            console.print(f"[yellow]⚠️  无法验证插件状态: {e}[/yellow]")
            return False
    
    async def _inject_bridge_plugin(self):
        """注入 DevBridge 插件"""
        bridge_src = Path(__file__).parent / "bridge_plugin"
        bridge_dst = self.mmc_path / "plugins" / "dev_bridge"
        
        if not bridge_dst.exists():
            console.print("[cyan]🔗 注入开发模式插件...[/cyan]")
            
            # 优先使用软链接
            try:
                bridge_dst.symlink_to(bridge_src, target_is_directory=True)
            except Exception:
                # 降级到复制
                import shutil
                shutil.copytree(bridge_src, bridge_dst)
    
    async def _start_mmc(self):
        """启动主程序"""
        console.print(f"[cyan]🚀 启动主程序: {self.mmc_path}/bot.py[/cyan]")
        
        # 构建启动命令
        cmd = self.python_cmd + ["bot.py"]
        
        console.print(f"[dim]命令: {' '.join(cmd)}[/dim]")
        
        # 启动进程
        self.mmc_process = subprocess.Popen(
            cmd,
            cwd=str(self.mmc_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )awesome_plugin

# 5. 进入插件目录
cd my_awesome_plugin

# 6. 启动开发模式
mpdt dev

# 输出示例：
# ┌──────────────────────────────────────────┐
# │ 🚀 MoFox Plugin Dev Server               │
# │                                           │
# │ 📂 目录名: my_awesome_plugin              │
# │ 📦 插件名: awesome_plugin                 │
# │ 📍 路径: E:/dev/my_awesome_plugin         │
# └──────────────────────────────────────────┘
#
# 🔗 注入开发模式插件...
# 🚀 启动主程序: E:/delveoper/mmc010/mmc/bot.py
# ✅ 主程序已启动
# ⏳ 等待主程序就绪...
# 🔌 连接开发模式接口...
# ✅ 已连接到主程序
# ✅ 插件已加载: awesome_plugin
# 👀 开始监控: E:/dev/my_awesome_plugin
#
# ✨ 开发服务器就绪！
# 监控文件变化中... (Ctrl+C 退出)

# 7. 编辑代码，保存后自动重载
# 输出：
# 📝 检测到变化: plugin.py
# 🔄 重新加载 awesome_plugin...
# ✅ 插件 awesome_plugin 重载成功
```

### 插件名称不匹配的情况

```python
# 目录插件名称解析失败

```python
plugin_name = extract_plugin_name(plugin_path)
if not plugin_name:
    console.print("[red]❌ 无法读取插件名称[/red]")
    console.print("\n[yellow]请检查 plugin.py 中是否包含：[/yellow]")
    console.print("""
class YourPlugin(BasePlugin):
    plugin_name = "your_plugin"  # 这个字段是必需的
    """)
    console.print("\n[yellow]或者使用目录名作为插件名（不推荐）[/yellow]")
    
    if Confirm.ask("是否使用目录名作为插件名?"):
        plugin_name = plugin_path.name
    else:
### 插件加载失败

```python
# 收到 plugins_loaded 通知后
if self.plugin_name in failed_plugins:
    console.print(f"[red]❌ 插件加载失败: {self.plugin_name}[/red]")
    console.print("\n[yellow]可能的原因：[/yellow]")
    console.print("  1. 语法错误或导入错误")
    console.print("  2. 依赖缺失")
    console.print("  3. BasePlugin 未正确继承")
    console.print("  4. plugin_name 字段错误")
    console.print("\n[yellow]建议操作：[/yellow]")
    console.print("  1. 查看主程序日志获取详细错误")
    console.print("  2. 修复代码后保存，将自动重载")
    console.print("  3. 确保 enable_plugin = True")
    
    console.print("\n[cyan]你仍然可以继续开发，修复后保存即可重载[/cyan]")
    
    if not Confirm.ask("是否继续监控?", default=True):
        await self.stop()
        return

elif self.plugin_name not in loaded_plugins:
    console.print(f"[yellow]⚠️  插件未找到: {self.plugin_name}[/yellow]")
    console.print("\n[yellow]可能的原因：[/yellow]")
    console.print("  1. 插件名称不匹配")
    console.print(f"     - 解析出的名称: {self.plugin_name}")
    console.print(f"     - 目录名: {self.dir_name}")
    console.print("  2. 插件目录不在主程序的 plugins/ 下")
    console.print("  3. plugin.py 文件有问题")
    
    console.print(f"\n[dim]已加载的插件: {', '.join(loaded_plugins[:10])}...[/dim]")
    console.print(f"[dim]加载失败的插件: {', '.join(failed_plugins)}[/dim]")
    
    if not Confirm.ask("是否继续监控?", default=False):
        await self.stop()
        return
```

### 主程序端口被占用

```python
# 发现服务器会自动处理端口切换
# 如果 8000 被占用，主程序会切换到 8001
# mpdt dev 通过发现服务器动态获取实际端口

# 如果发现服务器无法启动（12318 被占用）
try:
    await start_discovery_server(main_host, main_port)
except Exception as e:
    logger.error(f"发现服务器启动失败（端口 12318 可能被占用）: {e}")
    logger.warning("开发模式将不可用")
```

### 连接超时处理

```python
# 发现服务器连接超时
try:
    await self._discover_main_server()
except Exception as e:
    console.print(f"[red]❌ 无法连接到发现服务器: {e}[/red]")
    console.print("\n[yellow]可能的原因：[/yellow]")
    console.print("  1. 主程序未成功启动")
    console.print("  2. DevBridge 插件未加载")
    console.print("  3. 发现服务器端口 12318 被占用")
    console.print("\n[yellow]请检查：[/yellow]")
    console.print("  - 主程序日志")
    console.print("  - plugins/dev_bridge 是否存在")
    return

# WebSocket 连接超时
try:
    await self._connect_websocket()
except Exception as e:
    console.print(f"[red]❌ 无法连接到 WebSocket: {e}[/red]")
    console.print(f"[dim]URL: {self.ws_url}[/dim]")
    console.print("\n[yellow]请检查：[/yellow]")
    console.print("  - 主程序是否正常运行")
    console.print("  - DevBridge 路由组件是否正确注册")
    return
```

### 目录名和插件名不同
```python
my_awesome_plugin/
    plugin.py:
        class MyAwesomePlugin(BasePlugin):
            plugin_name = "awesome_plugin"  # 与目录名不同

# mpdt dev 会自动处理
# ✅ 使用 "awesome_plugin" 进行重载
# ✅ 不会使用 "my_awesome_plugin"
```

### 启动命令示例
["E:/delveoper/mmc010/venv/Scripts/python.exe", "bot.py"]

# 2. uv (Windows)
["E:/delveoper/mmc010/.venv/Scripts/python.exe", "bot.py"]

# 3. conda
["conda", "run", "-p", "E:/delveoper/mmc010/conda_env", "python", "bot.py"]

# 4. poetry
["poetry", "run", "python", "bot.py"]
# 注意：需要在 mmc 目录中有 pyproject.toml

# 5. 系统 Python
["python", "bot.py"]
```

## 使用流程完整示例

### 首次使用

```bash
# 1. 安装 mpdt
pip install mofox-plugin-toolkit

# 2. 初始化配置（只需一次）
mpdt config init

# 输入提示：
# 主程序路径: E:/delveoper/mmc010/mmc
# 虚拟环境类型: venv
# 虚拟环境路径: E:/delveoper/mmc010/venv

# 3. 测试配置
mpdt config test

# 输出：
# ✅ 主程序路径有效
# ✅ 找到 bot.py
# ✅ 虚拟环境有效
# Python 命令: E:/delveoper/mmc010/venv/Scripts/python.exe

# 4. 创建插件
mpdt init my_plugin

# 5. 进入插件目录
cd my_plugin
动流程：
# ✅ 启动主程序（使用配置的虚拟环境）
# ✅ 连接发现服务器获取端口
# ✅ 建立 WebSocket 连接
# ✅ 等待插件加载通知
# ✅ 开始监控文件变化

# 7. 修改代码
# 保存后自动重载，立即生效！

# 8. 退出开发模式
# Ctrl+C
```

### 
# 6. 启动开发模式
mpdt dev

# 自插件名称最佳实践

### 推荐的命名方式

```python
# 1. 目录名使用下划线（Python 包命名规范）
my_awesome_plugin/

# 2. 插件运行时名称也使用下划线
class MyAwesomePlugin(BasePlugin):
    plugin_name = "my_awesome_plugin"  # 与目录名一致（推荐）

# 3. 如果需要不同，确保 plugin_name 是唯一的
class MyPlugin(BasePlugin):
    plugin_name = "awesome_plugin"  # 可以与目录名不同
```

### 调试插件名称

```bash
# 使用 mpdt 查看插件信息
mpdt info

# 输出：
# 插件信息
# ├─ 目录名: my_awesome_plugin
# ├─ 插件名: awesome_plugin
# ├─ 类名: MyAwesomePlugin
# └─ 路径: E:/dev/my_awesome_plugin
```

### 常见问题

**Q: 为什么需要区分目录名和插件名？**
A: 因为 PluginManager 使用 `plugin_name` 作为注册键，而不是目录名。

**Q: 如果插件名称解析失败怎么办？**
A: mpdt 会降级使用目录名，但会显示警告。建议修正 plugin.py。

**Q: 可以有多个插件类吗？**
A: 技术上可以，但 mpdt 只会使用第一个找到的 BasePlugin 子类。

## 总结

这个方案完美结合了：
1. ✅ **插件名称解析** - 正确识别运行时插件名
2. ✅ **配置管理** - 一次配置，终身使用
3. ✅ **环境适配** - 支持多种虚拟环境
4. ✅ **插件系统** - 使用 BaseRouterComponent
5. ✅ **独立进程** - mpdt dev 独立运行
6. ✅ **WebSocket** - 双向通信
7. ✅ **临时注入** - 不影响生产环境
8. ✅ **自动管理** - 启动、注入、清理全自动

**核心思路：**
- AST 解析确保使用正确的插件名
- 配置服务解决环境差异
- 将开发工具本身做成插件
## 通信协议详细说明

### WebSocket 消息格式

**客户端 → 服务器：**
```json
// 重载插件
{
  "command": "reload",
  "plugin_name": "awesome_plugin"
}

// 查询状态
{
  "command": "status"
}

// 心跳
{
  "command": "ping"
}

// 获取已加载插件
{
  "command": "get_loaded_plugins"
}
```

**服务器 → 客户端：**
```json
// 重载结果
{
  "type": "reload_result",
  "plugin_name": "awesome_plugin",
  "success": true,
  "message": "插件 awesome_plugin 重载成功"
}

// 状态响应
{
  "type": "status",
  "loaded_plugins": ["plugin1", "plugin2", ...],
  "failed_plugins": ["bad_plugin"]
}

// 心跳响应
{
  "type": "pong"
}

// 插件加载完成通知（主程序推送）
{
  "type": "plugins_loaded",
  "loaded_plugins": ["plugin1", "plugin2", ...],
  "failed_plugins": ["bad_plugin"]
}
```

## 总结

这个方案完美结合了：
1. ✅ **插件名称解析** - 正确识别运行时插件名
2. ✅ **配置管理** - 一次配置，终身使用
3. ✅ **环境适配** - 支持多种虚拟环境
4. ✅ **插件系统** - 使用 BaseRouterComponent
5. ✅ **独立进程** - mpdt dev 独立运行
6. ✅ **动态端口** - 发现服务器（固定 12318）+ 主程序（动态端口）
7. ✅ **WebSocket** - 双向通信
8. ✅ **加载通知** - 主程序推送插件加载状态
9. ✅ **失败处理** - 插件加载失败不影响主程序和开发流程
10. ✅ **临时注入** - 不影响生产环境
11. ✅ **自动管理** - 启动、注入、清理全自动

**核心思路：**
- AST 解析确保使用正确的插件名
- 配置服务解决环境差异
- 将开发工具本身做成插件
- 发现服务器（12318）提供动态端口
- 正确的路由规则（/plugin-api/...）
- WebSocket 提供控制通道

**关键改进：**
- 🆕 读取插件类中的 `plugin_name` 字段
- 🆕 发现服务器动态获取主程序端口
- 🆕 主程序加载完成后推送插件状态
- 🆕 插件加载失败不影响开发流程
- 🆕 详细的错误提示和调试信息
- 🆕 正确的 WebSocket 路径构建

**端口策略：**
- 发现服务器：固定 `12318`
- 主程序：动态端口（从 .env 读取，占用时自动切换）
- mpdt dev 通过发现服务器获取主程序实际端口

🎯
Windows: `C:\Users\用户名\.mpdt\config.toml`
Linux/Mac: `~/.mpdt/config.toml`

## 错误处理

### 配置未设置

```python
if not config.get_mmc_path():
    console.print("[red]❌ 未配置主程序路径[/red]")
    console.print("\n[yellow]请先运行配置向导：[/yellow]")
    console.print("  mpdt config init")
    console.print("\n[yellow]或手动设置：[/yellow]")
    console.print("  mpdt config set-mmc /path/to/mmc")
    return
```

### 虚拟环境无效

```python
if not config._validate_venv(venv_path, venv_type):
    console.print("[red]❌ 虚拟环境配置无效[/red]")
    console.print(f"路径: {venv_path}")
    console.print(f"类型: {venv_type}")
    console.print("\n[yellow]请重新配置：[/yellow]")
    console.print("  mpdt config set-venv /path/to/venv --type venv")
    return
```

### 主程序启动失败

```python
# 检查进程是否正常启动
if self.mmc_process.poll() is not None:
    # 进程已退出
    stdout, stderr = self.mmc_process.communicate()
    console.print("[red]❌ 主程序启动失败[/red]")
    console.print("\n[yellow]标准输出：[/yellow]")
    console.print(stdout)
    console.print("\n[yellow]错误输出：[/yellow]")
    console.print(stderr)
    return
```

## 配置迁移和版本管理

```toml
# ~/.mpdt/config.toml

[meta]
version = 1  # 配置文件版本

[mmc]
path = "..."
venv_path = "..."
venv_type = "venv"

[dev]
ws_port = 8765
auto_reload = true
reload_delay = 0.3

# 未来可扩展
[build]
output_dir = "dist"
format = "zip"

[test]
test_command = "pytest"
```

## 实现优先级

### Phase 1: 配置系统（必须）✅
- [x] MPDTConfig 类
- [x] 交互式配置向导
- [x] CLI 命令 (config init/set/show)
- [x] 虚拟环境处理
- [x] 配置验证

### Phase 2: DevBridge 插件（必须）
- [ ] DevBridgeRouter (WebSocket 端点)
- [ ] 重载处理逻辑
- [ ] 状态查询接口

### Phase 3: DevServer（必须）
- [ ] 配置集成
- [ ] 插件注入逻辑
- [ ] 主程序启动
- [ ] WebSocket 客户端
- [ ] 文件监控

### Phase 4: 增强功能（可选）
- [ ] 实时日志流
- [ ] 多插件监控
- [ ] 调试模式
- [ ] Web 控制界面

## 总结

这个方案完美结合了：
1. ✅ **配置管理** - 一次配置，终身使用
2. ✅ **环境适配** - 支持多种虚拟环境
3. ✅ **插件系统** - 使用 BaseRouterComponent
4. ✅ **独立进程** - mpdt dev 独立运行
5. ✅ **WebSocket** - 双向通信
6. ✅ **临时注入** - 不影响生产环境
7. ✅ **自动管理** - 启动、注入、清理全自动

**核心思路：**
- 配置服务解决环境差异
- 将开发工具本身做成插件
- WebSocket 提供控制通道

🎯

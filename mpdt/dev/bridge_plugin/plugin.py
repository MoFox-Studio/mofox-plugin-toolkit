"""
DevBridge 插件 - 为 mpdt dev 提供 WebSocket 桥接
临时注入到主程序，提供插件重载接口
"""

import asyncio
from typing import ClassVar

from fastapi import WebSocket, WebSocketDisconnect
from src.common.logger import get_logger
from src.common.server import get_global_server
from src.plugin_system import (
    BasePlugin,
    register_plugin,
)
from src.plugin_system.base.base_http_component import BaseRouterComponent
from src.plugin_system.base.component_types import ComponentInfo

logger = get_logger("dev_bridge")


class DevBridgeRouter(BaseRouterComponent):
    """开发模式 WebSocket 路由组件"""

    component_name = "dev_bridge_router"
    component_description = "开发模式 WebSocket 桥接，提供插件重载接口"
    component_version = "1.0.0"

    def __init__(self, plugin_config: dict | None = None):
        """初始化路由组件"""
        self.active_connections: set[WebSocket] = set()
        super().__init__(plugin_config)

    def register_endpoints(self) -> None:
        """注册 HTTP 端点"""

        @self.router.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket 端点 - 与 mpdt dev 通信

            完整路径: ws://{host}:{port}/plugin-api/dev_bridge/dev_bridge_router/ws

            消息格式:
                客户端 → 服务器:
                    {"command": "reload", "plugin_name": "xxx"}
                    {"command": "status"}
                    {"command": "ping"}
                    {"command": "get_loaded_plugins"}

                服务器 → 客户端:
                    {"type": "reload_result", "success": true, "message": "..."}
                    {"type": "status", "loaded_plugins": [...], "failed_plugins": [...]}
                    {"type": "pong"}
                    {"type": "plugins_loaded", "loaded": [...], "failed": [...]}
            """
            await websocket.accept()
            self.active_connections.add(websocket)
            logger.info("开发模式客户端已连接")

            # 立即发送插件加载状态
            try:
                status = self._get_plugin_status()
                await websocket.send_json({
                    "type": "plugins_loaded",
                    "loaded": status["loaded_plugins"],
                    "failed": status["failed_plugins"]
                })
                logger.info(f"已发送插件状态: {len(status['loaded_plugins'])} 个已加载")
            except Exception as e:
                logger.error(f"发送插件状态失败: {e}")

            try:
                while True:
                    data = await websocket.receive_json()
                    command = data.get("command")

                    if command == "reload":
                        plugin_name = data.get("plugin_name")
                        if not plugin_name:
                            await websocket.send_json({"type": "error", "message": "缺少 plugin_name 参数"})
                            continue

                        # 执行插件重载
                        success, message = await self._reload_plugin(plugin_name)
                        await websocket.send_json(
                            {
                                "type": "reload_result",
                                "success": success,
                                "plugin_name": plugin_name,
                                "message": message,
                            }
                        )

                    elif command == "status":
                        # 返回插件状态
                        logger.info("返回插件状态")
                        status = self._get_plugin_status()
                        await websocket.send_json({"type": "status", **status})

                    elif command == "ping":
                        await websocket.send_json({"type": "pong"})

                    elif command == "get_loaded_plugins":
                        status = self._get_plugin_status()
                        await websocket.send_json(
                            {
                                "type": "loaded_plugins",
                                "loaded": status["loaded_plugins"],
                                "failed": status["failed_plugins"],
                            }
                        )

                    else:
                        await websocket.send_json({"type": "error", "message": f"未知命令: {command}"})

            except WebSocketDisconnect:
                logger.info("开发模式客户端已断开")
            except Exception as e:
                logger.error(f"WebSocket 通信错误: {e}")
            finally:
                self.active_connections.discard(websocket)

        @self.router.get("/status")
        async def get_status():
            """HTTP 状态查询端点

            完整路径: http://{host}:{port}/plugin-api/dev_bridge/dev_bridge_router/status
            """
            return self._get_plugin_status()

        @self.router.post("/reload/{plugin_name}")
        async def reload_plugin(plugin_name: str):
            """HTTP 重载端点

            完整路径: http://{host}:{port}/plugin-api/dev_bridge/dev_bridge_router/reload/{plugin_name}
            """
            success, message = await self._reload_plugin(plugin_name)
            return {"success": success, "plugin_name": plugin_name, "message": message}

    async def _reload_plugin(self, plugin_name: str) -> tuple[bool, str]:
        """重载插件

        Args:
            plugin_name: 插件名称（不是目录名）

        Returns:
            (成功, 消息)
        """
        from src.plugin_system.apis import (
            plugin_manage_api,
        )

        try:
            logger.info(f"开始重载插件: {plugin_name}")
            success = await plugin_manage_api.reload_plugin(plugin_name)

            # 广播重载成功消息
            await self._broadcast({"type": "plugin_reloaded", "plugin_name": plugin_name, "success": success})

            return True, f"插件 {plugin_name} 重载成功"
        except Exception as e:
            error_msg = f"插件重载失败: {e}"
            logger.error(error_msg)

            # 广播重载失败消息
            await self._broadcast(
                {"type": "plugin_reloaded", "plugin_name": plugin_name, "success": False, "error": str(e)}
            )

            return False, error_msg

    def _get_plugin_status(self) -> dict:
        """获取插件状态"""
        # 使用 plugin_info_api 获取插件列表
        from src.plugin_system.apis import (
            plugin_info_api,
        )

        loaded_plugins = plugin_info_api.list_plugins("loaded")
        failed_plugins = plugin_info_api.list_plugins("failed")

        return {"loaded_plugins": loaded_plugins, "failed_plugins": failed_plugins}

    async def _broadcast(self, message: dict) -> None:
        """向所有连接的客户端广播消息"""
        if not self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"广播消息失败: {e}")
                disconnected.add(connection)

        # 清理断开的连接
        self.active_connections -= disconnected


@register_plugin
class DevBridgePlugin(BasePlugin):
    """开发模式桥接插件

    这是一个特殊的插件，在开发模式下临时注入到主程序。
    通过 WebSocket 与 mpdt dev 通信，提供插件重载等功能。
    """

    plugin_name = "dev_bridge"
    enable_plugin = True
    config_file_name = "config.toml"
    dependencies: ClassVar = []
    python_dependencies: ClassVar = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router_component: DevBridgeRouter | None = None
        self._discovery_task: asyncio.Task | None = None

    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """注册路由组件"""
        return [(DevBridgeRouter.get_router_info(), DevBridgeRouter)]

    async def on_plugin_loaded(self):
        """插件加载完成后启动发现服务器"""
        from .discovery_server import start_discovery_server

        # 获取主程序的 host 和 port
        # 从 app_state 或配置中获取
        try:
            server = get_global_server()
            main_host = server.host
            main_port = server.port
        except Exception:
            main_host = "127.0.0.1"
            main_port = 8000

        # 启动发现服务器
        self._discovery_task = asyncio.create_task(start_discovery_server(main_host, main_port))

        logger.info("DevBridge 插件已加载，发现服务器: http://127.0.0.1:12318")
        logger.info(f"WebSocket 端点: ws://{main_host}:{main_port}/plugin-api/dev_bridge/dev_bridge_router/ws")

    async def on_plugin_unload(self):
        """插件卸载时停止发现服务器"""
        from .discovery_server import stop_discovery_server

        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass

        await stop_discovery_server()
        logger.info("DevBridge 插件已卸载")

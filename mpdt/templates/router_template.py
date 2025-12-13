"""
Router 组件模板
"""

ROUTER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from fastapi import APIRouter, HTTPException
from src.common.logger import get_logger
from src.plugin_system import BaseRouterComponent

logger = get_logger(__name__)


class {class_name}(BaseRouterComponent):
    """
    {description}

    Router 组件用于对外暴露 HTTP 接口。

    使用场景：
    - 提供 RESTful API
    - Webhook 接收端点
    - 自定义 HTTP 服务
    - 与外部系统集成
    """

    # Router 元数据
    component_name: str = "{router_name}"
    component_description: str = "{description}"
    component_version: str = "1.0.0"

    def register_endpoints(self) -> None:
        """
        注册 HTTP 端点

        使用 self.router 来添加路由:
        - @self.router.get("/path")
        - @self.router.post("/path")
        - @self.router.put("/path")
        - @self.router.delete("/path")
        """

        @self.router.get("/hello")
        async def hello():
            """
            示例 GET 端点
            """
            return {{"message": "Hello from {{self.component_name}}"}}

        @self.router.get("/status")
        async def get_status():
            """
            获取状态
            """
            try:
                # TODO: 实现状态检查逻辑
                return {{
                    "status": "ok",
                    "component": self.component_name,
                    "version": self.component_version
                }}
            except Exception as e:
                logger.error(f"获取状态失败: {{e}}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/webhook")
        async def webhook(data: dict):
            """
            Webhook 接收端点

            Args:
                data: 接收的数据
            """
            try:
                logger.info(f"收到 webhook 数据: {{data}}")

                # TODO: 处理 webhook 数据
                result = await self._process_webhook(data)

                return {{
                    "success": True,
                    "result": result
                }}
            except Exception as e:
                logger.error(f"处理 webhook 失败: {{e}}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/data/{{item_id}}")
        async def get_item(item_id: str):
            """
            获取指定项目

            Args:
                item_id: 项目ID
            """
            try:
                # TODO: 实现获取逻辑
                item = await self._get_item(item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
                return item
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取项目失败: {{e}}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/data")
        async def create_item(data: dict):
            """
            创建新项目

            Args:
                data: 项目数据
            """
            try:
                # TODO: 实现创建逻辑
                result = await self._create_item(data)
                return {{
                    "success": True,
                    "item_id": result
                }}
            except Exception as e:
                logger.error(f"创建项目失败: {{e}}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _process_webhook(self, data: dict) -> dict:
        """
        处理 webhook 数据

        Args:
            data: webhook 数据

        Returns:
            处理结果
        """
        # TODO: 实现 webhook 处理逻辑
        return {{"processed": True}}

    async def _get_item(self, item_id: str) -> dict | None:
        """
        获取项目

        Args:
            item_id: 项目ID

        Returns:
            项目数据或 None
        """
        # TODO: 实现获取逻辑
        return {{"id": item_id, "name": "示例项目"}}

    async def _create_item(self, data: dict) -> str:
        """
        创建项目

        Args:
            data: 项目数据

        Returns:
            新项目ID
        """
        # TODO: 实现创建逻辑
        return "new_item_id"
'''


def get_router_template() -> str:
    """获取 Router 组件模板"""
    return ROUTER_TEMPLATE

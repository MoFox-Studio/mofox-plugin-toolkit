"""
Router 组件模板（Neo-MoFox 架构）
"""

ROUTER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from fastapi import HTTPException
from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseRouter

logger = get_logger(__name__)


class {class_name}(BaseRouter):
    """
    {description}

    Router 组件用于对外暴露 HTTP 接口。

    使用场景：
    - 提供 RESTful API
    - Webhook 接收端点
    - 自定义 HTTP 服务
    - 与外部系统集成
    """

    router_name = "{component_name}"
    router_description = "{description}"
    custom_route_path = "/api/{component_name}"  # 自定义路由路径
    cors_origins = ["*"]  # CORS 配置，None 表示禁用 CORS

    def register_endpoints(self) -> None:
        """
        注册 HTTP 端点

        使用 self.app 来添加路由:
        - @self.app.get("/path")
        - @self.app.post("/path")
        - @self.app.put("/path")
        - @self.app.delete("/path")
        """

        @self.app.get("/hello")
        async def hello():
            """
            示例 GET 端点
            """
            return {{"message": f"Hello from {{self.router_name}}"}}

        @self.app.get("/status")
        async def get_status():
            """
            获取状态
            """
            try:
                # TODO: 实现状态检查逻辑
                return {{
                    "status": "ok",
                    "router": self.router_name,
                }}
            except Exception as e:
                logger.error(f"获取状态失败: {{e}}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/webhook")
        async def webhook(data: dict):
            """
            Webhook 接收端点

            Args:
                data: 接收的数据
            """
            try:
                logger.info(f"收到 webhook 数据: {{data}}")

                # TODO: 处理 webhook 数据

                return {{
                    "success": True,
                    "message": "Webhook received"
                }}
            except Exception as e:
                logger.error(f"处理 webhook 失败: {{e}}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/data/{{item_id}}")
        async def get_item(item_id: str):
            """
            获取指定项目

            Args:
                item_id: 项目ID
            """
            try:
                logger.info(f"获取项目: {{item_id}}")
                # TODO: 实现获取逻辑
                return {{
                    "item_id": item_id,
                    "data": "example data"
                }}
            except Exception as e:
                logger.error(f"获取项目失败: {{e}}")
                raise HTTPException(status_code=404, detail=str(e))
'''


def get_router_template() -> str:
    """获取 Router 组件模板"""
    return ROUTER_TEMPLATE

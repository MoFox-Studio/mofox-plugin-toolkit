"""
Service 组件模板（Neo-MoFox 架构）
"""

SERVICE_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseService

logger = get_logger(__name__)


class {class_name}(BaseService):
    """
    {description}

    Service 组件暴露特定功能供其他插件或组件调用。
    可以实现 typing.Protocol 定义的接口标准（如 MemoryService, ConfigService 等）。

    使用场景：
    - 提供通用功能服务
    - 插件间功能共享
    - 实现标准协议接口
    """

    service_name = "{component_name}"
    service_description = "{description}"
    version = "1.0.0"

    async def initialize(self) -> bool:
        """
        初始化服务

        Returns:
            bool: 是否初始化成功
        """
        try:
            logger.info(f"初始化服务: {{self.service_name}}")
            # TODO: 实现初始化逻辑
            return True
        except Exception as e:
            logger.error(f"服务初始化失败: {{e}}")
            return False

    async def shutdown(self) -> None:
        """
        关闭服务，清理资源
        """
        try:
            logger.info(f"关闭服务: {{self.service_name}}")
            # TODO: 实现清理逻辑
        except Exception as e:
            logger.error(f"服务关闭失败: {{e}}")

    # 示例方法：存储数据
    async def store(self, key: str, value: Any) -> bool:
        """
        存储数据

        Args:
            key: 键
            value: 值

        Returns:
            bool: 是否存储成功
        """
        try:
            logger.debug(f"存储数据: {{key}} = {{value}}")
            # TODO: 实现存储逻辑
            return True
        except Exception as e:
            logger.error(f"存储失败: {{e}}")
            return False

    # 示例方法：检索数据
    async def retrieve(self, key: str) -> Any | None:
        """
        检索数据

        Args:
            key: 键

        Returns:
            Any | None: 检索到的值，不存在则返回 None
        """
        try:
            logger.debug(f"检索数据: {{key}}")
            # TODO: 实现检索逻辑
            return None
        except Exception as e:
            logger.error(f"检索失败: {{e}}")
            return None
'''


def get_service_template() -> str:
    """获取 Service 组件模板"""
    return SERVICE_TEMPLATE

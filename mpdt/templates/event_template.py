"""
Event Handler 组件模板（Neo-MoFox 架构）
"""

EVENT_HANDLER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseEventHandler
from src.core.components.types import EventType

logger = get_logger(__name__)


class {class_name}(BaseEventHandler):
    """
    {description}

    Event Handler 组件用于处理系统事件。

    使用场景：
    - 监听消息事件
    - 监听系统事件
    - 实现事件驱动逻辑
    - 在特定事件发生时执行操作
    """

    handler_name = "{component_name}"
    handler_description = "{description}"
    weight = 10  # 权重：数值越大优先级越高
    intercept_message = False  # 是否拦截消息（拦截后消息不再传递给后续处理器）
    init_subscribe = [EventType.ON_MESSAGE_RECEIVED]  # 初始订阅的事件类型列表

    async def execute(self, kwargs: dict | None) -> tuple[bool, bool, str | None]:
        """
        处理事件

        Args:
            kwargs: 事件参数字典，包含事件相关的所有信息

        Returns:
            tuple[bool, bool, str | None]: (success, intercept, message)
                - success: 是否成功
                - intercept: 是否拦截（True 则阻止后续处理器执行）
                - message: 返回消息（可选）
        """
        try:
            logger.info(f"处理事件: {{self.handler_name}}")
            logger.debug(f"事件参数: {{kwargs}}")

            # 检查是否应该处理此事件
            if not self._should_handle(kwargs):
                logger.debug("跳过此事件")
                return True, False, None

            # TODO: 实现事件处理逻辑
            result = await self._process_event(kwargs)

            logger.info("事件处理完成")
            return True, False, result

        except Exception as e:
            logger.error(f"事件处理失败: {{e}}")
            return False, False, str(e)

    def _should_handle(self, kwargs: dict | None) -> bool:
        """
        判断是否应该处理该事件

        Args:
            kwargs: 事件参数

        Returns:
            是否处理
        """
        # TODO: 实现判断逻辑
        # 示例: 检查事件类型、来源、条件等
        return True

    async def _process_event(self, kwargs: dict | None) -> str:
        """
        处理事件的核心逻辑

        Args:
            kwargs: 事件参数

        Returns:
            处理结果消息
        """
        # TODO: 实现处理逻辑
        return "事件处理成功"
'''


def get_event_handler_template() -> str:
    """获取 Event Handler 组件模板"""
    return EVENT_HANDLER_TEMPLATE

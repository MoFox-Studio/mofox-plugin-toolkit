"""
Event Handler 组件模板
"""

EVENT_HANDLER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.common.logger import get_logger
from src.plugin_system import BaseEventHandler

logger = get_logger(__name__)


class {class_name}(BaseEventHandler):
    """
    {description}

    处理的事件类型: {event_type}

    事件处理器在特定事件发生时被触发，可以用于:
    - 监听消息事件
    - 监听系统事件
    - 实现事件驱动逻辑
    """

    def __init__(self):
        super().__init__()
        self.event_type = "{event_type}"  # 事件类型
        self.priority = 100  # 优先级 (0-1000, 数字越小优先级越高)

    {async_keyword}def handle(self, event: Any, **kwargs: Any) -> Any:
        """
        处理事件

        Args:
            event: 事件对象
            **kwargs: 其他参数

        Returns:
            处理结果
        """
        try:
            logger.info(f"处理事件: {{self.event_type}}")
            logger.debug(f"事件内容: {{event}}")

            # 检查是否应该处理此事件
            if not self.should_handle(event):
                logger.debug("跳过此事件")
                return False

            # TODO: 实现事件处理逻辑
            # 根据事件类型进行不同的处理
            result = self._process_event(event, **kwargs)

            logger.info("事件处理完成")
            return result

        except Exception as e:
            logger.error(f"事件处理失败: {{e}}")
            raise

    def should_handle(self, event: Any) -> bool:
        """
        判断是否应该处理该事件

        Args:
            event: 事件对象

        Returns:
            是否处理
        """
        # TODO: 实现判断逻辑
        # 示例: 检查事件类型、来源等
        return True

    {async_keyword}def _process_event(self, event: Any, **kwargs: Any) -> Any:
        """
        处理事件的具体逻辑

        Args:
            event: 事件对象
            **kwargs: 其他参数

        Returns:
            处理结果
        """
        # TODO: 实现具体的事件处理逻辑
        return True

    def get_priority(self) -> int:
        """
        获取处理优先级

        Returns:
            优先级值
        """
        return self.priority
'''


def get_event_handler_template() -> str:
    """获取 Event Handler 组件模板"""
    return EVENT_HANDLER_TEMPLATE

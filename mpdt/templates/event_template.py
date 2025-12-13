"""
Event Handler 组件模板
"""

EVENT_HANDLER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.common.logger import get_logger
from src.plugin_system import BaseEventHandler, HandlerResult

logger = get_logger(__name__)


class {class_name}(BaseEventHandler):
    """
    {description}

    Event Handler 组件用于处理系统事件。

    处理的事件类型: {event_type}

    使用场景：
    - 监听消息事件
    - 监听系统事件
    - 实现事件驱动逻辑
    - 在特定事件发生时执行操作
    """

    # Event Handler 元数据
    handler_name: str = "{class_name}"
    event_types: list[str] = ["{event_type}"]  # 监听的事件类型列表
    weight: int = 100  # 权重：0-1000，数字越大优先级越高

    async def execute(self, params: dict) -> HandlerResult:
        """
        处理事件

        Args:
            params: 事件参数字典，包含事件相关的所有信息

        Returns:
            HandlerResult: 处理结果
                - success: 是否成功
                - continue_process: 是否继续处理后续 handler
                - message: 返回消息
        """
        try:
            logger.info(f"处理事件: {{self.handler_name}}")
            logger.debug(f"事件参数: {{params}}")

            # 检查是否应该处理此事件
            if not self._should_handle(params):
                logger.debug("跳过此事件")
                return HandlerResult(
                    success=True,
                    continue_process=True,
                    message="已跳过",
                    handler_name=self.handler_name
                )

            # TODO: 实现事件处理逻辑
            result = await self._process_event(params)

            logger.info("事件处理完成")
            return HandlerResult(
                success=True,
                continue_process=True,  # 设为 False 可以阻止后续 handler 执行
                message=result,
                handler_name=self.handler_name
            )

        except Exception as e:
            logger.error(f"事件处理失败: {{e}}")
            return HandlerResult(
                success=False,
                continue_process=True,
                message=str(e),
                handler_name=self.handler_name
            )

    def _should_handle(self, params: dict) -> bool:
        """
        判断是否应该处理该事件

        Args:
            params: 事件参数

        Returns:
            是否处理
        """
        # TODO: 实现判断逻辑
        # 示例: 检查事件类型、来源、条件等
        return True

    async def _process_event(self, params: dict) -> str:
        """
        处理事件的具体逻辑

        Args:
            params: 事件参数

        Returns:
            处理结果消息
        """
        # TODO: 实现具体的事件处理逻辑
        return "处理成功"
'''


def get_event_handler_template() -> str:
    """获取 Event Handler 组件模板"""
    return EVENT_HANDLER_TEMPLATE

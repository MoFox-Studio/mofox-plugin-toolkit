"""
Event Handler 组件模板（Neo-MoFox 架构）
"""

EVENT_HANDLER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseEventHandler
from src.core.components.types import EventType
from src.kernel.event import EventDecision

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

    async def execute(
        self, event_name: str, params: dict[str, Any]
    ) -> tuple[EventDecision, dict[str, Any]]:
        """
        执行事件处理的主要逻辑。

        与 kernel EventBus 订阅者协议保持一致：接受事件名称和参数字典，
        返回决策枚举与（可能已修改的）参数字典。

        Args:
            event_name: 触发本处理器的事件名称（由 EventBus 传入）
            params: 事件参数字典（即 EventBus publish 时的 params，可就地修改）

        Returns:
            tuple[EventDecision, dict[str, Any]]:
                - ``EventDecision.SUCCESS`` — 执行完成，继续后续处理器
                - ``EventDecision.STOP``    — 拦截，阻止后续处理器执行
                - ``EventDecision.PASS``    — 跳过本处理器，不传播参数变更
        """
        try:
            logger.info(f"处理事件: {{event_name}}")
            logger.debug(f"事件参数: {{params}}")

            # 检查是否应该处理此事件
            if not self._should_handle(event_name, params):
                logger.debug("跳过此事件")
                return EventDecision.PASS, params

            # TODO: 实现事件处理逻辑
            await self._process_event(event_name, params)

            logger.info("事件处理完成")
            # 正常处理，继续后续处理器
            return EventDecision.SUCCESS, params

        except Exception as e:
            logger.error(f"事件处理失败: {{e}}", exc_info=True)
            # 发生错误时跳过，不影响其他处理器
            return EventDecision.PASS, params

    def _should_handle(self, event_name: str, params: dict[str, Any]) -> bool:
        """
        判断是否应该处理该事件

        Args:
            event_name: 事件名称
            params: 事件参数

        Returns:
            是否处理
        """
        # TODO: 实现判断逻辑
        # 示例: 检查事件类型、来源、条件等
        # if event_name == EventType.ON_MESSAGE_RECEIVED:
        #     message = params.get("message")
        #     if message and "关键词" in message:
        #         return True
        return True

    async def _process_event(self, event_name: str, params: dict[str, Any]) -> None:
        """
        处理事件的核心逻辑

        Args:
            event_name: 事件名称
            params: 事件参数（可就地修改）
        """
        # TODO: 实现处理逻辑
        # 示例：修改参数
        # params["processed"] = True
        # params["handler_name"] = self.handler_name

        # 示例：根据事件类型执行不同逻辑
        # if event_name == EventType.ON_MESSAGE_RECEIVED:
        #     await self._handle_message(params)
        # elif event_name == EventType.ON_START:
        #     await self._handle_bot_start(params)

        logger.info(f"事件 {{event_name}} 处理完成")
'''


def get_event_handler_template() -> str:
    """获取 Event Handler 组件模板"""
    return EVENT_HANDLER_TEMPLATE

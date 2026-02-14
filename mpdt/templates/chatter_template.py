"""
Chatter 组件模板（Neo-MoFox 架构）
"""

CHATTER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import AsyncGenerator

from src.core.components.base import BaseChatter, Wait, Success, Failure, ChatterResult
from src.core.components.types import ChatType
from src.kernel.logger import get_logger

logger = get_logger(__name__)


class {class_name}(BaseChatter):
    """
    {description}

    Chatter 组件用于处理聊天流程，控制对话的整体逻辑。
    使用生成器模式，通过 yield 返回 Wait/Success/Failure/Stop 结果。

    使用场景：
    - 自定义对话流程
    - 特殊聊天模式处理
    - 对话状态管理
    - 多轮对话控制
    """

    chatter_name = "{component_name}"
    chatter_description = "{description}"
    
    # 关联平台（可选，默认支持所有平台）
    associated_platforms: list[str] = []
    
    # 支持的聊天类型（私聊/群聊/所有）
    chat_type: ChatType = ChatType.ALL

    async def execute(self) -> AsyncGenerator[ChatterResult, None]:
        """
        执行聊天器的主要逻辑。

        使用生成器模式，通过 yield 返回执行结果：
        - Wait: 等待一段时间或等待新消息
        - Success: 成功完成执行
        - Failure: 执行失败
        - Stop: 停止一段时间后重新开始

        Yields:
            ChatterResult: Wait/Success/Failure/Stop 结果
        """
        try:
            logger.info(f"[{{self.chatter_name}}] 开始执行")

            # 获取并刷新未读消息
            unreads_json, unread_messages = await self.fetch_and_flush_unreads(
                format_as_group=True,
                time_format="%H:%M"
            )

            if not unread_messages:
                logger.debug(f"[{{self.chatter_name}}] 无未读消息，等待新消息")
                yield Wait(time=None)  # 等待新消息
                return

            logger.info(f"[{{self.chatter_name}}] 处理 {{len(unread_messages)}} 条未读消息")

            # TODO: 实现聊天处理逻辑
            # 示例：简单响应
            current_msg = unread_messages[-1]  # 最新消息
            message_text = current_msg.processed_plain_text or str(current_msg.content or "")

            # 示例：获取可用组件
            # llm_usables = await self.get_llm_usables()
            # available = await self.modify_llm_usables(llm_usables)
            
            # 示例：执行某个 Action/Tool
            # success, result = await self.exec_llm_usable(
            #     SomeActionClass,
            #     current_msg,
            #     param1="value1"
            # )

            # 构建响应
            response = f"收到消息: {{message_text}}"
            
            # 发送响应（需要使用 chat_stream.send 方法）
            from src.core.managers import get_stream_manager
            stream_manager = get_stream_manager()
            chat_stream = await stream_manager.get_or_create_stream(self.stream_id)
            await chat_stream.send(response)

            # 返回成功结果
            yield Success(
                message="处理完成",
                data={{"processed": len(unread_messages)}}
            )

        except Exception as e:
            logger.error(f"[{{self.chatter_name}}] 执行失败: {{e}}", exc_info=True)
            yield Failure(
                error=f"处理失败: {{e}}",
                exception=e
            )
'''


def get_chatter_template() -> str:
    """获取 Chatter 组件模板"""
    return CHATTER_TEMPLATE

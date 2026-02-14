"""
Chatter 组件模板（Neo-MoFox 架构）
"""

CHATTER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import AsyncGenerator

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseChatter
from src.core.components.types import ChatType

logger = get_logger(__name__)


class {class_name}(BaseChatter):
    """
    {description}

    Chatter 组件用于处理聊天流程，控制对话的整体逻辑。

    使用场景：
    - 自定义对话流程
    - 特殊聊天模式处理
    - 对话状态管理
    - 多轮对话控制
    """

    chatter_name = "{component_name}"
    chatter_description = "{description}"
    chat_types: list[ChatType] = [ChatType.PRIVATE, ChatType.GROUP]  # 支持的聊天类型

    async def chat(self, msg_env) -> AsyncGenerator[str, None]:
        """
        执行聊天处理逻辑（异步生成器）

        Args:
            msg_env: 消息环境对象，包含聊天上下文信息
                - msg_env.message_id: 消息ID
                - msg_env.sender_id: 发送者ID
                - msg_env.text: 消息文本
                - msg_env.chat_type: 聊天类型
                - 等等...

        Yields:
            str: 聊天响应文本，逐步生成
        """
        try:
            logger.info(f"执行 Chatter: {{self.chatter_name}}")
            logger.debug(f"消息环境: {{msg_env}}")

            # TODO: 实现聊天处理逻辑

            # 示例：简单回复
            message = msg_env.text
            response = f"收到消息: {{message}}"
            
            yield response

        except Exception as e:
            logger.error(f"Chatter 执行失败: {{e}}")
            yield f"处理失败: {{e}}"
'''
            处理结果字典，包含：
                - success: 是否成功
                - response: 响应内容（可选）
                - next_action: 下一步动作（可选）
        """
        try:
            logger.info(f"执行 Chatter: {{self.chatter_name}}")
            logger.debug(f"聊天上下文: {{context}}")

            # TODO: 实现聊天处理逻辑

            # 示例：根据消息内容处理
            message = context.message_content
            user_name = context.user_name

            # 可以使用 action_manager 调用 Action
            # result = await self.action_manager.execute_action("action_name", {{}})

            # 构建响应
            response = self._generate_response(message, user_name)

            return {{
                "success": True,
                "response": response,
                "next_action": None
            }}

        except Exception as e:
            logger.error(f"Chatter 执行失败: {{e}}")
            return {{
                "success": False,
                "error": str(e)
            }}

    def _generate_response(self, message: str, user_name: str) -> str:
        """
        生成响应内容

        Args:
            message: 用户消息
            user_name: 用户名

        Returns:
            响应文本
        """
        # TODO: 实现响应生成逻辑
        return f"收到 {{user_name}} 的消息: {{message}}"
        '''


def get_chatter_template() -> str:
    """获取 Chatter 组件模板"""
    return CHATTER_TEMPLATE

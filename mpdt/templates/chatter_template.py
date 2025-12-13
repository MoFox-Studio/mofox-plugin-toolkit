"""
Chatter 组件模板
"""

CHATTER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.common.data_models.message_manager_data_model import StreamContext
from src.common.logger import get_logger
from src.plugin_system import BaseChatter, ChatType

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

    # Chatter 元数据
    chatter_name: str = "{chatter_name}"
    chatter_description: str = "{description}"
    chat_types: list[ChatType] = [ChatType.PRIVATE, ChatType.GROUP]  # 支持的聊天类型

    async def execute(self, context: StreamContext) -> dict:
        """
        执行聊天处理逻辑

        Args:
            context: StreamContext对象，包含聊天上下文信息
                - context.stream_id: 聊天流ID
                - context.user_id: 用户ID
                - context.user_name: 用户名
                - context.message_content: 消息内容
                - context.chat_type: 聊天类型
                - 等等...

        Returns:
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

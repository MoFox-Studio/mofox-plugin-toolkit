"""
Action 组件模板（Neo-MoFox 架构）
"""

ACTION_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base.action import BaseAction

logger = get_logger(__name__)


class {class_name}(BaseAction):
    """
    {description}

    Action 组件用于执行聊天中的具体动作任务。
    """

    action_name = "{component_name}"
    action_description = "{description}"

    # 可选：指定允许使用此 Action 的 chatter
    # chatter_allow: list[str] = ["your_chatter_name"]

    async def execute(self, *args, **kwargs) -> tuple[bool, str]:
        """
        执行 Action 的主要逻辑

        可以使用以下方法：
        - await self._send_to_stream(text)  # 发送消息到流

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            (success: bool, message: str): 执行结果和消息
        """
        try:
            logger.info(f"执行 Action: {{self.action_name}}")

            # TODO: 实现 Action 的核心逻辑
            result_message = "执行成功"

            # 示例：发送消息
            # await self._send_to_stream("你好！")

            return True, result_message

        except Exception as e:
            logger.error(f"Action 执行失败: {{e}}")
            return False, f"执行失败: {{e}}"
'''


def get_action_template() -> str:
    """获取 Action 组件模板"""
    return ACTION_TEMPLATE

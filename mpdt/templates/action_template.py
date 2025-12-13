"""
Action 组件模板
"""

ACTION_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.common.logger import get_logger
from src.plugin_system import BaseAction

logger = get_logger(__name__)


class {class_name}(BaseAction):
    """
    {description}

    这个 Action 用于执行特定的操作任务。

    Args:
        context: 执行上下文
        **kwargs: 其他参数

    Returns:
        执行结果
    """

    def __init__(self):
        super().__init__()
        # TODO: 初始化你的 Action
        self.name = "{component_name}"
        self.description = "{description}"

    {async_keyword}def execute(self, context: Any, **kwargs: Any) -> Any:
        """
        执行 Action

        Args:
            context: 执行上下文
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        try:
            logger.info(f"开始执行 Action: {{self.name}}")

            # TODO: 实现你的逻辑
            result = None

            logger.info(f"Action {{self.name}} 执行完成")
            return result

        except Exception as e:
            logger.error(f"Action {{self.name}} 执行失败: {{e}}")
            raise
    def validate(self, **kwargs: Any) -> bool:
        """
        验证参数
        Args:
            **kwargs: 参数

        Returns:
            是否有效
        """
        # TODO: 实现参数验证逻辑
        return True
'''


def get_action_template() -> str:
    """获取 Action 组件模板"""
    return ACTION_TEMPLATE

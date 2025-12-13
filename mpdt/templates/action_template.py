"""
Action 组件模板
"""

ACTION_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.common.logger import get_logger
from src.plugin_system import BaseAction, ActionActivationType, ChatMode

logger = get_logger(__name__)


class {class_name}(BaseAction):
    """
    {description}

    Action 组件用于执行聊天中的具体动作任务。
    """

    # Action 元数据
    action_name: str = "{component_name}"
    action_description: str = "{description}"

    # 激活配置
    mode_enable: list[ChatMode] = [ChatMode.FOCUS, ChatMode.NORMAL]  # 支持的聊天模式
    parallel_action: bool = False  # 是否允许与其他 Action 并行执行

    # 专注模式激活配置
    focus_activation_type: ActionActivationType = ActionActivationType.KEYWORD
    # 普通模式激活配置
    normal_activation_type: ActionActivationType = ActionActivationType.LLM_JUDGE

    # 激活条件
    activation_keywords: list[str] = ["关键词1", "关键词2"]  # 关键词激活时使用
    keyword_case_sensitive: bool = False  # 关键词是否区分大小写

    # LLM 判断激活的提示词
    llm_judge_prompt: str = """
判断用户是否需要执行某个特定操作。
如果需要，返回 true，否则返回 false。
"""

    async def go_activate(self, llm_judge_model=None) -> bool:
        """
        自定义激活逻辑（推荐方式）

        可以组合使用以下工具函数：
        - await self._keyword_match(["关键词"])  # 关键词匹配
        - await self._random_activation(0.3)  # 随机激活（30%概率）
        - await self._llm_judge_activation(prompt, llm_judge_model)  # LLM判断

        Returns:
            是否激活此 Action
        """
        # 示例：关键词匹配
        return await self._keyword_match(self.activation_keywords, self.keyword_case_sensitive)

    async def execute(self) -> tuple[bool, str]:
        """
        执行 Action 的主要逻辑

        可以使用以下方法：
        - await self.send_text("文本内容")  # 发送文本消息
        - await self.send_image(image_base64)  # 发送图片
        - await self.send_command("command_name", args)  # 调用命令
        - await self.call_action("action_name", data)  # 调用其他 Action
        - await self.wait_for_new_message(timeout)  # 等待用户回复

        Returns:
            (是否成功, 结果消息)
        """
        try:
            logger.info(f"执行 Action: {{self.action_name}}")

            # TODO: 实现 Action 的核心逻辑

            # 示例：发送消息
            await self.send_text("Action 执行成功！")

            # 存储 Action 信息到上下文
            await self.store_action_info(
                action_build_into_prompt=True,
                action_prompt_display=f"执行了 {{self.action_name}}",
                action_done=True
            )

            return True, "执行成功"

        except Exception as e:
            logger.error(f"Action 执行失败: {{e}}")
            return False, f"执行失败: {{e}}"
'''


def get_action_template() -> str:
    """获取 Action 组件模板"""
    return ACTION_TEMPLATE

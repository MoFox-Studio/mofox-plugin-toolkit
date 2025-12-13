"""
Prompt 组件模板
"""

PROMPT_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.chat.utils.prompt_params import PromptParameters
from src.common.logger import get_logger
from src.plugin_system.base.component_types import InjectionRule
logger = get_logger(__name__)


class {class_name}(BasePrompt):
    """
    {description}

    Prompt 组件用于向核心 Prompt 模板注入额外的上下文信息。

    使用场景：
    - 向系统提示词添加自定义指令
    - 注入动态上下文信息
    - 添加角色设定或行为规则
    - 提供额外的背景知识
    """

    # Prompt 组件元数据
    prompt_name: str = "{prompt_name}"
    prompt_description: str = "{description}"

    # 定义注入规则：指定要注入到哪个核心 Prompt，以什么方式注入
    injection_rules = [
        InjectionRule(
            target_prompt="planner_prompt",  # 目标 Prompt 名称
            injection_type=InjectionType.APPEND,  # 注入方式：APPEND(追加) 或 PREPEND(前置)
            priority=50  # 优先级：0-100，数字越大优先级越高
        )
    ]

    async def execute(self) -> str:
        """
        生成要注入的 Prompt 内容

        可以访问 self.params 来获取上下文信息：
        - self.params.user_id: 用户ID
        - self.params.user_name: 用户名
        - self.params.bot_name: 机器人名称
        - self.params.recent_messages: 最近的消息列表
        - self.params.chat_type: 聊天类型（私聊/群聊）
        - 等等...

        Returns:
            要注入的文本内容
        """
        try:
            logger.info(f"生成 Prompt: {{self.prompt_name}}")

            # TODO: 根据 self.params 构建要注入的内容
            # 示例：根据用户信息生成个性化提示词
            user_name = self.params.user_name or "用户"

            prompt_content = f"""
# 特殊指令

你正在与 {{user_name}} 对话。

## 行为规则
- 保持友好和专业的态度
- 准确理解用户意图
- 提供有价值的回答

## 额外能力
- 你可以执行特定的操作
- 你有访问某些数据的权限
"""

            logger.debug(f"生成的内容: {{prompt_content[:100]}}...")
            return prompt_content.strip()

        except Exception as e:
            logger.error(f"生成 Prompt 失败: {{e}}")
            return ""
'''


def get_prompt_template() -> str:
    """获取 Prompt 组件模板"""
    return PROMPT_TEMPLATE

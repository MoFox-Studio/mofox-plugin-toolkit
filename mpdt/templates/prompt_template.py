"""
Prompt 组件模板
"""

PROMPT_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any, Optional

from src.common.logger import get_logger
from src.plugin_system import BasePrompt

logger = get_logger(__name__)


class {class_name}(BasePrompt):
    """
    {description}

    Prompt 组件用于管理和生成 AI 提示词，包括:
    - 系统提示词
    - 用户提示词
    - 上下文注入
    - 动态提示词生成
    """

    def __init__(self):
        super().__init__()
        self.name = "{prompt_name}"
        self.description = "{description}"

        # 基础提示词模板
        self.template = """
{{system_instruction}}

{{context}}

{{user_input}}
"""

    def build(self, **kwargs: Any) -> str:
        """
        构建完整的提示词

        Args:
            **kwargs: 构建参数

        Returns:
            完整的提示词文本
        """
        try:
            logger.info(f"构建 Prompt: {{self.name}}")

            # TODO: 从 kwargs 中提取所需参数
            context = kwargs.get("context", "")
            user_input = kwargs.get("user_input", "")

            # 构建系统指令
            system_instruction = self.get_system_instruction()

            # 格式化提示词
            prompt = self.template.format(
                system_instruction=system_instruction,
                context=context,
                user_input=user_input
            )

            logger.debug(f"生成的 Prompt: {{prompt[:100]}}...")
            return prompt

        except Exception as e:
            logger.error(f"构建 Prompt 失败: {{e}}")
            raise

    def get_system_instruction(self) -> str:
        """
        获取系统指令

        Returns:
            系统指令文本
        """
        # TODO: 定义系统指令
        return """
你是一个智能助手，具有以下特点：
- 友好、专业
- 准确理解用户意图
- 提供有价值的回答
"""

    def add_context(self, context: str, **kwargs: Any) -> str:
        """
        添加上下文信息

        Args:
            context: 上下文内容
            **kwargs: 其他参数

        Returns:
            格式化后的上下文
        """
        # TODO: 格式化上下文
        return f"### 上下文\\n{{context}}\\n"

    def add_examples(self, examples: list[dict]) -> str:
        """
        添加示例

        Args:
            examples: 示例列表，每个示例是一个字典 {{"input": "...", "output": "..."}}

        Returns:
            格式化后的示例文本
        """
        if not examples:
            return ""

        examples_text = "### 示例\\n"
        for i, example in enumerate(examples, 1):
            examples_text += f"示例 {{i}}:\\n"
            examples_text += f"输入: {{example.get('input', '')}}\\n"
            examples_text += f"输出: {{example.get('output', '')}}\\n\\n"

        return examples_text

    def validate(self, prompt: str) -> bool:
        """
        验证生成的提示词

        Args:
            prompt: 提示词文本

        Returns:
            是否有效
        """
        # TODO: 实现验证逻辑
        # 检查长度、格式等
        if not prompt or len(prompt.strip()) == 0:
            return False

        # 检查是否超过最大长度
        max_length = 8000  # 根据模型限制设置
        if len(prompt) > max_length:
            logger.warning(f"Prompt 长度 ({{len(prompt)}}) 超过限制 ({{max_length}})")
            return False

        return True

    def optimize(self, prompt: str) -> str:
        """
        优化提示词

        Args:
            prompt: 原始提示词

        Returns:
            优化后的提示词
        """
        # TODO: 实现优化逻辑
        # 例如: 压缩空白、移除冗余等
        optimized = prompt.strip()
        # 压缩多余的换行
        while "\\n\\n\\n" in optimized:
            optimized = optimized.replace("\\n\\n\\n", "\\n\\n")

        return optimized
'''


def get_prompt_template() -> str:
    """获取 Prompt 组件模板"""
    return PROMPT_TEMPLATE

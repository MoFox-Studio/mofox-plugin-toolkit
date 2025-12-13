"""
Tool 组件模板
"""

TOOL_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.common.logger import get_logger
from src.plugin_system import BaseTool

logger = get_logger(__name__)


class {class_name}(BaseTool):
    """
    {description}

    这个 Tool 提供特定功能，可以被 AI 模型调用。
    """

    def __init__(self):
        super().__init__()
        self.name = "{tool_name}"
        self.description = "{description}"

        # Tool Schema 定义 (OpenAI Function Calling 格式)
        self.schema = {{
            "type": "function",
            "function": {{
                "name": self.name,
                "description": self.description,
                "parameters": {{
                    "type": "object",
                    "properties": {{
                        # TODO: 定义参数 schema
                        "param1": {{
                            "type": "string",
                            "description": "参数1的说明"
                        }},
                        "param2": {{
                            "type": "number",
                            "description": "参数2的说明（可选）"
                        }}
                    }},
                    "required": ["param1"]  # 必需参数列表
                }}
            }}
        }}

    {async_keyword}def run(self, **kwargs: Any) -> Any:
        """
        运行 Tool

        Args:
            **kwargs: Tool 参数，对应 schema 中定义的参数

        Returns:
            执行结果（通常是字典格式）
        """
        try:
            logger.info(f"运行 Tool: {{self.name}}")
            logger.debug(f"参数: {{kwargs}}")

            # TODO: 验证参数
            self._validate_params(**kwargs)

            # TODO: 实现 Tool 逻辑
            # 示例实现
            param1 = kwargs.get("param1")
            result = {{
                "status": "success",
                "data": f"处理了参数: {{param1}}",
                "message": "执行成功"
            }}

            logger.info("Tool 运行完成")
            return result

        except Exception as e:
            logger.error(f"Tool 运行失败: {{e}}")
            return {{
                "status": "error",
                "message": str(e)
            }}

    def _validate_params(self, **kwargs: Any) -> None:
        """
        验证参数

        Args:
            **kwargs: 参数

        Raises:
            ValueError: 参数无效时
        """
        # TODO: 实现参数验证逻辑
        required_params = ["param1"]
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"缺少必需参数: {{param}}")
'''


def get_tool_template() -> str:
    """获取 Tool 组件模板"""
    return TOOL_TEMPLATE

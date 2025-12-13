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
from src.plugin_system import BaseTool, ToolParamType

logger = get_logger(__name__)


class {class_name}(BaseTool):
    """
    {description}

    Tool 组件可以被 LLM 调用来执行特定功能。
    """

    # Tool 元数据
    name: str = "{tool_name}"
    description: str = "{description}"
    available_for_llm: bool = True  # 是否可供 LLM 使用

    # 定义工具参数
    # 格式: [("参数名", 参数类型, "参数描述", 是否必填, 枚举值列表)]
    parameters = [
        ("query", ToolParamType.STRING, "查询内容", True, None),
        ("limit", ToolParamType.INTEGER, "返回结果数量限制", False, None),
        ("format", ToolParamType.STRING, "输出格式", False, ["json", "text", "markdown"]),
    ]

    # 缓存配置（可选）
    enable_cache: bool = False  # 是否启用缓存
    cache_ttl: int = 3600  # 缓存过期时间（秒）

    async def execute(self, function_args: dict[str, Any]) -> dict[str, Any]:
        """
        执行工具功能（供 LLM 调用）

        Args:
            function_args: LLM 传入的参数，格式符合 parameters 定义

        Returns:
            执行结果字典
        """
        try:
            logger.info(f"执行 Tool: {{self.name}}")
            logger.debug(f"参数: {{function_args}}")

            # 获取参数
            query = function_args.get("query")
            limit = function_args.get("limit", 10)
            output_format = function_args.get("format", "text")

            # TODO: 实现工具的核心逻辑
            result_data = self._process_query(query, limit)

            # 格式化返回结果
            return {{
                "status": "success",
                "data": result_data,
                "message": "执行成功"
            }}

        except Exception as e:
            logger.error(f"Tool 执行失败: {{e}}")
            return {{
                "status": "error",
                "message": str(e)
            }}

    def _process_query(self, query: str, limit: int) -> Any:
        """
        处理查询的核心逻辑

        Args:
            query: 查询内容
            limit: 结果数量限制

        Returns:
            处理结果
        """
        # TODO: 实现具体的处理逻辑
        return {{"query": query, "count": limit}}
'''


def get_tool_template() -> str:
    """获取 Tool 组件模板"""
    return TOOL_TEMPLATE

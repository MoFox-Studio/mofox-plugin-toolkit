"""
Tool 组件模板（Neo-MoFox 架构）
"""

TOOL_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Annotated, Any

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseTool

logger = get_logger(__name__)


class {class_name}(BaseTool):
    """
    {description}

    Tool 提供特定的功能接口供 LLM 调用。
    与 Action 不同，Tool 侧重于"查询"功能而非"响应"动作。
    """

    tool_name = "{component_name}"
    tool_description = "{description}"

    async def execute(
        self,
        query: Annotated[str, "查询内容"],
        limit: Annotated[int, "返回结果数量限制"] = 10,
    ) -> tuple[bool, str | dict]:
        """
        执行工具的主要逻辑

        必须编写参数文档来告诉 LLM 每个参数的作用。
        使用 Annotated 类型提示来提供参数描述。

        Args:
            query: 查询内容
            limit: 返回结果数量限制，默认10

        Returns:
            tuple[bool, str | dict]: (是否成功, 返回结果)

        Examples:
            >>> success, result = await tool.execute("搜索内容", limit=5)
            >>> if success:
            ...     print(result)
        """
        try:
            logger.info(f"执行 Tool: {{self.tool_name}}")
            logger.debug(f"查询: {{query}}, 限制: {{limit}}")

            # TODO: 实现工具的核心逻辑
            result_data = await self._process_query(query, limit)

            # 返回结果（可以是字符串或字典）
            return True, {{
                "status": "success",
                "data": result_data,
                "message": "执行成功"
            }}

        except Exception as e:
            logger.error(f"Tool 执行失败: {{e}}")
            return False, f"执行失败: {{e}}"

    async def _process_query(self, query: str, limit: int) -> Any:
        """
        处理查询的核心逻辑

        Args:
            query: 查询内容
            limit: 结果数量限制

        Returns:
            Any: 查询结果
        """
        # TODO: 实现查询逻辑
        return {{"query": query, "limit": limit, "results": []}}
'''


def get_tool_template() -> str:
    """获取 Tool 组件模板"""
    return TOOL_TEMPLATE

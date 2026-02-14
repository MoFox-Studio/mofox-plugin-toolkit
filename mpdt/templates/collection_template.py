"""
Collection 组件模板（Neo-MoFox 架构）
"""

COLLECTION_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.core.components.base import BaseCollection
from src.core.components.types import ChatType
from src.kernel.logger import get_logger

logger = get_logger(__name__)


class {class_name}(BaseCollection):
    """
    {description}

    Collection 是 LLMUsable 的集合体，可以包含多个 Action/Tool，甚至嵌套的 Collection。
    当 LLM 调用 Collection 时，会解包其内部组件，使它们可用。

    使用场景：
    - 组织相关的 Action/Tool 组件
    - 动态激活一组功能
    - 分组管理复杂功能
    - 嵌套的功能集合
    """

    collection_name = "{component_name}"
    collection_description = "{description}"

    # 关联平台（可选，默认支持所有平台）
    associated_platforms: list[str] = []

    # 支持的 Chatter 列表（可选，空列表表示所有 Chatter 都可用）
    chatter_allow: list[str] = []

    # 支持的聊天类型（私聊/群聊/所有）
    chat_type: ChatType = ChatType.ALL

    # 是否覆盖内部组件的 go_activate 结果
    # True: 当 Collection 被调用时，强制激活所有内部组件
    # False: 内部组件仍需通过自己的 go_activate 判断
    cover_go_activate: bool = False

    async def get_contents(self) -> list[str]:
        """
        获取 Collection 内部包含的所有 LLMUsable 组件。

        返回组件签名列表，格式："插件名:组件类型:组件名"

        Returns:
            list[str]: 包含的所有 LLMUsable 组件签名列表

        Examples:
            >>> async def get_contents(self) -> list[str]:
            ...     return [
            ...         "my_plugin:action:send_message",
            ...         "my_plugin:tool:get_weather",
            ...         "my_plugin:collection:nested_collection",
            ...     ]
        """
        # TODO: 返回 Collection 包含的组件签名列表

        # 示例：返回同一插件内的组件
        plugin_name = self.plugin.plugin_name

        return [
            # f"{{plugin_name}}:action:some_action",
            # f"{{plugin_name}}:tool:some_tool",
            # 也可以包含其他插件的组件
            # "other_plugin:action:other_action",
        ]

    async def go_activate(self) -> bool:
        """
        判断是否激活此 Collection（可选实现）。

        如果不实现此方法，Collection 默认总是可用。
        实现此方法可以根据条件动态决定是否激活整个集合。

        Returns:
            bool: True 表示激活，False 表示不激活

        Examples:
            >>> async def go_activate(self) -> bool:
            ...     # 根据配置决定是否激活
            ...     config = self.plugin.get_config()
            ...     return config.get("enable_collection", True)
        """
        # 默认总是激活
        return True
'''


def get_collection_template() -> str:
    """获取 Collection 组件模板"""
    return COLLECTION_TEMPLATE

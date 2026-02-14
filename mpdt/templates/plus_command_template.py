"""
PlusCommand 组件模板（Neo-MoFox 架构）
"""

PLUS_COMMAND_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseCommand
from src.core.components.decorators import cmd_route

logger = get_logger(__name__)


class {class_name}(BaseCommand):
    """
    {description}

    Command 是增强型命令，支持：
    - 复杂的参数解析
    - 子命令系统（Trie 树路由）
    - 权限检查
    - 类型提示参数解析
    """

    command_name = "{component_name}"
    command_description = "{description}"
    command_prefix = "/"  # 命令前缀

    # 示例：处理 "/{component_name} set <value>" 命令
    @cmd_route("set")
    async def handle_set(self, value: str) -> tuple[bool, str]:
        """
        设置值

        Args:
            value: 要设置的值

        Returns:
            (success: bool, message: str)
        """
        try:
            logger.info(f"设置值: {{value}}")
            # TODO: 实现设置逻辑
            return True, f"已设置为: {{value}}"
        except Exception as e:
            logger.error(f"设置失败: {{e}}")
            return False, f"设置失败: {{e}}"

    # 示例：处理 "/{component_name} get" 命令
    @cmd_route("get")
    async def handle_get(self) -> tuple[bool, str]:
        """
        获取值

        Returns:
            (success: bool, message: str)
        """
        try:
            logger.info("获取值")
            # TODO: 实现获取逻辑
            return True, "当前值: [value]"
        except Exception as e:
            logger.error(f"获取失败: {{e}}")
            return False, f"获取失败: {{e}}"

    # 示例：处理 "/{component_name} list" 命令
    @cmd_route("list")
    async def handle_list(self) -> tuple[bool, str]:
        """
        列表所有项

        Returns:
            (success: bool, message: str)
        """
        try:
            logger.info("列表项")
            # TODO: 实现列表逻辑
            return True, "列表: [items]"
        except Exception as e:
            logger.error(f"列表失败: {{e}}")
            return False, f"列表失败: {{e}}"
'''


def get_plus_command_template() -> str:
    """获取 PlusCommand 组件模板"""
    return PLUS_COMMAND_TEMPLATE

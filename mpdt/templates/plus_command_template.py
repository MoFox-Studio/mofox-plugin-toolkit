"""
PlusCommand 组件模板
"""

PLUS_COMMAND_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.common.logger import get_logger
from src.plugin_system import BasePlusCommand

logger = get_logger(__name__)


class {class_name}(BasePlusCommand):
    """
    {description}

    PlusCommand 是增强型命令，支持：
    - 复杂的参数解析
    - 子命令系统
    - 权限检查
    - 更丰富的交互方式
    """

    # PlusCommand 元数据
    command_name: str = "{command_name}"
    command_description: str = "{description}"
    command_aliases: list[str] = []  # 命令别名
    usage: str = "{command_name} [子命令] [选项]"

    async def execute(self, **kwargs) -> tuple[bool, str]:
        """
        执行命令

        可以访问的参数：
        - self.stream_context: 聊天流上下文
        - self.raw_text: 原始命令文本
        - self.command_args: 解析后的命令参数

        Returns:
            (是否成功, 结果消息)
        """
        try:
            logger.info(f"执行 PlusCommand: {{self.command_name}}")

            # 获取命令参数
            args = self.command_args if hasattr(self, "command_args") else []

            if not args:
                return True, self._help_message()

            subcommand = args[0]
            subcommand_args = args[1:] if len(args) > 1 else []

            # 执行子命令
            if subcommand == "list":
                return await self._list_command(subcommand_args)
            elif subcommand == "add":
                return await self._add_command(subcommand_args)
            elif subcommand == "remove":
                return await self._remove_command(subcommand_args)
            elif subcommand == "help":
                return True, self._help_message()
            else:
                return False, f"未知子命令: {{subcommand}}\\n{{self._help_message()}}"

        except Exception as e:
            logger.error(f"命令执行失败: {{e}}")
            return False, f"执行失败: {{e}}"

    async def _list_command(self, args: list[str]) -> tuple[bool, str]:
        """
        列表子命令

        Args:
            args: 参数列表

        Returns:
            (是否成功, 结果消息)
        """
        # TODO: 实现列表功能
        return True, "列表功能"

    async def _add_command(self, args: list[str]) -> tuple[bool, str]:
        """
        添加子命令

        Args:
            args: 参数列表

        Returns:
            (是否成功, 结果消息)
        """
        if not args:
            return False, f"用法: {{self.command_name}} add <项目>"

        item = " ".join(args)
        # TODO: 实现添加功能
        return True, f"已添加: {{item}}"

    async def _remove_command(self, args: list[str]) -> tuple[bool, str]:
        """
        删除子命令

        Args:
            args: 参数列表

        Returns:
            (是否成功, 结果消息)
        """
        if not args:
            return False, f"用法: {{self.command_name}} remove <项目>"

        item = " ".join(args)
        # TODO: 实现删除功能
        return True, f"已删除: {{item}}"

    def _help_message(self) -> str:
        """
        生成帮助信息

        Returns:
            帮助信息文本
        """
        return f"""
命令: {{self.command_name}}
描述: {{self.command_description}}
用法: {{self.usage}}

子命令:
    list       列出所有项目
    add        添加新项目
    remove     删除项目
    help       显示此帮助信息

示例:
    {{self.command_name}} list
    {{self.command_name}} add item1
    {{self.command_name}} remove item1
"""
'''


def get_plus_command_template() -> str:
    """获取 PlusCommand 组件模板"""
    return PLUS_COMMAND_TEMPLATE

"""
PlusCommand 组件模板
"""

PLUS_COMMAND_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any, Optional

from src.common.logger import get_logger
from src.plugin_system import BasePlusCommand

logger = get_logger(__name__)


class {class_name}(BasePlusCommand):
    """
    {description}

    PlusCommand 是增强型命令，支持:
    - 复杂的参数解析
    - 子命令系统
    - 权限检查
    - 更丰富的交互方式
    """

    def __init__(self):
        super().__init__()
        self.command_name = "{command_name}"
        self.aliases = []  # 命令别名
        self.description = "{description}"
        self.usage = "{command_name} [子命令] [选项]"

        # 子命令定义
        self.subcommands = {{
            "list": self.list_command,
            "add": self.add_command,
            "remove": self.remove_command,
            "help": self.help_command,
        }}

        # 权限要求
        self.required_permission = None  # 例如: "admin", "user" 等

    {async_keyword}def execute(self, context: Any, args: list[str], **kwargs: Any) -> Any:
        """
        执行命令

        Args:
            context: 执行上下文
            args: 命令参数列表
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        try:
            logger.info(f"执行 PlusCommand: {{self.command_name}} {{args}}")

            # 检查权限
            if not self.check_permission(context):
                return "权限不足"

            # 解析参数
            if not args:
                return self.help_command(context, [])

            subcommand = args[0]
            subcommand_args = args[1:] if len(args) > 1 else []

            # 执行子命令
            if subcommand in self.subcommands:
                handler = self.subcommands[subcommand]
                result = {await_keyword}handler(context, subcommand_args)
                return result
            else:
                return f"未知子命令: {{subcommand}}\\n使用 '{{self.command_name}} help' 查看帮助"

        except Exception as e:
            logger.error(f"命令执行失败: {{e}}")
            return f"执行失败: {{e}}"

    {async_keyword}def list_command(self, context: Any, args: list[str]) -> str:
        """
        列表子命令

        Args:
            context: 执行上下文
            args: 参数列表

        Returns:
            执行结果
        """
        # TODO: 实现列表功能
        return "列表功能"

    {async_keyword}def add_command(self, context: Any, args: list[str]) -> str:
        """
        添加子命令

        Args:
            context: 执行上下文
            args: 参数列表

        Returns:
            执行结果
        """
        if not args:
            return "用法: {{self.command_name}} add <项目>"

        item = " ".join(args)
        # TODO: 实现添加功能
        return f"已添加: {{item}}"

    {async_keyword}def remove_command(self, context: Any, args: list[str]) -> str:
        """
        删除子命令

        Args:
            context: 执行上下文
            args: 参数列表

        Returns:
            执行结果
        """
        if not args:
            return "用法: {{self.command_name}} remove <项目>"

        item = " ".join(args)
        # TODO: 实现删除功能
        return f"已删除: {{item}}"

    {async_keyword}def help_command(self, context: Any, args: list[str]) -> str:
        """
        帮助子命令

        Args:
            context: 执行上下文
            args: 参数列表

        Returns:
            帮助信息
        """
        return f"""
命令: {{self.command_name}}
描述: {{self.description}}
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

    def check_permission(self, context: Any) -> bool:
        """
        检查权限

        Args:
            context: 执行上下文

        Returns:
            是否有权限
        """
        if self.required_permission is None:
            return True

        # TODO: 实现权限检查逻辑
        # 从 context 中获取用户信息并验证权限
        return True

    def parse_options(self, args: list[str]) -> tuple[dict[str, Any], list[str]]:
        """
        解析命令选项

        Args:
            args: 参数列表

        Returns:
            (选项字典, 剩余参数)
        """
        options = {{}}
        remaining_args = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("--"):
                # 长选项
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    options[key] = value
                else:
                    key = arg[2:]
                    if i + 1 < len(args) and not args[i + 1].startswith("-"):
                        options[key] = args[i + 1]
                        i += 1
                    else:
                        options[key] = True
            elif arg.startswith("-"):
                # 短选项
                key = arg[1:]
                if i + 1 < len(args) and not args[i + 1].startswith("-"):
                    options[key] = args[i + 1]
                    i += 1
                else:
                    options[key] = True
            else:
                remaining_args.append(arg)
            i += 1

        return options, remaining_args
'''


def get_plus_command_template() -> str:
    """获取 PlusCommand 组件模板"""
    return PLUS_COMMAND_TEMPLATE

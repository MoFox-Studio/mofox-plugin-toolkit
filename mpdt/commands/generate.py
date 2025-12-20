"""
代码生成命令实现
"""

from pathlib import Path
from typing import Any

import libcst as cst
import questionary

from mpdt.templates import prepare_component_context
from mpdt.utils.plugin_parser import extract_plugin_name
from mpdt.utils.color_printer import (
    console,
    print_error,
    print_step,
    print_success,
    print_warning,
)
from mpdt.utils.file_ops import (
    ensure_dir,
    get_git_user_info,
    safe_write_file,
    to_snake_case,
    validate_component_name,
)


def generate_component(
    component_type: str | None = None,
    component_name: str | None = None,
    description: str | None = None,
    output_dir: str | None = None,
    force: bool = False,
    verbose: bool = False,
) -> None:
    """
    生成插件组件(始终生成异步方法)

    Args:
        component_type: 组件类型 (None 表示交互式询问)
        component_name: 组件名称 (None 表示交互式询问)
        description: 组件描述
        output_dir: 输出目录
        force: 是否覆盖
        verbose: 详细输出
    """
    # 交互式获取组件信息
    if not component_type or not component_name:
        component_info = _interactive_generate()
        component_type = component_info["component_type"]
        component_name = component_info["component_name"]
        description = component_info.get("description") or description
        force = component_info.get("force", force)

    # 此时 component_type 和 component_name 必定不为 None
    assert component_type is not None
    assert component_name is not None

    print_step(f"生成 {component_type.upper()} 组件: {component_name}")

    # 验证组件名称
    if not validate_component_name(component_name):
        print_error("组件名称无效！必须使用小写字母、数字和下划线，以字母开头")
        return

    # 确定工作目录
    if output_dir:
        work_dir = Path(output_dir)
    else:
        work_dir = Path.cwd()

    # 检查是否在插件目录中
    plugin_name = _detect_plugin_name(work_dir)
    if not plugin_name:
        print_error("未检测到插件目录！请在插件根目录下运行此命令")
        print_warning("提示: 插件目录应包含 plugin.py 文件")
        return

    if verbose:
        console.print(f"[dim]检测到插件: {plugin_name}[/dim]")

    # 确保组件名称为 snake_case
    component_name = to_snake_case(component_name)

    # 标准化组件类型（命令行参数 plus-command -> plus_command）
    normalized_type = component_type.replace("-", "_")

    # 准备上下文
    git_info = get_git_user_info()
    context = prepare_component_context(
        component_type=normalized_type,
        component_name=component_name,
        plugin_name=plugin_name,
        author=git_info.get("name", ""),
        description=description or f"{component_name} 组件",
        is_async=True,  # 始终生成异步方法
    )

    # 生成组件文件
    component_file = _generate_component_file(
        work_dir=work_dir,
        component_type=normalized_type,  # 使用标准化的类型
        component_name=component_name,
        context=context,
        force=force,
        verbose=verbose,
    )

    if not component_file:
        return

    # 更新插件注册
    if not _update_plugin_registration(
        work_dir=work_dir,
        component_type=normalized_type,  # 使用标准化的类型
        component_name=component_name,
        context=context,
        verbose=verbose,
    ):
        print_warning("⚠️  自动更新插件注册失败，请手动添加到 plugin.py")

    # 打印成功信息
    print_success(f"✨ {context['class_name']} 生成成功！")
    console.print("\n[bold cyan]生成的文件:[/bold cyan]")
    console.print(f"  📄 {component_file.relative_to(work_dir)}")

    console.print("\n[bold cyan]下一步:[/bold cyan]")
    console.print(f"  1. 编辑 {component_file.name} 实现具体逻辑")
    console.print("  2. 运行 mpdt check 检查代码")
    console.print("  3. 运行 mpdt test 测试功能")


def _interactive_generate() -> dict[str, Any]:
    """交互式生成组件"""
    console.print("\n[bold cyan]🔧 组件生成向导[/bold cyan]\n")

    answers = questionary.form(
        component_type=questionary.select(
            "选择组件类型:",
            choices=[
                questionary.Choice("Action 组件", value="action"),
                questionary.Choice("Tool 组件", value="tool"),
                questionary.Choice("Event 事件", value="event"),
                questionary.Choice("Adapter 适配器", value="adapter"),
                questionary.Choice("Prompt 提示词", value="prompt"),
                questionary.Choice("Plus Command 命令", value="plus-command"),
                questionary.Choice("Chatter 聊天组件", value="chatter"),
                questionary.Choice("Router 路由组件", value="router"),
            ],
        ),
        component_name=questionary.text(
            "组件名称 (使用下划线命名):",
            validate=lambda x: validate_component_name(x) or "组件名称格式无效",
        ),
        description=questionary.text(
            "组件描述 (可选):",
            default="",
        ),
        force=questionary.confirm(
            "如果文件存在，是否覆盖?",
            default=False,
        ),
    ).ask()

    return answers


def _detect_plugin_name(work_dir: Path) -> str | None:
    """
    检测插件名称

    Args:
        work_dir: 工作目录

    Returns:
        插件名称,未检测到则返回 None
    """
    # 检查 plugin.py 文件
    plugin_file = work_dir / "plugin.py"
    if not plugin_file.exists():
        # 尝试在父目录查找
        plugin_file = work_dir.parent / "plugin.py"
        if not plugin_file.exists():
            return None
        work_dir = work_dir.parent

    # 从目录名推断插件名
    return work_dir.name


def _generate_component_file(
    work_dir: Path,
    component_type: str,
    component_name: str,
    context: dict,
    force: bool,
    verbose: bool,
) -> Path | None:
    """
    生成组件文件

    Args:
        work_dir: 工作目录
        component_type: 组件类型
        component_name: 组件名称
        context: 模板上下文
        force: 是否覆盖
        verbose: 详细输出

    Returns:
        生成的文件路径,失败返回 None
    """
    # 确定组件目录
    component_dir = work_dir / "components" / f"{component_type}s"
    ensure_dir(component_dir)

    # 确保 __init__.py 存在
    init_file = component_dir / "__init__.py"
    if not init_file.exists():
        safe_write_file(init_file, f'"""\n{component_type.title()}s 组件\n"""\n')

    # 生成组件文件
    component_file = component_dir / f"{component_name}.py"


    # 组件类型到模板 key 的映射（此时 component_type 已经是标准化的下划线格式）
    type_map = {
        "action": "action",
        "tool": "tool",
        "event": "event",
        "adapter": "adapter",
        "prompt": "prompt",
        "plus_command": "plus_command",
        "chatter":"chatter",
        "router":"router"
    }
    template_key = type_map.get(component_type)
    if not template_key:
        print_error(f"不支持的组件类型: {component_type}")
        return None

    from mpdt.templates import get_component_template
    template = get_component_template(template_key)
    content = template.format(**context)

    try:
        safe_write_file(component_file, content, force=force)
        if verbose:
            console.print(f"[dim]✓ 生成文件: {component_file}[/dim]")
        return component_file
    except FileExistsError:
        print_error(f"文件已存在: {component_file}")
        print_warning("使用 --force 选项覆盖已存在的文件")
        return None
    except Exception as e:
        print_error(f"生成文件失败: {e}")
        return None


def _update_plugin_registration(
    work_dir: Path,
    component_type: str,
    component_name: str,
    context: dict,
    verbose: bool,
) -> bool:
    """
    更新插件注册代码 (使用 AST 解析)

    Args:
        work_dir: 工作目录
        component_type: 组件类型
        component_name: 组件名称
        context: 模板上下文
        verbose: 详细输出

    Returns:
        是否更新成功
    """
    plugin_file = work_dir / "plugin.py"
    if not plugin_file.exists():
        return False

    try:
        # 使用 plugin_parser 验证插件名称
        parsed_plugin_name = extract_plugin_name(work_dir)
        if not parsed_plugin_name:
            if verbose:
                console.print("[dim]⚠  无法解析插件名称[/dim]")
            return False

        # 读取源代码
        source_code = plugin_file.read_text(encoding="utf-8")
        source_tree = cst.parse_module(source_code)

        # 创建转换器
        transformer = PluginRegistrationTransformer(
            plugin_name=parsed_plugin_name,
            component_type=component_type,
            component_name=component_name,
            class_name=context["class_name"],
        )

        # 应用转换
        modified_tree = source_tree.visit(transformer)

        # 写回文件
        plugin_file.write_text(modified_tree.code, encoding="utf-8")

        if verbose:
            console.print(f"[dim]✓ 更新插件注册: {plugin_file}[/dim]")

        return True

    except Exception as e:
        if verbose:
            console.print(f"[dim]⚠  自动更新插件注册失败: {e}[/dim]")
        return False


class PluginRegistrationTransformer(cst.CSTTransformer):
    """用于添加组件导入和注册的 CST 转换器"""

    def __init__(
        self,
        plugin_name: str,
        component_type: str,
        component_name: str,
        class_name: str,
    ):
        self.plugin_name = plugin_name
        self.component_type = component_type
        self.component_name = component_name
        self.class_name = class_name
        self.import_added = False
        self.registration_added = False

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """在模块级别添加导入语句"""
        if self.import_added:
            return updated_node

        # 构建导入语句
        import_statement = cst.parse_statement(
            f"from {self.plugin_name}.components.{self.component_type}s.{self.component_name} import {self.class_name}"
        )

        # 检查是否已存在相同的导入
        for stmt in updated_node.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, cst.ImportFrom) and s.module:
                        module_str = cst.Module([]).code_for_node(s.module)
                        target_module = f"{self.plugin_name}.components.{self.component_type}s.{self.component_name}"
                        if module_str == target_module:
                            self.import_added = True
                            return updated_node

        # 找到最后一个导入语句的位置
        last_import_idx = -1
        for idx, stmt in enumerate(updated_node.body):
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, (cst.Import, cst.ImportFrom)):
                        last_import_idx = idx

        # 在最后一个导入后添加新导入
        if last_import_idx >= 0:
            new_body = list(updated_node.body)
            new_body.insert(last_import_idx + 1, import_statement)
            self.import_added = True
            return updated_node.with_changes(body=new_body)

        return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """在 get_plugin_components 函数中添加注册代码"""
        if updated_node.name.value != "get_plugin_components":
            return updated_node

        if self.registration_added:
            return updated_node

        # 根据组件类型生成对应的 get_xxx_info() 方法调用
        info_method_map = {
            "action": "get_action_info",
            "tool": "get_tool_info",
            "event": "get_event_handler_info",
            "adapter": "get_adapter_info",
            "prompt": "get_prompt_info",
            "plus_command": "get_command_info",
            "chatter": "get_chatter_info",
            "router": "get_router_info",
        }
        info_method = info_method_map.get(self.component_type, "get_component_info")

        # 构建注册代码
        registration_code = f"""# 注册 {self.class_name}
        components.append(({self.class_name}.{info_method}(), {self.class_name}))"""

        # 检查是否已存在注册代码
        function_code = cst.Module([]).code_for_node(updated_node)
        if self.class_name in function_code and info_method in function_code:
            self.registration_added = True
            return updated_node

        # 找到 return 语句并在其前面插入注册代码
        new_body = []
        for stmt in updated_node.body.body:
            # 如果是 return 语句，在前面插入注册代码
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, cst.Return):
                        # 插入注册代码
                        for line in registration_code.split("\n"):
                            if line.strip():
                                new_body.append(cst.parse_statement(line))
                        self.registration_added = True

            new_body.append(stmt)

        if self.registration_added:
            new_function_body = updated_node.body.with_changes(body=new_body)
            return updated_node.with_changes(body=new_function_body)

        return updated_node

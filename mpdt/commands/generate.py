"""
代码生成命令实现
"""

from pathlib import Path
from typing import Any

import libcst as cst
import questionary

from mpdt.templates import prepare_component_context
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

# =============================================================================
# 常量定义
# =============================================================================

# 组件类型到目录名的映射(统一管理)
COMPONENT_DIR_MAP = {
    "action": "actions",
    "tool": "tools",
    "plus_command": "plus_command",
    "event": "events",
    "adapter": "adapters",
    "chatter": "chatters",
    "router": "routers",
    "service": "services",
    "config": "configs",
}

# 组件类型到模板 key 的映射
COMPONENT_TYPE_MAP = {
    "action": "action",
    "tool": "tool",
    "event": "event",
    "adapter": "adapter",
    "plus_command": "plus_command",
    "chatter": "chatter",
    "router": "router",
    "service": "service",
    "config": "config",
}


# =============================================================================
# 主入口函数
# =============================================================================


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
    # 确定工作目录
    if output_dir:
        work_dir = Path(output_dir)
    else:
        work_dir = Path.cwd()

    # 先检查是否在插件目录中，避免用户填完信息后才报错
    plugin_name = _detect_plugin_name(work_dir)
    if not plugin_name:
        print_error("未检测到插件目录！请在插件根目录下运行此命令")
        print_warning("提示: 插件目录应包含 plugin.py 文件")
        return

    if verbose:
        console.print(f"[dim]检测到插件: {plugin_name}[/dim]")

    # 交互式获取组件信息
    use_components_folder = True  # 默认使用 components 文件夹
    if not component_type or not component_name:
        component_info = _interactive_generate()
        component_type = component_info["component_type"]
        component_name = component_info["component_name"]
        description = component_info.get("description") or description
        use_components_folder = component_info.get("use_components_folder", True)
        force = component_info.get("force", force)

    # 此时 component_type 和 component_name 必定不为 None
    assert component_type is not None
    assert component_name is not None

    print_step(f"生成 {component_type.upper()} 组件: {component_name}")

    # 验证组件名称
    if not validate_component_name(component_name):
        print_error("组件名称无效！必须使用小写字母、数字和下划线，以字母开头")
        return

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
    )

    # 生成组件文件
    component_file = _generate_component_file(
        work_dir=work_dir,
        component_type=normalized_type,  # 使用标准化的类型
        component_name=component_name,
        context=context,
        force=force,
        verbose=verbose,
        use_components_folder=use_components_folder,
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
        use_components_folder=use_components_folder,
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


# =============================================================================
# 交互式界面
# =============================================================================


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
                questionary.Choice("Plus Command 命令", value="plus-command"),
                questionary.Choice("Chatter 聊天组件", value="chatter"),
                questionary.Choice("Router 路由组件", value="router"),
                questionary.Choice("Service 服务", value="service"),
                questionary.Choice("Config 配置", value="config"),
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
        use_components_folder=questionary.select(
            "组件文件存放位置:",
            choices=[
                questionary.Choice("components/ 文件夹 (推荐)", value=True),
                questionary.Choice("插件根目录", value=False),
            ],
        ),
        force=questionary.confirm(
            "如果文件存在，是否覆盖?",
            default=False,
        ),
    ).ask()

    return answers


# =============================================================================
# 插件检测
# =============================================================================


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


# =============================================================================
# 组件文件生成
# =============================================================================


def _generate_component_file(
    work_dir: Path,
    component_type: str,
    component_name: str,
    context: dict,
    force: bool,
    verbose: bool,
    use_components_folder: bool = True,
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
        use_components_folder: 是否使用 components 文件夹，False 则在根目录生成

    Returns:
        生成的文件路径,失败返回 None
    """
    # 确定组件目录
    if use_components_folder:
        dir_name = COMPONENT_DIR_MAP.get(component_type, f"{component_type}s")
        component_dir = work_dir / "components" / dir_name
        ensure_dir(component_dir)

        # 确保 __init__.py 存在
        init_file = component_dir / "__init__.py"
        if not init_file.exists():
            safe_write_file(init_file, f'"""\n{dir_name.title()} 组件\n"""\n')
    else:
        # 在插件根目录生成
        component_dir = work_dir

    # 生成组件文件
    component_file = component_dir / f"{component_name}.py"

    # 获取模板 key
    template_key = COMPONENT_TYPE_MAP.get(component_type)
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


# =============================================================================
# 插件注册更新
# =============================================================================


def _update_manifest_json(
    work_dir: Path,
    component_type: str,
    component_name: str,
    verbose: bool,
) -> bool:
    """
    更新 manifest.json 文件，添加新组件

    Args:
        work_dir: 工作目录
        component_type: 组件类型
        component_name: 组件名称
        verbose: 详细输出

    Returns:
        是否更新成功
    """
    import json

    manifest_file = work_dir / "manifest.json"
    if not manifest_file.exists():
        if verbose:
            console.print("[dim yellow]⚠ 未找到 manifest.json 文件[/dim yellow]")
        return False

    try:
        # 读取现有 manifest
        with open(manifest_file, encoding="utf-8") as f:
            manifest = json.load(f)

        # 检查组件是否已存在
        include_list = manifest.get("include", [])
        for item in include_list:
            if item.get("component_name") == component_name and item.get("component_type") == component_type:
                if verbose:
                    console.print(f"[dim]组件 {component_name} 已在 manifest.json 中[/dim]")
                return True

        # 添加新组件
        new_component = {"component_type": component_type, "component_name": component_name, "dependencies": []}
        include_list.append(new_component)
        manifest["include"] = include_list

        # 写回文件
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=4)

        if verbose:
            console.print("[dim]✓ 已更新 manifest.json[/dim]")
        return True

    except Exception as e:
        if verbose:
            console.print(f"[dim red]更新 manifest.json 失败: {e}[/dim red]")
        return False


def _update_plugin_py_components(
    work_dir: Path,
    component_type: str,
    component_name: str,
    context: dict,
    verbose: bool,
    use_components_folder: bool = True,
) -> bool:
    """
    更新 plugin.py 中的 get_components() 方法，添加组件导入和类引用

    Args:
        work_dir: 工作目录
        component_type: 组件类型
        component_name: 组件名称
        context: 模板上下文
        verbose: 详细输出
        use_components_folder: 是否使用 components 文件夹

    Returns:
        是否更新成功
    """
    plugin_file = work_dir / "plugin.py"
    if not plugin_file.exists():
        return False

    try:
        from mpdt.utils.plugin_parser import extract_plugin_name

        # 使用 plugin_parser 验证插件名称
        parsed_plugin_name = extract_plugin_name(work_dir)
        if not parsed_plugin_name:
            # 如果无法从类属性中解析，使用目录名作为后备方案
            parsed_plugin_name = work_dir.name

        # 使用 CodeParser 读取和解析源代码
        from mpdt.utils.code_parser import CodeParser

        parser = CodeParser.from_file(plugin_file)

        # 创建转换器
        transformer = ComponentImportTransformer(
            plugin_name=parsed_plugin_name,
            component_type=component_type,
            component_name=component_name,
            class_name=context["class_name"],
            use_components_folder=use_components_folder,
        )

        # 应用转换
        modified_tree = parser.module.visit(transformer)

        # 写回文件
        plugin_file.write_text(modified_tree.code, encoding="utf-8")

        if verbose:
            console.print("[dim]✓ 已更新 plugin.py[/dim]")

        return transformer.import_added or transformer.component_added

    except Exception as e:
        if verbose:
            console.print(f"[dim red]更新 plugin.py 失败: {e}[/dim red]")
        return False


def _update_plugin_registration(
    work_dir: Path,
    component_type: str,
    component_name: str,
    context: dict,
    verbose: bool,
    use_components_folder: bool = True,
) -> bool:
    """
    更新插件注册代码（Neo-MoFox 架构）

    更新两个文件：
    1. manifest.json - 添加组件声明
    2. plugin.py - 添加组件导入和 get_components() 返回列表

    Args:
        work_dir: 工作目录
        component_type: 组件类型
        component_name: 组件名称
        context: 模板上下文
        verbose: 详细输出
        use_components_folder: 是否使用 components 文件夹

    Returns:
        是否更新成功
    """
    # 更新 manifest.json
    manifest_updated = _update_manifest_json(work_dir, component_type, component_name, verbose)

    # 更新 plugin.py
    plugin_updated = _update_plugin_py_components(
        work_dir, component_type, component_name, context, verbose, use_components_folder
    )

    return manifest_updated or plugin_updated


# =============================================================================
# CST 代码转换器
# =============================================================================


class ComponentImportTransformer(cst.CSTTransformer):
    """用于添加组件导入和更新插件类的 CST 转换器（Neo-MoFox 架构）

    功能：
    1. 添加组件导入语句
    2. 对于 config 组件：更新 configs 类属性
    3. 对于其他组件：更新 get_components() 方法返回列表
    """

    def __init__(
        self,
        plugin_name: str,
        component_type: str,
        component_name: str,
        class_name: str,
        use_components_folder: bool = True,
    ):
        self.plugin_name = plugin_name
        self.component_type = component_type
        self.component_name = component_name
        self.class_name = class_name
        self.use_components_folder = use_components_folder
        self.import_added = False
        self.component_added = False
        self.is_config = component_type == "config"

    def leave_Module(  # noqa: N802
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """在模块级别添加导入语句"""
        if self.import_added:
            return updated_node

        # 根据存放位置构建导入语句
        if self.use_components_folder:
            dir_name = COMPONENT_DIR_MAP.get(self.component_type, f"{self.component_type}s")
            import_path = f"{self.plugin_name}.components.{dir_name}.{self.component_name}"
        else:
            import_path = f"{self.plugin_name}.{self.component_name}"

        import_statement = cst.parse_statement(f"from {import_path} import {self.class_name}")

        # 检查是否已存在相同的导入
        for stmt in updated_node.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, cst.ImportFrom) and s.module:
                        module_str = cst.Module([]).code_for_node(s.module)
                        if module_str == import_path:
                            self.import_added = True
                            return updated_node

        # 找到最后一个导入语句的位置
        last_import_idx = -1
        for idx, stmt in enumerate(updated_node.body):
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, cst.Import | cst.ImportFrom):
                        last_import_idx = idx

        # 在最后一个导入后添加新导入
        if last_import_idx >= 0:
            new_body = list(updated_node.body)
            new_body.insert(last_import_idx + 1, import_statement)
            self.import_added = True
            return updated_node.with_changes(body=new_body)

        return updated_node

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        """更新插件类的 configs 类属性（仅用于 config 组件）"""
        # 只有 config 组件才需要更新 configs 类属性
        if not self.is_config:
            return updated_node

        if self.component_added:
            return updated_node

        # 检查是否已存在 configs 属性
        new_body = []
        configs_found = False

        for stmt in updated_node.body.body:
            # 查找 configs 类属性定义
            if isinstance(stmt, cst.SimpleStatementLine):
                for assign in stmt.body:
                    if isinstance(assign, cst.AnnAssign) and isinstance(assign.target, cst.Name):
                        if assign.target.value == "configs":
                            configs_found = True
                            # 检查是否已包含当前配置类
                            if assign.value and isinstance(assign.value, cst.List):
                                existing_elements = list(assign.value.elements)
                                # 检查是否已存在
                                has_class = any(
                                    isinstance(elem.value, cst.Name) and elem.value.value == self.class_name
                                    for elem in existing_elements
                                )
                                if not has_class:
                                    # 添加新配置类
                                    new_element = cst.Element(value=cst.Name(self.class_name))
                                    existing_elements.append(new_element)
                                    new_list = assign.value.with_changes(elements=existing_elements)
                                    new_assign = assign.with_changes(value=new_list)
                                    new_stmt_body = [new_assign if s is assign else s for s in stmt.body]
                                    stmt = stmt.with_changes(body=new_stmt_body)
                                    self.component_added = True
            new_body.append(stmt)

        # 如果找到并更新了 configs 属性
        if configs_found and self.component_added:
            return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))

        return updated_node

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """在 get_components 函数中添加组件类引用（不包括 config 组件）"""
        # config 组件在 configs 类属性中处理，不需要在 get_components 中添加
        if self.is_config:
            return updated_node
        if updated_node.name.value != "get_components":
            return updated_node

        if self.component_added:
            return updated_node

        # 检查是否已存在组件引用
        function_code = cst.Module([]).code_for_node(updated_node)
        if self.class_name in function_code:
            self.component_added = True
            return updated_node

        # 找到 return 语句并修改其返回列表
        new_body = []
        for stmt in updated_node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for i, s in enumerate(stmt.body):
                    if isinstance(s, cst.Return) and s.value:
                        # 尝试解析返回值
                        if isinstance(s.value, cst.List):
                            # 如果是列表，添加新组件
                            existing_elements = list(s.value.elements)
                            new_element = cst.Element(value=cst.Name(self.class_name))
                            existing_elements.append(new_element)
                            new_list = s.value.with_changes(elements=existing_elements)
                            new_return = s.with_changes(value=new_list)
                            new_stmt_body = list(stmt.body)
                            new_stmt_body[i] = new_return
                            stmt = stmt.with_changes(body=new_stmt_body)
                            self.component_added = True
            new_body.append(stmt)

        if self.component_added:
            new_function_body = updated_node.body.with_changes(body=new_body)
            return updated_node.with_changes(body=new_function_body)

        return updated_node

"""
组件验证器
"""

import ast
import re
from pathlib import Path

from .base import BaseValidator, ValidationResult


class ComponentValidator(BaseValidator):
    """组件验证器

    通过解析 plugin.py 中的 get_plugin_components() 方法，
    找到所有组件类，然后检查每个组件类是否有必需的元数据。
    """

    # 不同组件类型的必需元数据
    # 注意：根据 MMC 基类定义，各组件使用不同的属性名：
    # - BaseTool: name, description
    # - BaseCommand/PlusCommand: command_name, command_description
    # - BaseAction: action_name, action_description
    # - BaseEventHandler: handler_name, handler_description
    # - BaseAdapter: adapter_name, adapter_description
    # - BasePrompt: prompt_name (无 prompt_description)
    # - BaseRouterComponent: component_name, component_description
    COMPONENT_REQUIRED_FIELDS = {
        "Action": ["action_name", "action_description"],
        "BaseAction": ["action_name", "action_description"],
        "Command": ["command_name", "command_description"],
        "BaseCommand": ["command_name", "command_description"],
        "PlusCommand": ["command_name", "command_description"],
        "Tool": ["name", "description"],
        "BaseTool": ["name", "description"],
        "EventHandler": ["handler_name", "handler_description"],
        "BaseEventHandler": ["handler_name", "handler_description"],
        "Adapter": ["adapter_name", "adapter_description"],
        "BaseAdapter": ["adapter_name", "adapter_description"],
        "Prompt": ["prompt_name"],
        "BasePrompt": ["prompt_name"],
        "Chatter": ["chatter_name", "chatter_description"],
        "BaseChatter": ["chatter_name", "chatter_description"],
        "Router": ["component_name", "component_description"],
        "BaseRouterComponent": ["component_name", "component_description"],
    }

    def validate(self) -> ValidationResult:
        """执行组件验证

        Returns:
            ValidationResult: 验证结果
        """
        # 获取插件名称
        plugin_name = self._get_plugin_name()
        if not plugin_name:
            self.result.add_error("无法确定插件名称")
            return self.result

        plugin_dir = self.plugin_path
        plugin_file = plugin_dir / "plugin.py"

        if not plugin_file.exists():
            self.result.add_error("插件文件不存在: plugin.py")
            return self.result

        # 解析 plugin.py 获取组件信息
        components = self._extract_components_from_plugin(plugin_file, plugin_name)

        if not components:
            self.result.add_warning(
                "未找到任何组件注册",
                file_path="plugin.py",
                suggestion="请在 get_plugin_components() 方法中注册组件",
            )
            return self.result

        # 验证每个组件
        for component_info in components:
            self._validate_component(component_info, plugin_dir, plugin_name)

        return self.result

    def _extract_components_from_plugin(self, plugin_file: Path, plugin_name: str) -> list[dict]:
        """从 plugin.py 中提取组件信息

        Args:
            plugin_file: plugin.py 文件路径
            plugin_name: 插件名称

        Returns:
            组件信息列表，每个元素包含: {
                'class_name': 组件类名,
                'base_class': 基类名称,
                'import_from': 导入来源（相对路径）
            }
        """
        try:
            with open(plugin_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(plugin_file))
        except Exception as e:
            self.result.add_error(f"解析 plugin.py 失败: {e}")
            return []

        components = []

        # 收集所有导入的组件类
        imports = self._collect_imports(tree, plugin_name)

        # 查找 get_plugin_components 方法
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_plugin_components":
                # 分析函数体，查找 components.append() 调用
                components.extend(self._extract_components_from_function(node, imports))

        return components

    def _extract_components_from_function(self, func_node: ast.FunctionDef, imports: dict[str, str]) -> list[dict]:
        """从 get_plugin_components 函数中提取组件信息

        Args:
            func_node: 函数定义节点
            imports: 导入映射

        Returns:
            组件信息列表
        """
        components = []

        # 遍历函数体，查找 components.append(...) 或直接 return [...]
        for stmt in func_node.body:
            # 情况1: components.append((ComponentInfo, ComponentClass))
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                # 检查是否是 .append() 调用
                if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                    # 获取 append 的参数（应该是一个元组）
                    if call.args:
                        component = self._extract_component_from_tuple(call.args[0], imports)
                        if component:
                            components.append(component)

            # 情况2: return [(...), (...), ...]
            elif isinstance(stmt, ast.Return) and stmt.value:
                if isinstance(stmt.value, ast.List):
                    for element in stmt.value.elts:
                        component = self._extract_component_from_tuple(element, imports)
                        if component:
                            components.append(component)

        return components

    def _collect_imports(self, tree: ast.AST, plugin_name: str) -> dict[str, str]:
        """收集导入信息

        Args:
            tree: AST 树
            plugin_name: 插件名称

        Returns:
            导入映射: {类名: 导入路径}
        """
        imports = {}

        for node in ast.walk(tree):
            # from xxx import yyy
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("."):
                    # 相对导入
                    for alias in node.names:
                        imports[alias.name] = node.module
                elif node.module and node.module.startswith(plugin_name):
                    # 绝对导入
                    for alias in node.names:
                        # 转换为相对路径
                        relative_module = "." + node.module[len(plugin_name) :]
                        imports[alias.name] = relative_module

        return imports

    def _extract_components_from_return(self, return_node: ast.AST, imports: dict[str, str]) -> list[dict]:
        """从 return 语句中提取组件信息

        Args:
            return_node: return 语句的 AST 节点
            imports: 导入映射

        Returns:
            组件信息列表
        """
        components = []

        if isinstance(return_node, ast.List):
            for element in return_node.elts:
                component = self._extract_component_from_tuple(element, imports)
                if component:
                    components.append(component)

        return components

    def _extract_component_from_tuple(self, tuple_node: ast.AST, imports: dict[str, str]) -> dict | None:
        """从元组中提取组件信息

        Args:
            tuple_node: 元组节点
            imports: 导入映射

        Returns:
            组件信息字典
        """
        if not isinstance(tuple_node, ast.Tuple) or len(tuple_node.elts) < 2:
            return None

        # 第二个元素应该是组件类
        class_node = tuple_node.elts[1]

        if isinstance(class_node, ast.Name):
            class_name = class_node.id
            import_from = imports.get(class_name, "")

            return {"class_name": class_name, "import_from": import_from}

        return None

    def _validate_component(self, component_info: dict, plugin_dir: Path, plugin_name: str) -> None:
        """验证单个组件

        Args:
            component_info: 组件信息
            plugin_dir: 插件目录
            plugin_name: 插件名称
        """
        class_name = component_info["class_name"]
        import_from = component_info["import_from"]

        # 根据导入路径找到组件文件
        component_file = self._resolve_component_file(import_from, class_name, plugin_dir)

        if not component_file:
            self.result.add_warning(
                f"无法定位组件 {class_name} 的源文件",
                file_path=f"{plugin_name}/plugin.py",
            )
            return

        # 解析组件文件
        try:
            with open(component_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(component_file))
        except Exception as e:
            self.result.add_error(
                f"解析组件文件失败: {component_file.name} - {e}",
                file_path=str(component_file.relative_to(self.plugin_path)),
            )
            return

        # 查找组件类定义
        class_node = self._find_class_definition(tree, class_name)
        if not class_node:
            self.result.add_error(
                f"在文件中未找到类定义: {class_name}",
                file_path=str(component_file.relative_to(self.plugin_path)),
            )
            return

        # 确定组件基类
        base_class = self._get_base_class(class_node)

        # 获取该组件类型需要的字段
        required_fields = self.COMPONENT_REQUIRED_FIELDS.get(base_class, [])

        if not required_fields:
            # 未知的组件类型
            self.result.add_info(
                f"组件 {class_name} 的基类 {base_class} 不在已知类型列表中",
                file_path=str(component_file.relative_to(self.plugin_path)),
            )
            return

        # 检查必需字段
        class_attributes = self._extract_class_attributes(class_node)

        for field in required_fields:
            if field not in class_attributes:
                self.result.add_error(
                    f"组件 {class_name} 缺少必需的类属性: {field}",
                    file_path=str(component_file.relative_to(self.plugin_path)),
                    suggestion=f"在类中添加: {field} = '...'",
                )
            elif not class_attributes[field]:
                self.result.add_warning(
                    f"组件 {class_name} 的类属性 {field} 为空",
                    file_path=str(component_file.relative_to(self.plugin_path)),
                )

    def _resolve_component_file(self, import_from: str, class_name: str, plugin_dir: Path) -> Path | None:
        """解析组件文件路径

        Args:
            import_from: 导入路径（如 ".actions.my_action"）
            class_name: 类名
            plugin_dir: 插件目录

        Returns:
            组件文件路径，如果找不到返回 None
        """
        # 如果没有导入路径，说明组件类在 plugin.py 中定义
        if not import_from:
            plugin_file = plugin_dir / "plugin.py"
            if plugin_file.exists():
                return plugin_file
            return None

        # 转换相对导入路径为文件路径
        # ".actions.my_action" -> "actions/my_action.py"
        module_path = import_from.lstrip(".").replace(".", "/")
        component_file = plugin_dir / f"{module_path}.py"

        if component_file.exists():
            return component_file

        # 尝试查找 __init__.py 中的定义
        init_file = plugin_dir / module_path / "__init__.py"
        if init_file.exists():
            return init_file

        # 搜索整个插件目录
        for py_file in plugin_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                    # 简单的正则匹配
                    if re.search(rf"class\s+{re.escape(class_name)}\s*\(", content):
                        return py_file
            except Exception:
                continue

        return None

    def _find_class_definition(self, tree: ast.AST, class_name: str) -> ast.ClassDef | None:
        """查找类定义

        Args:
            tree: AST 树
            class_name: 类名

        Returns:
            类定义节点
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def _get_base_class(self, class_node: ast.ClassDef) -> str:
        """获取组件的基类名称

        Args:
            class_node: 类定义节点

        Returns:
            基类名称
        """
        if not class_node.bases:
            return ""

        # 获取第一个基类
        base = class_node.bases[0]
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr

        return ""

    def _extract_class_attributes(self, class_node: ast.ClassDef) -> dict[str, str | None]:
        """提取类的属性

        Args:
            class_node: 类定义节点

        Returns:
            属性字典 {属性名: 属性值}
        """
        attributes = {}

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                # 类型注解的赋值: name: str = "value"
                attr_name = node.target.id
                attr_value = self._extract_value(node.value) if node.value else None
                attributes[attr_name] = attr_value
            elif isinstance(node, ast.Assign):
                # 普通赋值: name = "value"
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        attr_value = self._extract_value(node.value)
                        attributes[attr_name] = attr_value

        return attributes

    def _extract_value(self, node: ast.AST) -> str | None:
        """提取 AST 节点的值"""
        if isinstance(node, ast.Constant):
            return str(node.value) if node.value else None
        elif isinstance(node, ast.Str):  # Python 3.7 兼容
            return str(node.s) if node.s else None
        elif isinstance(node, ast.List):
            return "[...]"
        elif isinstance(node, ast.Dict):
            return "{...}"
        return None

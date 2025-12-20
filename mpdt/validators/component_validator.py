"""
组件验证器
"""

import ast
import re
from pathlib import Path

from .base import BaseValidator, ValidationResult
from ..utils.code_parser import CodeParser

class ComponentValidator(BaseValidator):
    """组件验证器

    通过解析 plugin.py 中的 get_plugin_components() 方法，
    找到所有组件类，然后检查每个组件类是否有必需的元数据和方法。
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

    # 不同组件类型的必需方法
    # 格式: {基类名: [必需方法名列表]}
    COMPONENT_REQUIRED_METHODS = {
        "BaseAction": ["execute", "go_activate"],
        "BaseCommand": ["execute"],
        "PlusCommand": ["execute"],
        "BaseTool": ["execute"],
        "BaseEventHandler": ["execute"],
        "BaseAdapter": ["from_platform_message"],
        "BasePrompt": ["execute"],
        "BaseRouterComponent": ["register_endpoints"],
    }

    # 方法签名要求
    # 格式: {基类名: {方法名: {"params": [...], "return_type": "..."}}}
    COMPONENT_METHOD_SIGNATURES = {
        "BaseAction": {
            "execute": {
                "params": [],  # async def execute(self)
                "return_type": "tuple[bool, str]",
                "is_async": True,
            },
            "go_activate": {
                "params": [("llm_judge_model", "optional")],  # async def go_activate(self, llm_judge_model=None)
                "return_type": "bool",
                "is_async": True,
            },
        },
        "BaseCommand": {
            "execute": {
                "params": [],  # async def execute(self)
                "return_type": "tuple[bool, str | None, bool]",
                "is_async": True,
            },
        },
        "PlusCommand": {
            "execute": {
                "params": [("args", "CommandArgs")],  # async def execute(self, args: CommandArgs)
                "return_type": "tuple[bool, str | None, bool]",
                "is_async": True,
            },
        },
        "BaseTool": {
            "execute": {
                "params": [("function_args", "dict[str, Any]")],  # async def execute(self, function_args: dict[str, Any])
                "return_type": "dict[str, Any]",
                "is_async": True,
            },
        },
        "BaseEventHandler": {
            "execute": {
                "params": [("kwargs", "dict | None")],  # async def execute(self, kwargs: dict | None)
                "return_type": "tuple[bool, bool, str | None]",
                "is_async": True,
            },
        },
        "BaseAdapter": {
            "from_platform_message": {
                "params": [("raw", "Any")],  # async def from_platform_message(self, raw: Any)
                "return_type": "MessageEnvelope",
                "is_async": True,
            },
        },
        "BasePrompt": {
            "execute": {
                "params": [],  # async def execute(self)
                "return_type": "str",
                "is_async": True,
            },
        },
        "BaseRouterComponent": {
            "register_endpoints": {
                "params": [],  # def register_endpoints(self)
                "return_type": "None",
                "is_async": False,
            },
        },
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

        # 验证插件类本身的元数据
        self._validate_plugin_class(plugin_file, plugin_name)

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

    def _validate_plugin_class(self, plugin_file: Path, plugin_name: str) -> None:
        """验证插件类本身的元数据

        检查 plugin.py 中的插件主类是否定义了必需的属性

        Args:
            plugin_file: plugin.py 文件路径
            plugin_name: 插件名称
        """
        try:
            parser = CodeParser.from_file(plugin_file)
        except Exception as e:
            self.result.add_error(f"解析 plugin.py 失败: {e}")
            return

        # 查找继承自 BasePlugin 的类
        plugin_classes = parser.find_class(base_class="BasePlugin")

        if not plugin_classes:
            self.result.add_warning(
                "未找到继承自 BasePlugin 的插件类",
                file_path="plugin.py",
                suggestion="插件主类应该继承自 BasePlugin",
            )
            return

        plugin_class = plugin_classes[0]
        class_name = plugin_class.name.value

        # 提取类属性
        class_attributes = parser.find_all_class_attributes(base_class="BasePlugin")

        # 检查必需的类属性
        # plugin_name 是必需的
        if "plugin_name" not in class_attributes:
            self.result.add_error(
                f"插件类 {class_name} 缺少必需的类属性: plugin_name",
                file_path="plugin.py",
                suggestion="在类中添加: plugin_name = '...'",
            )
        elif not class_attributes["plugin_name"]:
            self.result.add_error(
                f"插件类 {class_name} 的 plugin_name 属性为空",
                file_path="plugin.py",
            )

        # config_file_name 必需有
        if "config_file_name" not in class_attributes:
            self.result.add_error(
                f"插件类 {class_name} 未定义 config_file_name",
                file_path="plugin.py",
                suggestion="在类中添加: config_file_name = 'config.toml'",
            )

        # 检查 enable_plugin 属性（有默认值，但可以检查是否自定义）
        if "enable_plugin" in class_attributes:
            enable_value = class_attributes["enable_plugin"]
            if enable_value and str(enable_value).lower() not in ["true", "false"]:
                self.result.add_warning(
                    f"插件类 {class_name} 的 enable_plugin 应该是布尔值",
                    file_path="plugin.py",
                )

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

        # 递归遍历所有语句节点，包括 if/for 等块内的语句
        def walk_statements(statements):
            for stmt in statements:
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

                # 情况3: if 语句块内
                elif isinstance(stmt, ast.If):
                    # 递归检查 if 块
                    walk_statements(stmt.body)
                    # 递归检查 else/elif 块
                    walk_statements(stmt.orelse)

                # 情况4: for/while 循环块内
                elif isinstance(stmt, (ast.For, ast.While)):
                    walk_statements(stmt.body)
                    walk_statements(stmt.orelse)

                # 情况5: with 语句块内
                elif isinstance(stmt, ast.With):
                    walk_statements(stmt.body)

                # 情况6: try-except 块内
                elif isinstance(stmt, ast.Try):
                    walk_statements(stmt.body)
                    for handler in stmt.handlers:
                        walk_statements(handler.body)
                    walk_statements(stmt.orelse)
                    walk_statements(stmt.finalbody)

        # 从函数体开始遍历
        walk_statements(func_node.body)

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
            self.result.add_error(
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

        # 检查必需方法
        required_methods = self.COMPONENT_REQUIRED_METHODS.get(base_class, [])
        if required_methods:
            self._validate_required_methods(class_node, class_name, required_methods, component_file)

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

    def _validate_required_methods(
        self, class_node: ast.ClassDef, class_name: str, required_methods: list[str], component_file: Path
    ) -> None:
        """验证组件类是否实现了所有必需的方法

        Args:
            class_node: 类定义节点
            class_name: 类名
            required_methods: 必需方法列表
            component_file: 组件文件路径
        """
        # 提取类中定义的所有方法
        defined_methods = {}
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                defined_methods[node.name] = node

        # 获取基类名以查找签名要求
        base_class = self._get_base_class(class_node)
        method_signatures = self.COMPONENT_METHOD_SIGNATURES.get(base_class, {})

        # 检查每个必需方法
        for method_name in required_methods:
            if method_name not in defined_methods:
                self.result.add_error(
                    f"组件 {class_name} 缺少必需的方法: {method_name}",
                    file_path=str(component_file.relative_to(self.plugin_path)),
                    suggestion=f"在类中实现方法:\n    async def {method_name}(self, ...):\n        ...",
                )
            else:
                method_node = defined_methods[method_name]
                
                # 检查方法是否为空实现
                self._check_method_implementation(class_node, method_name, class_name, component_file)
                
                # 检查方法签名（如果有签名要求）
                if method_name in method_signatures:
                    signature_spec = method_signatures[method_name]
                    self._check_method_signature(
                        method_node, class_name, method_name, signature_spec, component_file
                    )

    def _check_method_implementation(
        self, class_node: ast.ClassDef, method_name: str, class_name: str, component_file: Path
    ) -> None:
        """检查方法是否为空实现

        Args:
            class_node: 类定义节点
            method_name: 方法名
            class_name: 类名
            component_file: 组件文件路径
        """
        # 找到方法定义
        method_node = None
        for node in class_node.body:
            if (isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)) and node.name == method_name:
                method_node = node
                break

        if not method_node:
            return

        # 检查方法体
        if not method_node.body:
            self.result.add_warning(
                f"组件 {class_name} 的方法 {method_name} 为空",
                file_path=str(component_file.relative_to(self.plugin_path)),
            )
            return

        # 检查是否只有 pass 或 raise NotImplementedError
        is_stub = True
        for stmt in method_node.body:
            # 跳过文档字符串
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, (ast.Str, ast.Constant)):
                continue

            # 检查是否为 pass
            if isinstance(stmt, ast.Pass):
                continue

            # 检查是否为 raise NotImplementedError
            if isinstance(stmt, ast.Raise):
                if isinstance(stmt.exc, ast.Call):
                    if isinstance(stmt.exc.func, ast.Name) and stmt.exc.func.id == "NotImplementedError":
                        continue

            # 如果有其他语句，说明不是空实现
            is_stub = False
            break

        if is_stub:
            self.result.add_warning(
                f"组件 {class_name} 的方法 {method_name} 只包含 pass 或 raise NotImplementedError，可能未实现",
                file_path=str(component_file.relative_to(self.plugin_path)),
                suggestion=f"请实现方法 {method_name} 的具体逻辑",
            )

    def _check_method_signature(
        self,
        method_node: ast.FunctionDef | ast.AsyncFunctionDef,
        class_name: str,
        method_name: str,
        signature_spec: dict,
        component_file: Path,
    ) -> None:
        """检查方法签名是否符合要求

        Args:
            method_node: 方法定义节点
            class_name: 类名
            method_name: 方法名
            signature_spec: 签名规范
            component_file: 组件文件路径
        """
        # 检查是否为异步方法
        is_async_required = signature_spec.get("is_async", False)
        is_async_actual = isinstance(method_node, ast.AsyncFunctionDef)

        if is_async_required and not is_async_actual:
            self.result.add_error(
                f"组件 {class_name} 的方法 {method_name} 应该是异步方法（使用 async def）",
                file_path=str(component_file.relative_to(self.plugin_path)),
                suggestion=f"将 'def {method_name}' 改为 'async def {method_name}'",
            )
        elif not is_async_required and is_async_actual:
            self.result.add_warning(
                f"组件 {class_name} 的方法 {method_name} 不应该是异步方法",
                file_path=str(component_file.relative_to(self.plugin_path)),
                suggestion=f"将 'async def {method_name}' 改为 'def {method_name}'",
            )

        # 检查参数（排除 self）
        required_params = signature_spec.get("params", [])
        actual_args = method_node.args.args[1:]  # 跳过 self

        # 检查参数数量
        min_params = sum(1 for param in required_params if param[1] != "optional")
        max_params = len(required_params)

        if len(actual_args) < min_params:
            param_names = [param[0] for param in required_params if param[1] != "optional"]
            self.result.add_error(
                f"组件 {class_name} 的方法 {method_name} 缺少必需参数，应包含: {', '.join(param_names)}",
                file_path=str(component_file.relative_to(self.plugin_path)),
                suggestion=f"方法签名应为: {'async ' if is_async_required else ''}def {method_name}(self, {', '.join(param_names)})",
            )
        elif len(actual_args) > max_params and not method_node.args.vararg and not method_node.args.kwarg:
            # 如果参数过多且没有 *args 或 **kwargs
            expected_params = [param[0] for param in required_params]
            self.result.add_warning(
                f"组件 {class_name} 的方法 {method_name} 参数过多，预期: {', '.join(expected_params) if expected_params else '无参数'}",
                file_path=str(component_file.relative_to(self.plugin_path)),
            )

        # 检查返回类型注解
        expected_return = signature_spec.get("return_type")
        if expected_return and method_node.returns:
            actual_return = self._extract_return_annotation(method_node.returns)
            if actual_return and not self._compare_type_annotations(actual_return, expected_return):
                self.result.add_warning(
                    f"组件 {class_name} 的方法 {method_name} 返回类型注解不匹配，预期: {expected_return}，实际: {actual_return}",
                    file_path=str(component_file.relative_to(self.plugin_path)),
                    suggestion=f"建议修改返回类型注解为: -> {expected_return}",
                )
        elif expected_return and not method_node.returns:
            self.result.add_warning(
                f"组件 {class_name} 的方法 {method_name} 缺少返回类型注解，建议添加: -> {expected_return}",
                file_path=str(component_file.relative_to(self.plugin_path)),
            )

    def _extract_return_annotation(self, node: ast.AST) -> str:
        """提取返回类型注解的字符串表示

        Args:
            node: 返回类型注解节点

        Returns:
            返回类型的字符串表示
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Subscript):
            # 处理泛型类型，如 tuple[bool, str]
            value = self._extract_return_annotation(node.value)
            if isinstance(node.slice, ast.Tuple):
                slice_parts = [self._extract_return_annotation(elt) for elt in node.slice.elts]
                return f"{value}[{', '.join(slice_parts)}]"
            else:
                slice_str = self._extract_return_annotation(node.slice)
                return f"{value}[{slice_str}]"
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # 处理联合类型，如 str | None
            left = self._extract_return_annotation(node.left)
            right = self._extract_return_annotation(node.right)
            return f"{left} | {right}"
        elif isinstance(node, ast.Attribute):
            # 处理 module.Type 形式
            return node.attr
        return ""

    def _compare_type_annotations(self, actual: str, expected: str) -> bool:
        """比较两个类型注解是否匹配（宽松比较）

        Args:
            actual: 实际的类型注解
            expected: 期望的类型注解

        Returns:
            是否匹配
        """
        # 标准化类型字符串（移除空格）
        actual = actual.replace(" ", "")
        expected = expected.replace(" ", "")

        # 直接比较
        if actual == expected:
            return True

        # 处理可选类型的不同写法
        # Optional[str] vs str | None
        if "Optional" in actual or "Optional" in expected:
            actual = actual.replace("Optional[", "").replace("]", "|None")
            expected = expected.replace("Optional[", "").replace("]", "|None")
            if actual == expected:
                return True

        # 宽松匹配：泛型基类型匹配
        # 例如 tuple 可以匹配 tuple[bool, str]，dict 可以匹配 dict[str, Any]
        actual_base = actual.split("[")[0]
        expected_base = expected.split("[")[0]
        
        if actual_base == expected_base:
            return True

        # 处理 Union 和 | 的不同写法
        if "Union" in actual or "Union" in expected or "|" in actual or "|" in expected:
            # 简化比较：提取基础类型
            actual_types = set(re.findall(r'\w+', actual))
            expected_types = set(re.findall(r'\w+', actual))
            if actual_types == expected_types:
                return True

        return False

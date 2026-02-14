"""
组件验证器模块

该模块提供组件验证功能，用于检查插件组件是否符合 Neo-MoFox 框架规范。
主要验证内容包括：
- 插件类的元数据和必需方法
- 组件类的元数据字段
- 组件类的必需方法及其签名
- 方法的实现完整性
"""

import ast
import re
from pathlib import Path

from ..utils.code_parser import CodeParser
from .base import BaseValidator, ValidationResult


class ComponentValidator(BaseValidator):
    """组件验证器类

    该验证器负责检查插件中的各类组件是否符合规范。验证流程如下：
    1. 解析 plugin.py 中的插件主类和 get_components() 方法
    2. 提取所有注册的组件类信息
    3. 对每个组件类进行规范性检查

    验证内容包括：
    - 插件类的基本元数据（plugin_name 等）
    - 插件类的必需方法（get_components）
    - 组件类的元数据字段（如 action_name, action_description 等）
    - 组件类的必需方法（如 execute, register_endpoints 等）
    - 方法签名的正确性（参数、返回类型、是否异步）
    - 方法实现的完整性（是否为空实现）
    """

    # ========================================
    # 配置常量：组件类型定义
    # ========================================

    # 不同组件类型的必需元数据字段映射表
    # 注意：根据 Neo-MoFox 基类定义，各组件使用不同的属性名：
    # - BaseTool: tool_name, tool_description
    # - BaseCommand: command_name, command_description
    # - BaseAction: action_name, action_description
    # - BaseEventHandler: handler_name, handler_description
    # - BaseAdapter: adapter_name, adapter_description
    # - BaseChatter: chatter_name, chatter_description
    # - BaseCollection: collection_name, collection_description
    # - BaseService: service_name, service_description
    # - BaseRouterComponent: router_name, router_description
    COMPONENT_REQUIRED_FIELDS = {
        "Action": ["action_name", "action_description"],
        "BaseAction": ["action_name", "action_description"],
        "Command": ["command_name", "command_description"],
        "BaseCommand": ["command_name", "command_description"],
        "Tool": ["tool_name", "tool_description"],
        "BaseTool": ["tool_name", "tool_description"],
        "EventHandler": ["handler_name", "handler_description"],
        "BaseEventHandler": ["handler_name", "handler_description"],
        "Adapter": ["adapter_name", "adapter_description"],
        "BaseAdapter": ["adapter_name", "adapter_description"],
        "Chatter": ["chatter_name", "chatter_description"],
        "BaseChatter": ["chatter_name", "chatter_description"],
        "Collection": ["collection_name", "collection_description"],
        "BaseCollection": ["collection_name", "collection_description"],
        "Service": ["service_name", "service_description"],
        "BaseService": ["service_name", "service_description"],
        "Router": ["router_name", "router_description"],
        "BaseRouterComponent": ["router_name", "router_description"],
    }

    # 不同组件类型的必需方法映射表
    # 格式: {基类名: [必需方法名列表]}
    COMPONENT_REQUIRED_METHODS = {
        "BaseAction": ["execute"],
        "BaseCommand": ["execute"],
        "BaseTool": ["execute"],
        "BaseEventHandler": ["execute"],
        "BaseAdapter": ["from_platform_message", "get_bot_info"],
        "BaseChatter": ["execute"],
        "BaseCollection": ["get_contents"],
        "BaseRouterComponent": ["register_endpoints"],
    }

    # 方法签名规范定义
    # 格式: {基类名: {方法名: {"params": [...], "return_type": "...", "is_async": bool}}}
    # 注意：对于接受 *args, **kwargs 的方法，params 设为 "variable"
    COMPONENT_METHOD_SIGNATURES = {
        "BaseAction": {
            "execute": {
                "params": "variable",  # async def execute(self, *args, **kwargs)
                "return_type": "tuple[bool, str]",
                "is_async": True,
            },
        },
        "BaseCommand": {
            "execute": {
                "params": [("message_text", "str")],  # async def execute(self, message_text: str)
                "return_type": "tuple[bool, str]",
                "is_async": True,
            },
        },
        "BaseTool": {
            "execute": {
                "params": "variable",  # async def execute(self, *args, **kwargs)
                "return_type": "tuple[bool, str | dict]",
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
            "get_bot_info": {
                "params": [],  # async def get_bot_info(self)
                "return_type": "dict[str, Any]",
                "is_async": True,
            },
        },
        "BaseChatter": {
            "execute": {
                "params": [],  # async def execute(self) -> AsyncGenerator[ChatterResult, None]
                "return_type": "AsyncGenerator",
                "is_async": True,
            },
        },
        "BaseCollection": {
            "get_contents": {
                "params": [],  # async def get_contents(self)
                "return_type": "list[str]",
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

    # ========================================
    # 主入口方法
    # ========================================

    # ========================================
    # 主入口方法
    # ========================================

    def validate(self) -> ValidationResult:
        """执行组件验证流程

        这是验证器的主入口方法，执行完整的组件验证流程：
        1. 获取插件名称
        2. 检查 plugin.py 文件是否存在
        3. 验证插件类本身的元数据
        4. 从 get_components() 中提取所有组件
        5. 对每个组件进行规范性验证

        Returns:
            ValidationResult: 验证结果对象，包含所有错误、警告和建议
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
                suggestion="请在 get_components() 方法中返回组件类列表，例如: return [MyAction, MyTool]",
            )
            return self.result

        # 验证每个组件
        for component_info in components:
            self._validate_component(component_info, plugin_dir, plugin_name)

        return self.result

    # ========================================
    # 插件类验证方法
    # ========================================

    def _validate_plugin_class(self, plugin_file: Path, plugin_name: str) -> None:
        """验证插件类本身的元数据和必需方法

        检查 plugin.py 中继承自 BasePlugin 的插件主类是否符合规范要求：
        - 必须定义 plugin_name 类属性
        - plugin_name 不能为空
        - 必须实现 get_components() 方法
        - get_components() 方法签名应正确
        - 建议添加返回类型注解

        Args:
            plugin_file: plugin.py 文件的路径对象
            plugin_name: 插件名称字符串
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
                suggestion="在类中添加: plugin_name = '...' | 可运行 'mpdt check --fix' 自动修复",
            )
        elif not class_attributes["plugin_name"]:
            self.result.add_error(
                f"插件类 {class_name} 的 plugin_name 属性为空",
                file_path="plugin.py",
            )

        # 检查必需的方法：get_components
        try:
            with open(plugin_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(plugin_file))
        except Exception as e:
            self.result.add_error(f"解析 plugin.py 失败: {e}")
            return

        # 查找插件类定义
        plugin_class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                plugin_class_node = node
                break

        if plugin_class_node:
            # 检查是否定义了 get_components 方法
            has_get_components = False
            for node in plugin_class_node.body:
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == "get_components":
                    has_get_components = True
                    # 检查方法签名
                    if len(node.args.args) != 1:  # 应该只有 self
                        self.result.add_warning(
                            f"插件类 {class_name} 的 get_components 方法签名不正确，应该是: def get_components(self) -> list[type]",
                            file_path="plugin.py",
                        )
                    # 检查返回类型注解
                    if not node.returns:
                        self.result.add_warning(
                            f"插件类 {class_name} 的 get_components 方法缺少返回类型注解，建议添加: -> list[type]",
                            file_path="plugin.py",
                        )
                    break

            if not has_get_components:
                self.result.add_error(
                    f"插件类 {class_name} 缺少必需的方法: get_components",
                    file_path="plugin.py",
                    suggestion="在类中实现方法:\n    def get_components(self) -> list[type]:\n        return [] | 可运行 'mpdt check --fix' 自动修复",
                )

    # ========================================
    # 组件提取方法
    # ========================================

    def _extract_components_from_plugin(self, plugin_file: Path, plugin_name: str) -> list[dict]:
        """从 plugin.py 中提取组件信息

        解析 plugin.py 文件，找到 get_components() 方法并提取其中返回的所有组件类。
        同时收集这些组件类的导入信息，用于后续定位组件源文件。

        处理流程：
        1. 解析 plugin.py 文件为 AST
        2. 收集文件中的所有导入语句
        3. 查找 get_components() 方法
        4. 分析该方法的返回值，提取组件类列表

        Args:
            plugin_file: plugin.py 文件的路径对象
            plugin_name: 插件名称字符串

        Returns:
            组件信息列表，每个元素为字典，包含:
                - 'class_name': 组件类的类名
                - 'import_from': 导入来源（相对路径，如 '.actions.my_action'）
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

        # 查找 get_components 方法
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "get_components":
                # 分析函数体，查找返回的组件类列表
                components.extend(self._extract_components_from_get_components(node, imports))
                break

        return components

    def _extract_components_from_get_components(
        self, func_node: ast.FunctionDef, imports: dict[str, str]
    ) -> list[dict]:
        """从 get_components 函数节点中提取组件信息

        分析 get_components 方法的实现，支持多种常见的返回模式：
        - 模式1: 直接返回列表 - return [MyAction, MyTool, MyCommand]
        - 模式2: 先赋值再返回 - components = [MyAction, MyTool]; return components
        - 模式3: 动态追加元素 - components = []; components.append(MyAction); return components

        处理步骤：
        1. 遍历函数体，收集所有变量赋值（列表类型）
        2. 收集所有列表的 append 调用
        3. 查找 return 语句
        4. 根据返回值类型（直接列表或变量名）提取组件类名
        5. 结合导入信息，构建完整的组件信息字典

        Args:
            func_node: get_components 函数的 AST 节点
            imports: 导入映射表，格式为 {类名: 导入路径}

        Returns:
            组件信息列表，每个元素包含组件类名和导入来源
        """
        # 收集函数内的所有变量赋值和 append 调用
        local_vars = {}  # 存储列表变量
        local_appends = {}  # 存储 append 调用: {变量名: [追加的元素]}

        for stmt in func_node.body:
            # 收集赋值语句: components = [...]
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and isinstance(stmt.value, ast.List):
                        var_name = target.id
                        local_vars[var_name] = stmt.value
                        if var_name not in local_appends:
                            local_appends[var_name] = []

            # 收集 append 调用: components.append(MyAction)
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                if isinstance(call.func, ast.Attribute) and call.func.attr == "append":
                    if isinstance(call.func.value, ast.Name):
                        var_name = call.func.value.id
                        if call.args and isinstance(call.args[0], ast.Name):
                            appended_class = call.args[0].id
                            if var_name not in local_appends:
                                local_appends[var_name] = []
                            local_appends[var_name].append(appended_class)

        # 查找 return 语句并提取组件列表
        components = []
        for stmt in func_node.body:
            if isinstance(stmt, ast.Return) and stmt.value:
                component_list = []

                # 情况1: return [ComponentClass1, ComponentClass2, ...]
                if isinstance(stmt.value, ast.List):
                    for element in stmt.value.elts:
                        if isinstance(element, ast.Name):
                            component_list.append(element.id)

                # 情况2/3: return variable_name
                elif isinstance(stmt.value, ast.Name):
                    var_name = stmt.value.id

                    # 从初始列表赋值中获取元素
                    if var_name in local_vars:
                        list_node = local_vars[var_name]
                        for element in list_node.elts:
                            if isinstance(element, ast.Name):
                                component_list.append(element.id)

                    # 从 append 调用中获取元素
                    if var_name in local_appends:
                        component_list.extend(local_appends[var_name])

                # 转换为组件信息字典
                for class_name in component_list:
                    import_from = imports.get(class_name, "")
                    components.append(
                        {
                            "class_name": class_name,
                            "import_from": import_from,
                        }
                    )
                break

        return components

    def _collect_imports(self, tree: ast.AST, plugin_name: str) -> dict[str, str]:
        """收集文件中的所有导入语句信息

        扫描 AST 树中的所有 ImportFrom 节点，提取导入的类名和路径映射。
        特别处理相对导入和绝对导入两种情况：
        - 相对导入: from .adapter import MyAdapter
        - 绝对导入: from myplugin.adapter import MyAdapter

        只收集本插件内部的导入，外部库的导入会被忽略。

        Args:
            tree: plugin.py 文件的 AST 树
            plugin_name: 插件包名（用于识别绝对导入中的本插件模块）

        Returns:
            导入映射字典，格式为 {类名: 相对导入路径}
            例如: {'MyAction': '.actions.my_action', 'MyTool': '.tools.my_tool'}
        """
        imports = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                # 使用 node.level 判断是否是相对导入
                # level > 0 表示相对导入（from . import, from .. import 等）
                if node.level > 0:
                    # 相对导入: from .adapter import X 或 from ..package.module import X
                    dots = "." * node.level
                    relative_module = dots + (node.module if node.module else "")
                    for alias in node.names:
                        imports[alias.name] = relative_module
                elif node.module and node.module.startswith(plugin_name):
                    # 绝对导入，但是导入本插件的模块
                    for alias in node.names:
                        relative_module = "." + node.module[len(plugin_name) :]
                        imports[alias.name] = relative_module

        return imports

    # ========================================
    # 组件验证方法
    # ========================================

    def _validate_component(self, component_info: dict, plugin_dir: Path, plugin_name: str) -> None:
        """验证单个组件的完整性和规范性

        对指定的组件进行全面验证，包括：
        1. 定位组件源文件
        2. 解析组件类定义
        3. 确定组件的基类类型
        4. 检查必需的元数据字段（如 action_name, action_description）
        5. 检查必需的方法（如 execute）
        6. 验证方法签名的正确性

        Args:
            component_info: 组件信息字典，包含 class_name 和 import_from
            plugin_dir: 插件目录路径
            plugin_name: 插件名称，用于错误报告
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
            # 列出文件中所有的类定义，帮助诊断
            all_classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            self.result.add_error(
                f"在文件中未找到类定义: {class_name}",
                file_path=str(component_file.relative_to(self.plugin_path)),
                suggestion=f"文件中实际定义的类: {', '.join(all_classes) if all_classes else '(无)'}",
            )
            return

        # 确定组件基类
        base_class = self._get_base_class(class_node)

        # 获取该组件类型需要的字段
        required_fields = self.COMPONENT_REQUIRED_FIELDS.get(base_class, [])

        if not required_fields:
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
                    suggestion=f"在类中添加: {field} = '...' | 可运行 'mpdt check --fix' 自动修复",
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

    # ========================================
    # 文件和类解析方法
    # ========================================

    def _resolve_component_file(self, import_from: str, class_name: str, plugin_dir: Path) -> Path | None:
        """解析组件类的源文件路径

        根据导入路径和类名定位组件的实际文件位置。支持多种情况：
        1. 无导入路径：组件在 plugin.py 中定义
        2. 相对导入：根据路径转换为文件路径
        3. 包导入：查找 __init__.py 文件
        4. 搜索备选：遍历插件目录找到类定义

        例如：
        - ".actions.my_action" -> "plugin_dir/actions/my_action.py"
        - ".adapter" -> "plugin_dir/adapter.py"

        Args:
            import_from: 导入路径字符串（如 ".actions.my_action"）
            class_name: 组件类名
            plugin_dir: 插件根目录路径

        Returns:
            组件文件的完整路径，如果找不到返回 None
        """
        # 如果没有导入路径，说明组件类在 plugin.py 中定义
        if not import_from:
            plugin_file = plugin_dir / "plugin.py"
            if plugin_file.exists():
                return plugin_file
            return None

        # 转换相对导入路径为文件路径
        # ".actions.my_action" -> "actions/my_action.py"
        # ".adapter" -> "adapter.py"
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
                    if re.search(rf"class\s+{re.escape(class_name)}\s*\(", content):
                        return py_file
            except Exception:
                continue

        return None

    def _find_class_definition(self, tree: ast.AST, class_name: str) -> ast.ClassDef | None:
        """在 AST 树中查找指定的类定义

        遍历 AST 树的所有节点，查找名称匹配的类定义节点。

        Args:
            tree: 文件的 AST 树
            class_name: 要查找的类名

        Returns:
            类定义的 AST 节点，如果未找到返回 None
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return node
        return None

    def _get_base_class(self, class_node: ast.ClassDef) -> str:
        """获取组件类的基类名称

        从类定义节点中提取第一个基类的名称。
        支持两种导入形式：
        - 直接名称: class MyAction(BaseAction)
        - 属性引用: class MyAction(module.BaseAction)

        Args:
            class_node: 类定义的 AST 节点

        Returns:
            基类名称字符串，如果没有基类则返回空字符串
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
        """提取类的所有属性及其值

        解析类定义中的所有属性赋值语句，支持两种格式：
        1. 带类型注解的赋值: name: str = "value"
        2. 普通赋值: name = "value"

        将提取出的属性值转换为字符串形式。

        Args:
            class_node: 类定义的 AST 节点

        Returns:
            属性字典，格式为 {属性名: 属性值字符串}
            对于复杂类型（列表、字典），返回简化表示（"[...]" 或 "{...}"）
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
        """从 AST 节点提取值的字符串表示

        将各种 AST 节点类型转换为相应的字符串值：
        - Constant/Str: 转换为字符串值
        - List: 返回 "[...]"
        - Dict: 返回 "{...}"
        - 其他: 返回 None

        Args:
            node: AST 节点

        Returns:
            值的字符串表示，无法提取则返回 None
        """
        if isinstance(node, ast.Constant):
            return str(node.value) if node.value else None
        elif isinstance(node, ast.Str):  # Python 3.7 兼容
            return str(node.s) if node.s else None
        elif isinstance(node, ast.List):
            return "[...]"
        elif isinstance(node, ast.Dict):
            return "{...}"
        return None

    # ========================================
    # 方法验证方法
    # ========================================

    def _validate_required_methods(
        self, class_node: ast.ClassDef, class_name: str, required_methods: list[str], component_file: Path
    ) -> None:
        """验证组件类是否实现了所有必需的方法

        检查组件类中是否定义了所有必需的方法，并验证：
        1. 方法是否存在
        2. 方法是否为空实现（只有 pass 或 raise NotImplementedError）
        3. 方法签名是否符合规范（如果有签名要求）

        Args:
            class_node: 组件类的 AST 节点
            class_name: 组件类名
            required_methods: 必需方法名列表
            component_file: 组件源文件路径
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
                    suggestion=f"在类中实现方法:\n    async def {method_name}(self, ...):\n        ... | 可运行 'mpdt check --fix' 自动修复",
                )
            else:
                method_node = defined_methods[method_name]

                # 检查方法是否为空实现
                self._check_method_implementation(class_node, method_name, class_name, component_file)

                # 检查方法签名（如果有签名要求）
                if method_name in method_signatures:
                    signature_spec = method_signatures[method_name]
                    self._check_method_signature(method_node, class_name, method_name, signature_spec, component_file)

    def _check_method_implementation(
        self, class_node: ast.ClassDef, method_name: str, class_name: str, component_file: Path
    ) -> None:
        """检查方法是否为空实现或占位实现

        判断方法体是否只包含以下内容：
        - 文档字符串（docstring）
        - pass 语句
        - raise NotImplementedError

        如果方法只包含以上内容，则认为是空实现，会产生警告。

        Args:
            class_node: 类定义节点
            method_name: 方法名
            class_name: 类名
            component_file: 组件文件路径
        """
        # 找到方法定义
        method_node = None
        for node in class_node.body:
            if (
                isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef)
            ) and node.name == method_name:
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
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str | ast.Constant):
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
        """检查方法签名是否符合规范要求

        根据 COMPONENT_METHOD_SIGNATURES 中定义的规范，验证方法的：
        1. 是否为异步方法（async def）
        2. 参数数量和类型是否正确
        3. 返回类型注解是否存在和匹配

        对于参数为 "variable" 的方法，跳过严格的参数检查（支持 *args, **kwargs）。

        Args:
            method_node: 方法定义的 AST 节点
            class_name: 类名
            method_name: 方法名
            signature_spec: 签名规范字典，包含 params, return_type, is_async
            component_file: 组件文件路径
        """
        # 检查是否为异步方法
        is_async_required = signature_spec.get("is_async", False)
        is_async_actual = isinstance(method_node, ast.AsyncFunctionDef)

        if is_async_required and not is_async_actual:
            self.result.add_error(
                f"组件 {class_name} 的方法 {method_name} 应该是异步方法（使用 async def）",
                file_path=str(component_file.relative_to(self.plugin_path)),
                suggestion=f"将 'def {method_name}' 改为 'async def {method_name}' | 可运行 'mpdt check --fix' 自动修复",
            )
        elif not is_async_required and is_async_actual:
            self.result.add_warning(
                f"组件 {class_name} 的方法 {method_name} 不应该是异步方法",
                file_path=str(component_file.relative_to(self.plugin_path)),
                suggestion=f"将 'async def {method_name}' 改为 'def {method_name}' | 可运行 'mpdt check --fix' 自动修复",
            )

        # 检查参数（排除 self）
        required_params = signature_spec.get("params", [])

        # 如果 params 为 "variable"，表示接受可变参数 (*args, **kwargs)，跳过严格的参数检查
        if required_params == "variable":
            # 对于可变参数方法，只需要确保方法存在即可
            pass
        elif isinstance(required_params, list):
            actual_args = method_node.args.args[1:]  # 跳过 self

            # 检查参数数量
            min_params = sum(1 for param in required_params if param[1] != "optional")
            max_params = len(required_params)

            if len(actual_args) < min_params:
                param_names = [param[0] for param in required_params if param[1] != "optional"]
                self.result.add_error(
                    f"组件 {class_name} 的方法 {method_name} 缺少必需参数，应包含: {', '.join(param_names)}",
                    file_path=str(component_file.relative_to(self.plugin_path)),
                    suggestion=f"方法签名应为: {'async ' if is_async_required else ''}def {method_name}(self, {', '.join(param_names)}) | 可运行 'mpdt check --fix' 自动修复",
                )
            elif len(actual_args) > max_params and not method_node.args.vararg and not method_node.args.kwarg:
                # 如果参数过多且没有 *args 或 **kwargs
                expected_params = [param[0] for param in required_params]
                self.result.add_warning(
                    f"组件 {class_name} 的方法 {method_name} 参数过多，预期: {', '.join(expected_params) if expected_params else '无参数'}",
                    file_path=str(component_file.relative_to(self.plugin_path)),
                    suggestion="可运行 'mpdt check --fix' 尝试自动修复",
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

    # ========================================
    # 类型注解解析方法
    # ========================================

    def _extract_return_annotation(self, node: ast.AST) -> str:
        """提取返回类型注解的字符串表示

        递归地解析 AST 节点，将复杂的类型注解转换为字符串形式。
        支持的类型格式：
        - 简单类型: str, int, bool
        - 泛型类型: list[str], dict[str, Any]
        - 元组类型: tuple[bool, str]
        - 联合类型: str | None
        - 模块属性: module.Type

        Args:
            node: 返回类型注解的 AST 节点

        Returns:
            类型注解的字符串表示，如 "tuple[bool, str]" 或 "str | None"
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
        """比较两个类型注解是否匹配（采用宽松比较策略）

        支持多种匹配策略：
        1. 精确匹配: 字符串完全相同
        2. Optional 等价: Optional[str] 等价于 str | None
        3. 泛型基类型匹配: tuple 匹配 tuple[bool, str]
        4. Union 等价: Union[str, None] 等价于 str | None

        这种宽松策略允许不同风格的类型注解通过验证。

        Args:
            actual: 实际的类型注解字符串
            expected: 期望的类型注解字符串

        Returns:
            是否匹配，True 表示匹配，False 表示不匹配
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
            actual_types = set(re.findall(r"\w+", actual))
            expected_types = set(re.findall(r"\w+", actual))
            if actual_types == expected_types:
                return True

        return False

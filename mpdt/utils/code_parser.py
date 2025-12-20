"""
代码解析器 - 使用 libcst 保留注释和格式

这是一个统一的代码解析工具，用于替代直接使用 ast 模块。
与 ast 不同，libcst（Concrete Syntax Tree）会保留所有的注释、空白和格式。

主要功能：
- 解析 Python 代码而不丢失注释
- 提取类定义、函数定义、赋值语句等
- 查找特定的类属性或方法
- 支持代码修改并保留原有格式

使用示例：
    >>> from mpdt.utils.code_parser import CodeParser
    >>> parser = CodeParser.from_file("plugin.py")
    >>> plugin_name = parser.find_class_attribute("BasePlugin", "plugin_name")
"""

from pathlib import Path
from typing import Any

import libcst as cst
from libcst.metadata import MetadataWrapper


class CodeParser:
    """代码解析器 - 保留注释的 Python 代码解析

    Attributes:
        module: libcst 的模块树
        source: 原始源代码字符串
    """

    def __init__(self, source: str):
        """初始化代码解析器

        Args:
            source: Python 源代码字符串
        """
        self.source = source
        self.module = cst.parse_module(source)

    @classmethod
    def from_file(cls, file_path: Path | str, encoding: str = "utf-8") -> "CodeParser":
        """从文件创建代码解析器

        Args:
            file_path: 文件路径
            encoding: 文件编码，默认 utf-8

        Returns:
            CodeParser 实例
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, encoding=encoding) as f:
            source = f.read()

        return cls(source)

    def find_class(self, class_name: str | None = None, base_class: str | None = None) -> list[cst.ClassDef]:
        """查找类定义

        Args:
            class_name: 类名，如果为 None 则匹配所有类
            base_class: 基类名，如果为 None 则不检查基类

        Returns:
            匹配的类定义列表
        """
        visitor = ClassFinderVisitor(class_name=class_name, base_class=base_class)
        self.module.visit(visitor)
        return visitor.found_classes

    def find_class_attribute(
        self,
        base_class: str | None = None,
        attribute_name: str | None = None,
        class_name: str | None = None,
    ) -> Any:
        """在类中查找属性的值

        Args:
            base_class: 基类名，用于过滤类
            attribute_name: 属性名
            class_name: 类名，用于精确匹配特定类

        Returns:
            属性值，如果找到多个返回第一个，未找到返回 None
        """
        classes = self.find_class(class_name=class_name, base_class=base_class)

        for cls in classes:
            for statement in cls.body.body:
                # 处理简单赋值: attr = value
                if isinstance(statement, cst.SimpleStatementLine):
                    for node in statement.body:
                        if isinstance(node, cst.Assign):
                            for target in node.targets:
                                if isinstance(target.target, cst.Name):
                                    if attribute_name is None or target.target.value == attribute_name:
                                        return self._extract_value(node.value)

                        # 处理带类型注解的赋值: attr: Type = value
                        elif isinstance(node, cst.AnnAssign):
                            if isinstance(node.target, cst.Name):
                                if attribute_name is None or node.target.value == attribute_name:
                                    if node.value:
                                        return self._extract_value(node.value)

        return None

    def find_all_class_attributes(
        self,
        base_class: str | None = None,
        class_name: str | None = None,
    ) -> dict[str, Any]:
        """获取类中的所有属性

        Args:
            base_class: 基类名
            class_name: 类名

        Returns:
            属性名到值的字典
        """
        classes = self.find_class(class_name=class_name, base_class=base_class)
        attributes = {}

        for cls in classes:
            for statement in cls.body.body:
                if isinstance(statement, cst.SimpleStatementLine):
                    for node in statement.body:
                        if isinstance(node, cst.Assign):
                            for target in node.targets:
                                if isinstance(target.target, cst.Name):
                                    attr_name = target.target.value
                                    attributes[attr_name] = self._extract_value(node.value)

                        elif isinstance(node, cst.AnnAssign):
                            if isinstance(node.target, cst.Name):
                                attr_name = node.target.value
                                if node.value:
                                    attributes[attr_name] = self._extract_value(node.value)

        return attributes

    def has_class_attribute(
        self,
        attribute_name: str,
        base_class: str | None = None,
        class_name: str | None = None,
    ) -> bool:
        """检查类中是否存在某个属性

        Args:
            attribute_name: 属性名
            base_class: 基类名
            class_name: 类名

        Returns:
            是否存在该属性
        """
        return self.find_class_attribute(base_class, attribute_name, class_name) is not None

    def find_assignments(self, variable_name: str) -> list[Any]:
        """查找模块级别的赋值语句

        Args:
            variable_name: 变量名

        Returns:
            赋值值的列表
        """
        visitor = AssignmentFinderVisitor(variable_name)
        self.module.visit(visitor)
        return visitor.found_values

    def find_call_arguments(self, variable_name: str, function_name: str | None = None) -> dict[str, Any] | None:
        """查找变量赋值中的函数调用参数

        Args:
            variable_name: 变量名（如 __plugin_meta__）
            function_name: 函数名（如 PluginMetadata），如果为 None 则匹配任何调用

        Returns:
            参数字典 {参数名: 参数值}，如果未找到返回 None
        """
        visitor = CallArgumentsFinderVisitor(variable_name, function_name)
        self.module.visit(visitor)
        if visitor.found_arguments:
            # 提取参数值
            result = {}
            for arg_name, arg_value in visitor.found_arguments.items():
                result[arg_name] = self._extract_value(arg_value)
            return result
        return None

    def get_missing_call_arguments(self, variable_name: str, required_args: list[str], function_name: str | None = None) -> list[str]:
        """获取函数调用中缺失的必需参数

        Args:
            variable_name: 变量名
            required_args: 必需参数列表
            function_name: 函数名

        Returns:
            缺失的参数名列表
        """
        current_args = self.find_call_arguments(variable_name, function_name)
        if current_args is None:
            return required_args
        
        missing = []
        for arg in required_args:
            if arg not in current_args or current_args[arg] is None or current_args[arg] == "":
                missing.append(arg)
        return missing

    def _extract_value(self, node: cst.BaseExpression) -> Any:
        """从 CST 节点中提取 Python 值

        Args:
            node: CST 表达式节点

        Returns:
            提取的 Python 值
        """
        # 处理字符串字面量
        if isinstance(node, (cst.SimpleString, cst.ConcatenatedString)):
            try:
                return node.evaluated_value
            except Exception:
                return None

        # 处理整数
        if isinstance(node, cst.Integer):
            return int(node.value)

        # 处理浮点数
        if isinstance(node, cst.Float):
            return float(node.value)

        # 处理布尔值和 None
        if isinstance(node, cst.Name):
            if node.value == "True":
                return True
            elif node.value == "False":
                return False
            elif node.value == "None":
                return None

        # 处理字典
        if isinstance(node, cst.Dict):
            result = {}
            for element in node.elements:
                if isinstance(element, cst.DictElement):
                    key = self._extract_value(element.key)
                    value = self._extract_value(element.value)
                    if key is not None:
                        result[key] = value
            return result

        # 处理列表
        if isinstance(node, cst.List):
            return [self._extract_value(el.value) for el in node.elements if isinstance(el, cst.Element)]

        # 处理元组
        if isinstance(node, cst.Tuple):
            return tuple(self._extract_value(el.value) for el in node.elements if isinstance(el, cst.Element))

        # 处理集合
        if isinstance(node, cst.Set):
            return {self._extract_value(el.value) for el in node.elements if isinstance(el, cst.Element)}

        # 无法提取的复杂表达式返回 None
        return None

    def get_code(self) -> str:
        """获取当前的代码（包含所有修改）

        Returns:
            代码字符串
        """
        return self.module.code

    def save_to_file(self, file_path: Path | str, encoding: str = "utf-8") -> None:
        """保存代码到文件

        Args:
            file_path: 文件路径
            encoding: 文件编码
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(self.get_code())


class ClassFinderVisitor(cst.CSTVisitor):
    """查找类定义的访问器"""

    def __init__(self, class_name: str | None = None, base_class: str | None = None):
        self.class_name = class_name
        self.base_class = base_class
        self.found_classes: list[cst.ClassDef] = []

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """访问类定义"""
        # 检查类名
        if self.class_name is not None and node.name.value != self.class_name:
            return

        # 检查基类
        if self.base_class is not None:
            has_base = False
            for arg in node.bases:
                if isinstance(arg.value, cst.Name) and arg.value.value == self.base_class:
                    has_base = True
                    break
                # 处理带模块的基类，如 module.BaseClass
                elif isinstance(arg.value, cst.Attribute) and arg.value.attr.value == self.base_class:
                    has_base = True
                    break

            if not has_base:
                return

        self.found_classes.append(node)


class AssignmentFinderVisitor(cst.CSTVisitor):
    """查找赋值语句的访问器"""

    def __init__(self, variable_name: str):
        self.variable_name = variable_name
        self.found_values: list[Any] = []
        self.parser = None

    def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine) -> None:
        """访问简单语句"""
        for statement in node.body:
            if isinstance(statement, cst.Assign):
                for target in statement.targets:
                    if isinstance(target.target, cst.Name) and target.target.value == self.variable_name:
                        # 需要一个 CodeParser 实例来提取值
                        # 这里我们暂时保存节点，让调用者来提取
                        self.found_values.append(statement.value)

            elif isinstance(statement, cst.AnnAssign):
                if isinstance(statement.target, cst.Name) and statement.target.value == self.variable_name:
                    if statement.value:
                        self.found_values.append(statement.value)


class CallArgumentsFinderVisitor(cst.CSTVisitor):
    """查找函数调用参数的访问器"""

    def __init__(self, variable_name: str, function_name: str | None = None):
        self.variable_name = variable_name
        self.function_name = function_name
        self.found_arguments: dict[str, cst.BaseExpression] = {}

    def visit_SimpleStatementLine(self, node: cst.SimpleStatementLine) -> None:
        """访问简单语句"""
        for statement in node.body:
            # 处理普通赋值: var = FunctionCall(...)
            if isinstance(statement, cst.Assign):
                for target in statement.targets:
                    if isinstance(target.target, cst.Name) and target.target.value == self.variable_name:
                        self._extract_call_arguments(statement.value)

            # 处理带类型注解的赋值: var: Type = FunctionCall(...)
            elif isinstance(statement, cst.AnnAssign):
                if isinstance(statement.target, cst.Name) and statement.target.value == self.variable_name:
                    if statement.value:
                        self._extract_call_arguments(statement.value)

    def _extract_call_arguments(self, node: cst.BaseExpression) -> None:
        """从表达式中提取函数调用参数"""
        if not isinstance(node, cst.Call):
            return

        # 检查函数名是否匹配
        if self.function_name is not None:
            func_name = None
            if isinstance(node.func, cst.Name):
                func_name = node.func.value
            elif isinstance(node.func, cst.Attribute):
                func_name = node.func.attr.value

            if func_name != self.function_name:
                return

        # 提取参数
        for arg in node.args:
            if arg.keyword:
                # 关键字参数: name=value
                arg_name = arg.keyword.value
                self.found_arguments[arg_name] = arg.value

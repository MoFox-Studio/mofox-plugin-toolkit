"""libcst Transformers for code modifications

提供各种代码转换器，用于修改 Python AST
"""

import libcst as cst


class AddCallArgumentTransformer(cst.CSTTransformer):
    """在函数调用中添加参数的转换器"""

    def __init__(self, variable_name: str, function_name: str, arg_name: str, arg_value: str):
        self.variable_name = variable_name
        self.function_name = function_name
        self.arg_name = arg_name
        self.arg_value = arg_value
        self.modified = False

    def leave_SimpleStatementLine(  # noqa: N802
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        """修改赋值语句中的函数调用"""
        new_body = []

        for statement in updated_node.body:
            # 处理普通赋值
            if isinstance(statement, cst.Assign):
                for target in statement.targets:
                    if isinstance(target.target, cst.Name) and target.target.value == self.variable_name:
                        # 找到目标变量，修改其值
                        new_value = self._add_argument_to_call(statement.value)
                        if new_value is not None:
                            statement = statement.with_changes(value=new_value)
                            self.modified = True

            # 处理带类型注解的赋值
            elif isinstance(statement, cst.AnnAssign):
                if isinstance(statement.target, cst.Name) and statement.target.value == self.variable_name:
                    if statement.value:
                        new_value = self._add_argument_to_call(statement.value)
                        if new_value is not None:
                            statement = statement.with_changes(value=new_value)
                            self.modified = True

            new_body.append(statement)

        return updated_node.with_changes(body=new_body)

    def _add_argument_to_call(self, node: cst.BaseExpression) -> cst.BaseExpression | None:
        """在函数调用中添加参数"""
        if not isinstance(node, cst.Call):
            return None

        # 检查函数名
        func_name = None
        if isinstance(node.func, cst.Name):
            func_name = node.func.value
        elif isinstance(node.func, cst.Attribute):
            func_name = node.func.attr.value

        if func_name != self.function_name:
            return None

        # 检查参数是否已存在
        for arg in node.args:
            if arg.keyword and arg.keyword.value == self.arg_name:
                return None  # 参数已存在

        # 创建新参数
        new_arg = cst.Arg(
            keyword=cst.Name(self.arg_name),
            value=cst.parse_expression(self.arg_value),
            equal=cst.AssignEqual(
                whitespace_before=cst.SimpleWhitespace(""), whitespace_after=cst.SimpleWhitespace("")
            ),
        )

        # 添加参数到列表
        new_args = list(node.args) + [new_arg]

        return node.with_changes(args=new_args)


class AddClassAttributeTransformer(cst.CSTTransformer):
    """添加类属性的转换器"""

    def __init__(self, class_name: str, attr_name: str, attr_value: str):
        self.class_name = class_name
        self.attr_name = attr_name
        self.attr_value = attr_value
        self.modified = False

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        """在类定义中添加属性"""
        if updated_node.name.value != self.class_name:
            return updated_node

        # 检查属性是否已存在
        for stmt in updated_node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, cst.Assign | cst.AnnAssign):
                        target = s.targets[0].target if isinstance(s, cst.Assign) else s.target
                        if isinstance(target, cst.Name) and target.value == self.attr_name:
                            return updated_node  # 属性已存在

        # 创建新的赋值语句
        new_assignment = cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name(self.attr_name))],
                    value=cst.parse_expression(self.attr_value),
                )
            ]
        )

        # 插入到类体开头（在 docstring 之后）
        body_list = list(updated_node.body.body)
        insert_pos = 0

        # 跳过 docstring
        if body_list and isinstance(body_list[0], cst.SimpleStatementLine):
            first_stmt = body_list[0].body[0]
            if isinstance(first_stmt, cst.Expr) and isinstance(
                first_stmt.value, cst.SimpleString | cst.ConcatenatedString
            ):
                insert_pos = 1

        body_list.insert(insert_pos, new_assignment)

        self.modified = True
        return updated_node.with_changes(body=updated_node.body.with_changes(body=body_list))


class AddMethodTransformer(cst.CSTTransformer):
    """添加方法的转换器"""

    def __init__(self, class_name: str, method_name: str, method_template: str):
        self.class_name = class_name
        self.method_name = method_name
        self.method_template = method_template
        self.modified = False

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        """在类中添加方法"""
        if updated_node.name.value != self.class_name:
            return updated_node

        # 检查方法是否已存在
        for stmt in updated_node.body.body:
            if isinstance(stmt, cst.FunctionDef):
                if stmt.name.value == self.method_name:
                    return updated_node  # 方法已存在

        # 解析方法模板
        try:
            # 将模板包装成完整的类来解析
            full_code = f"class Temp:\n    {self.method_template}"
            temp_module = cst.parse_module(full_code)
            temp_class = temp_module.body[0]
            if isinstance(temp_class, cst.ClassDef):
                new_method = temp_class.body.body[0]
            else:
                return updated_node

            # 添加到类体末尾
            body_list = list(updated_node.body.body)
            body_list.append(new_method)

            self.modified = True
            return updated_node.with_changes(body=updated_node.body.with_changes(body=body_list))
        except Exception:
            return updated_node


class FixMethodAsyncTransformer(cst.CSTTransformer):
    """修复方法异步性的转换器"""

    def __init__(self, class_name: str, method_name: str, should_be_async: bool):
        self.class_name = class_name
        self.method_name = method_name
        self.should_be_async = should_be_async
        self.modified = False
        self.in_target_class = False

    def visit_ClassDef(self, node: cst.ClassDef) -> None:  # noqa: N802
        if node.name.value == self.class_name:
            self.in_target_class = True

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            self.in_target_class = False
        return updated_node

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """修改函数定义"""
        if not self.in_target_class or updated_node.name.value != self.method_name:
            return updated_node

        if self.should_be_async:
            # 转换为异步函数
            self.modified = True
            return cst.FunctionDef(
                name=updated_node.name,
                params=updated_node.params,
                body=updated_node.body,
                decorators=updated_node.decorators,
                returns=updated_node.returns,
                asynchronous=cst.Asynchronous(whitespace_after=cst.SimpleWhitespace(" ")),
            )
        else:
            # 转换为同步函数（移除 async）
            if isinstance(updated_node, cst.FunctionDef) and updated_node.asynchronous:
                self.modified = True
                return updated_node.with_changes(asynchronous=None)

        return updated_node


class FixReturnTypeTransformer(cst.CSTTransformer):
    """修复方法返回类型的转换器"""

    def __init__(self, class_name: str, method_name: str, return_type: str):
        self.class_name = class_name
        self.method_name = method_name
        self.return_type = return_type
        self.modified = False
        self.in_target_class = False

    def visit_ClassDef(self, node: cst.ClassDef) -> None:  # noqa: N802
        if node.name.value == self.class_name:
            self.in_target_class = True

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            self.in_target_class = False
        return updated_node

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """修改函数返回类型"""
        if not self.in_target_class or updated_node.name.value != self.method_name:
            return updated_node

        try:
            # 创建新的返回类型注解
            new_annotation = cst.Annotation(annotation=cst.parse_expression(self.return_type))

            self.modified = True
            return updated_node.with_changes(returns=new_annotation)
        except Exception:
            return updated_node


class FixMethodParametersTransformer(cst.CSTTransformer):
    """修复方法参数的转换器"""

    def __init__(self, class_name: str, method_name: str, params_str: str):
        self.class_name = class_name
        self.method_name = method_name
        self.params_str = params_str
        self.modified = False
        self.in_target_class = False

    def visit_ClassDef(self, node: cst.ClassDef) -> None:  # noqa: N802
        if node.name.value == self.class_name:
            self.in_target_class = True

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            self.in_target_class = False
        return updated_node

    def leave_FunctionDef(  # noqa: N802
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        """修改函数参数"""
        if not self.in_target_class or updated_node.name.value != self.method_name:
            return updated_node

        try:
            # 解析参数
            param_list = [p.strip() for p in self.params_str.split(",")]
            new_params = [cst.Param(name=cst.Name("self"))]

            for param in param_list:
                if not param:
                    continue

                # 解析参数（可能包含类型注解和默认值）
                if ":" in param:
                    parts = param.split(":")
                    param_name = parts[0].strip()
                    type_and_default = parts[1].strip()

                    if "=" in type_and_default:
                        type_part, default_part = type_and_default.split("=", 1)
                        new_params.append(
                            cst.Param(
                                name=cst.Name(param_name),
                                annotation=cst.Annotation(annotation=cst.parse_expression(type_part.strip())),
                                default=cst.parse_expression(default_part.strip()),
                            )
                        )
                    else:
                        new_params.append(
                            cst.Param(
                                name=cst.Name(param_name),
                                annotation=cst.Annotation(annotation=cst.parse_expression(type_and_default)),
                            )
                        )
                else:
                    param_name = param.split("=")[0].strip()
                    if "=" in param:
                        default_val = param.split("=")[1].strip()
                        new_params.append(
                            cst.Param(name=cst.Name(param_name), default=cst.parse_expression(default_val))
                        )
                    else:
                        new_params.append(cst.Param(name=cst.Name(param_name)))

            self.modified = True
            return updated_node.with_changes(params=updated_node.params.with_changes(params=new_params))
        except Exception:
            return updated_node


class AddRegisterPluginDecoratorTransformer(cst.CSTTransformer):
    """为插件类添加 @register_plugin 装饰器的转换器"""

    def __init__(self, has_import: bool):
        self.has_import = has_import
        self.modified = False
        self.import_added = False

    def visit_Module(self, node: cst.Module) -> None:  # noqa: N802
        """访问模块，记录是否需要添加导入"""
        pass

    def leave_Module(  # noqa: N802
        self, original_node: cst.Module, updated_node: cst.Module
    ) -> cst.Module:
        """如果需要，在模块顶部添加 register_plugin 导入"""
        if not self.has_import and self.modified and not self.import_added:
            # 在导入部分的末尾添加 register_plugin 导入
            new_body = []
            import_section_ended = False

            for i, statement in enumerate(updated_node.body):
                new_body.append(statement)

                # 检查是否到达导入部分的末尾
                if not import_section_ended:
                    if isinstance(statement, cst.SimpleStatementLine):
                        # 检查是否为导入语句
                        is_import = any(isinstance(s, cst.Import | cst.ImportFrom) for s in statement.body)
                        if not is_import:
                            # 到达非导入语句，在此之前插入
                            import_line = cst.SimpleStatementLine(
                                body=[
                                    cst.ImportFrom(
                                        module=cst.Attribute(
                                            value=cst.Attribute(
                                                value=cst.Attribute(value=cst.Name("src"), attr=cst.Name("core")),
                                                attr=cst.Name("components"),
                                            ),
                                            attr=cst.Name("loader"),
                                        ),
                                        names=[cst.ImportAlias(name=cst.Name("register_plugin"))],
                                    )
                                ]
                            )
                            new_body.insert(-1, import_line)
                            import_section_ended = True
                            self.import_added = True

            if not self.import_added:
                # 如果没有找到合适的位置，在开头添加
                import_line = cst.SimpleStatementLine(
                    body=[
                        cst.ImportFrom(
                            module=cst.Attribute(
                                value=cst.Attribute(
                                    value=cst.Attribute(value=cst.Name("src"), attr=cst.Name("core")),
                                    attr=cst.Name("components"),
                                ),
                                attr=cst.Name("loader"),
                            ),
                            names=[cst.ImportAlias(name=cst.Name("register_plugin"))],
                        )
                    ]
                )
                new_body.insert(0, import_line)
                self.import_added = True

            if new_body != list(updated_node.body):
                return updated_node.with_changes(body=new_body)

        return updated_node

    def leave_ClassDef(  # noqa: N802
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        """为继承自 BasePlugin 的类添加 @register_plugin 装饰器"""
        # 检查是否继承自 BasePlugin
        is_plugin_class = False
        if updated_node.bases:
            for base in updated_node.bases:
                if isinstance(base.value, cst.Name) and base.value.value == "BasePlugin":
                    is_plugin_class = True
                    break

        if not is_plugin_class:
            return updated_node

        # 检查是否已有 register_plugin 装饰器
        has_decorator = False
        if updated_node.decorators:
            for decorator in updated_node.decorators:
                if isinstance(decorator.decorator, cst.Name) and decorator.decorator.value == "register_plugin":
                    has_decorator = True
                    break

        if has_decorator:
            return updated_node

        # 添加 @register_plugin 装饰器
        new_decorator = cst.Decorator(decorator=cst.Name("register_plugin"))
        new_decorators = list(updated_node.decorators) + [new_decorator]

        self.modified = True
        return updated_node.with_changes(decorators=new_decorators)

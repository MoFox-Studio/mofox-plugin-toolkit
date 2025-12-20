"""自动修复验证器

提供自动修复常见问题的功能，可以接收其他验证器的报错并尝试自动修复
"""

import ast
import re
from pathlib import Path
from typing import Any

import libcst as cst

from ..utils.code_parser import CodeParser
from .base import BaseValidator, ValidationIssue, ValidationLevel, ValidationResult


class AutoFixValidator(BaseValidator):
    """自动修复验证器

    接收其他验证器的错误并尝试自动修复
    """

    def __init__(self, plugin_path: Path):
        super().__init__(plugin_path)
        self.fixes_applied = []
        self.fixes_failed = []
        self.fixed_issues = []  # 记录已修复的原始问题

    def validate(self) -> ValidationResult:
        """执行自动修复（实际上是 fix 而非 validate）
        
        这是一个兼容方法，建议使用 fix_issues 方法
        """
        result = ValidationResult(
            validator_name="AutoFixValidator",
            success=True
        )

        plugin_name = self._get_plugin_name()
        if not plugin_name:
            result.add_error("无法确定插件名称")
            return result

        # 修复导入顺序
        self._fix_import_order(result)

        # 汇总修复结果
        if self.fixes_applied:
            result.add_info(f"应用了 {len(self.fixes_applied)} 个自动修复")
            for fix in self.fixes_applied:
                result.add_info(fix)
        else:
            result.add_info("未发现可自动修复的问题")

        return result

    def fix_issues(self, validation_results: list[ValidationResult]) -> ValidationResult:
        """自动修复验证问题
        
        Args:
            validation_results: 其他验证器返回的验证结果列表
            
        Returns:
            修复结果
        """
        result = ValidationResult(
            validator_name="AutoFixValidator",
            success=True
        )
        
        plugin_name = self._get_plugin_name()
        if not plugin_name:
            return result

        # 收集所有需要修复的问题
        all_issues = []
        for validation_result in validation_results:
            for issue in validation_result.issues:
                if issue.level == ValidationLevel.ERROR or issue.level == ValidationLevel.WARNING:
                    all_issues.append(issue)

        if not all_issues:
            return result

        # 按问题类型分类并修复
        self._fix_missing_metadata_issues(all_issues, result)
        self._fix_missing_component_fields(all_issues, result)
        self._fix_missing_methods(all_issues, result)
        self._fix_method_signatures(all_issues, result)
        self._fix_import_order(result)

        return result

    def _fix_missing_metadata_issues(self, issues: list[ValidationIssue], result: ValidationResult) -> None:
        """修复缺失的元数据问题"""
        for issue in issues:
            # 匹配 "缺少必需的类属性" 相关错误
            if "缺少必需的类属性" in issue.message or "缺少必需元数据字段" in issue.message:
                try:
                    # 从消息中提取字段名
                    match = re.search(r'[：:]\s*(\w+)', issue.message)
                    if match:
                        field_name = match.group(1)
                        file_path = self._resolve_file_path(issue.file_path)
                        if file_path and file_path.exists():
                            before_count = len(self.fixes_applied)
                            self._add_class_attribute(file_path, field_name, issue)
                            # 如果修复成功，记录原始问题
                            if len(self.fixes_applied) > before_count:
                                self.fixed_issues.append(issue)
                except Exception as e:
                    self.fixes_failed.append(f"修复元数据字段失败: {issue.message} - {e}")

    def _fix_missing_component_fields(self, issues: list[ValidationIssue], result: ValidationResult) -> None:
        """修复组件缺失的字段"""
        for issue in issues:
            if "缺少必需的类属性" in issue.message:
                try:
                    # 提取类名和字段名
                    # 格式: "组件 MyAction 缺少必需的类属性: action_name"
                    match = re.search(r'组件\s+(\w+)\s+缺少必需的类属性[：:]\s*(\w+)', issue.message)
                    if match:
                        class_name = match.group(1)
                        field_name = match.group(2)
                        file_path = self._resolve_file_path(issue.file_path)
                        
                        if file_path and file_path.exists():
                            before_count = len(self.fixes_applied)
                            self._add_class_attribute(
                                file_path, 
                                field_name, 
                                issue,
                                class_name=class_name
                            )
                            if len(self.fixes_applied) > before_count:
                                self.fixed_issues.append(issue)
                except Exception as e:
                    self.fixes_failed.append(f"修复组件字段失败: {issue.message} - {e}")

    def _fix_missing_methods(self, issues: list[ValidationIssue], result: ValidationResult) -> None:
        """修复缺失的方法"""
        for issue in issues:
            if "缺少必需的方法" in issue.message:
                try:
                    # 提取类名和方法名
                    # 格式: "组件 MyAction 缺少必需的方法: execute"
                    match = re.search(r'组件\s+(\w+)\s+缺少必需的方法[：:]\s*(\w+)', issue.message)
                    if match:
                        class_name = match.group(1)
                        method_name = match.group(2)
                        file_path = self._resolve_file_path(issue.file_path)
                        
                        if file_path and file_path.exists():
                            before_count = len(self.fixes_applied)
                            self._add_method_to_class(
                                file_path,
                                class_name,
                                method_name,
                                issue
                            )
                            if len(self.fixes_applied) > before_count:
                                self.fixed_issues.append(issue)
                except Exception as e:
                    self.fixes_failed.append(f"修复缺失方法失败: {issue.message} - {e}")

    def _fix_method_signatures(self, issues: list[ValidationIssue], result: ValidationResult) -> None:
        """修复方法签名问题"""
        for issue in issues:
            # 修复异步方法问题
            if "应该是异步方法" in issue.message or "不应该是异步方法" in issue.message:
                try:
                    # 提取类名和方法名
                    match = re.search(r'组件\s+(\w+)\s+的方法\s+(\w+)', issue.message)
                    if match:
                        class_name = match.group(1)
                        method_name = match.group(2)
                        file_path = self._resolve_file_path(issue.file_path)
                        should_be_async = "应该是异步方法" in issue.message
                        
                        if file_path and file_path.exists():
                            before_count = len(self.fixes_applied)
                            self._fix_method_async(
                                file_path,
                                class_name,
                                method_name,
                                should_be_async,
                                issue
                            )
                            if len(self.fixes_applied) > before_count:
                                self.fixed_issues.append(issue)
                except Exception as e:
                    self.fixes_failed.append(f"修复方法签名失败: {issue.message} - {e}")
            
            # 修复参数问题
            elif "缺少必需参数" in issue.message or "参数过多" in issue.message:
                try:
                    match = re.search(r'组件\s+(\w+)\s+的方法\s+(\w+)', issue.message)
                    if match:
                        class_name = match.group(1)
                        method_name = match.group(2)
                        file_path = self._resolve_file_path(issue.file_path)
                        
                        if file_path and file_path.exists() and issue.suggestion:
                            before_count = len(self.fixes_applied)
                            self._fix_method_parameters(
                                file_path,
                                class_name,
                                method_name,
                                issue
                            )
                            if len(self.fixes_applied) > before_count:
                                self.fixed_issues.append(issue)
                except Exception as e:
                    self.fixes_failed.append(f"修复方法参数失败: {issue.message} - {e}")

    def _add_class_attribute(
        self, 
        file_path: Path, 
        field_name: str, 
        issue: ValidationIssue,
        class_name: str | None = None
    ) -> None:
        """添加类属性
        
        Args:
            file_path: 文件路径
            field_name: 字段名
            issue: 验证问题
            class_name: 类名（可选）
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            
            # 查找目标类
            target_class = None
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if class_name is None or node.name == class_name:
                        target_class = node
                        break
            
            if not target_class:
                self.fixes_failed.append(f"未找到类定义: {class_name or '任意类'}")
                return
            
            # 使用 libcst 添加属性
            module = cst.parse_module(source)
            transformer = AddClassAttributeTransformer(
                target_class.name,
                field_name,
                self._get_default_value_for_field(field_name)
            )
            modified = module.visit(transformer)
            
            if transformer.modified:
                file_path.write_text(modified.code, encoding="utf-8")
                self.fixes_applied.append(
                    f"在 {file_path.name} 的类 {target_class.name} 中添加属性 {field_name}"
                )
            else:
                self.fixes_failed.append(f"未能修改类 {target_class.name}")
                
        except Exception as e:
            self.fixes_failed.append(f"添加类属性 {field_name} 失败: {e}")

    def _add_method_to_class(
        self,
        file_path: Path,
        class_name: str,
        method_name: str,
        issue: ValidationIssue
    ) -> None:
        """添加方法到类
        
        Args:
            file_path: 文件路径
            class_name: 类名
            method_name: 方法名
            issue: 验证问题
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            module = cst.parse_module(source)
            
            # 从建议中提取方法模板
            method_template = self._generate_method_template(method_name, issue.suggestion)
            
            transformer = AddMethodTransformer(class_name, method_name, method_template)
            modified = module.visit(transformer)
            
            if transformer.modified:
                file_path.write_text(modified.code, encoding="utf-8")
                self.fixes_applied.append(
                    f"在 {file_path.name} 的类 {class_name} 中添加方法 {method_name}"
                )
            else:
                self.fixes_failed.append(f"未能在类 {class_name} 中添加方法 {method_name}")
                
        except Exception as e:
            self.fixes_failed.append(f"添加方法 {method_name} 失败: {e}")

    def _fix_method_async(
        self,
        file_path: Path,
        class_name: str,
        method_name: str,
        should_be_async: bool,
        issue: ValidationIssue
    ) -> None:
        """修复方法的异步性
        
        Args:
            file_path: 文件路径
            class_name: 类名
            method_name: 方法名
            should_be_async: 是否应该是异步方法
            issue: 验证问题
        """
        try:
            source = file_path.read_text(encoding="utf-8")
            module = cst.parse_module(source)
            
            transformer = FixMethodAsyncTransformer(class_name, method_name, should_be_async)
            modified = module.visit(transformer)
            
            if transformer.modified:
                file_path.write_text(modified.code, encoding="utf-8")
                async_str = "异步" if should_be_async else "同步"
                self.fixes_applied.append(
                    f"修复 {file_path.name} 中 {class_name}.{method_name} 为{async_str}方法"
                )
            else:
                self.fixes_failed.append(f"未能修复方法 {class_name}.{method_name}")
                
        except Exception as e:
            self.fixes_failed.append(f"修复方法异步性失败: {e}")

    def _fix_method_parameters(
        self,
        file_path: Path,
        class_name: str,
        method_name: str,
        issue: ValidationIssue
    ) -> None:
        """修复方法参数
        
        Args:
            file_path: 文件路径
            class_name: 类名
            method_name: 方法名
            issue: 验证问题
        """
        try:
            # 从建议中提取参数列表
            if not issue.suggestion:
                return
            
            # 解析建议中的方法签名
            match = re.search(r'def\s+\w+\(self,\s*([^)]+)\)', issue.suggestion)
            if not match:
                match = re.search(r'应包含[：:]\s*([^。\n]+)', issue.suggestion)
            
            if not match:
                return
            
            params_str = match.group(1).strip()
            
            source = file_path.read_text(encoding="utf-8")
            module = cst.parse_module(source)
            
            transformer = FixMethodParametersTransformer(class_name, method_name, params_str)
            modified = module.visit(transformer)
            
            if transformer.modified:
                file_path.write_text(modified.code, encoding="utf-8")
                self.fixes_applied.append(
                    f"修复 {file_path.name} 中 {class_name}.{method_name} 的参数"
                )
            else:
                self.fixes_failed.append(f"未能修复方法 {class_name}.{method_name} 的参数")
                
        except Exception as e:
            self.fixes_failed.append(f"修复方法参数失败: {e}")

    def _resolve_file_path(self, relative_path: str | None) -> Path | None:
        """解析相对文件路径为绝对路径
        
        Args:
            relative_path: 相对路径
            
        Returns:
            绝对路径
        """
        if not relative_path:
            return None
        
        # 移除插件名前缀
        parts = relative_path.split("/")
        if len(parts) > 1:
            relative_path = "/".join(parts[1:])
        
        return self.plugin_path / relative_path

    def _get_default_value_for_field(self, field_name: str) -> str:
        """获取字段的默认值
        
        Args:
            field_name: 字段名
            
        Returns:
            默认值字符串
        """
        # 根据字段名推断默认值
        name_fields = ['name', 'action_name', 'command_name', 'handler_name', 
                      'adapter_name', 'prompt_name', 'chatter_name', 'component_name']
        desc_fields = ['description', 'action_description', 'command_description',
                      'handler_description', 'adapter_description', 'chatter_description',
                      'component_description']
        
        if field_name in name_fields:
            return f'"{field_name.replace("_", " ").title()}"'
        elif field_name in desc_fields:
            return '"待完善的描述"'
        elif 'version' in field_name.lower():
            return '"0.1.0"'
        elif 'author' in field_name.lower():
            return '""'
        else:
            return '""'

    def _generate_method_template(self, method_name: str, suggestion: str | None) -> str:
        """生成方法模板
        
        Args:
            method_name: 方法名
            suggestion: 建议信息
            
        Returns:
            方法代码模板
        """
        # 从建议中提取方法签名
        if suggestion and "def " in suggestion:
            lines = suggestion.split("\n")
            for line in lines:
                if "def " in line:
                    return line.strip()
        
        # 默认模板
        common_async_methods = ['execute', 'go_activate', 'from_platform_message']
        is_async = method_name in common_async_methods
        
        async_prefix = "async " if is_async else ""
        
        # 根据方法名推断参数
        if method_name == "execute":
            return f'{async_prefix}def execute(self):\n        """执行方法"""\n        raise NotImplementedError'
        elif method_name == "go_activate":
            return f'{async_prefix}def go_activate(self, llm_judge_model=None):\n        """激活判断"""\n        return True'
        elif method_name == "from_platform_message":
            return f'{async_prefix}def from_platform_message(self, raw):\n        """转换平台消息"""\n        raise NotImplementedError'
        elif method_name == "register_endpoints":
            return 'def register_endpoints(self):\n        """注册端点"""\n        pass'
        else:
            return f'{async_prefix}def {method_name}(self):\n        """TODO: 添加方法说明"""\n        raise NotImplementedError'

    def _fix_import_order(self, result: ValidationResult) -> None:
        """修复导入顺序（使用 ruff --fix）"""
        try:
            import subprocess

            # 查找所有 Python 文件
            python_files = list(self.plugin_path.rglob("*.py"))

            for py_file in python_files:
                # 使用 ruff 的 isort 规则修复导入顺序
                proc = subprocess.run(
                    ["ruff", "check", "--select", "I", "--fix", str(py_file)],
                    capture_output=True,
                    check=False  # 不因错误退出而失败
                )
                
            if python_files:
                self.fixes_applied.append("修复导入顺序")

        except Exception:
            # 如果 ruff 未安装，静默失败
            pass


# ============== libcst Transformers ==============

class AddClassAttributeTransformer(cst.CSTTransformer):
    """添加类属性的转换器"""
    
    def __init__(self, class_name: str, attr_name: str, attr_value: str):
        self.class_name = class_name
        self.attr_name = attr_name
        self.attr_value = attr_value
        self.modified = False
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """在类定义中添加属性"""
        if updated_node.name.value != self.class_name:
            return updated_node
        
        # 检查属性是否已存在
        for stmt in updated_node.body.body:
            if isinstance(stmt, cst.SimpleStatementLine):
                for s in stmt.body:
                    if isinstance(s, (cst.Assign, cst.AnnAssign)):
                        target = s.targets[0].target if isinstance(s, cst.Assign) else s.target
                        if isinstance(target, cst.Name) and target.value == self.attr_name:
                            return updated_node  # 属性已存在
        
        # 创建新的赋值语句
        new_assignment = cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=cst.Name(self.attr_name))],
                    value=cst.parse_expression(self.attr_value)
                )
            ]
        )
        
        # 插入到类体开头（在 docstring 之后）
        body_list = list(updated_node.body.body)
        insert_pos = 0
        
        # 跳过 docstring
        if body_list and isinstance(body_list[0], cst.SimpleStatementLine):
            first_stmt = body_list[0].body[0]
            if isinstance(first_stmt, cst.Expr) and isinstance(first_stmt.value, (cst.SimpleString, cst.ConcatenatedString)):
                insert_pos = 1
        
        body_list.insert(insert_pos, new_assignment)
        
        self.modified = True
        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=body_list)
        )


class AddMethodTransformer(cst.CSTTransformer):
    """添加方法的转换器"""
    
    def __init__(self, class_name: str, method_name: str, method_template: str):
        self.class_name = class_name
        self.method_name = method_name
        self.method_template = method_template
        self.modified = False
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """在类中添加方法"""
        if updated_node.name.value != self.class_name:
            return updated_node
        
        # 检查方法是否已存在
        for stmt in updated_node.body.body:
            if isinstance(stmt, (cst.FunctionDef,)):
                if stmt.name.value == self.method_name:
                    return updated_node  # 方法已存在
        
        # 解析方法模板
        try:
            # 将模板包装成完整的类来解析
            full_code = f"class Temp:\n    {self.method_template}"
            temp_module = cst.parse_module(full_code)
            temp_class = temp_module.body[0]
            new_method = temp_class.body.body[0]
            
            # 添加到类体末尾
            body_list = list(updated_node.body.body)
            body_list.append(new_method)
            
            self.modified = True
            return updated_node.with_changes(
                body=updated_node.body.with_changes(body=body_list)
            )
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
    
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        if node.name.value == self.class_name:
            self.in_target_class = True
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            self.in_target_class = False
        return updated_node
    
    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
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
                asynchronous=cst.Asynchronous(
                    whitespace_after=cst.SimpleWhitespace(" ")
                ),
            )
        else:
            # 转换为同步函数（移除 async）
            if isinstance(updated_node, cst.FunctionDef) and updated_node.asynchronous:
                self.modified = True
                return updated_node.with_changes(asynchronous=None)
        
        return updated_node


class FixMethodParametersTransformer(cst.CSTTransformer):
    """修复方法参数的转换器"""
    
    def __init__(self, class_name: str, method_name: str, params_str: str):
        self.class_name = class_name
        self.method_name = method_name
        self.params_str = params_str
        self.modified = False
        self.in_target_class = False
    
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        if node.name.value == self.class_name:
            self.in_target_class = True
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            self.in_target_class = False
        return updated_node
    
    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
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
                                annotation=cst.Annotation(
                                    annotation=cst.parse_expression(type_part.strip())
                                ),
                                default=cst.parse_expression(default_part.strip())
                            )
                        )
                    else:
                        new_params.append(
                            cst.Param(
                                name=cst.Name(param_name),
                                annotation=cst.Annotation(
                                    annotation=cst.parse_expression(type_and_default)
                                )
                            )
                        )
                else:
                    param_name = param.split("=")[0].strip()
                    if "=" in param:
                        default_val = param.split("=")[1].strip()
                        new_params.append(
                            cst.Param(
                                name=cst.Name(param_name),
                                default=cst.parse_expression(default_val)
                            )
                        )
                    else:
                        new_params.append(cst.Param(name=cst.Name(param_name)))
            
            self.modified = True
            return updated_node.with_changes(
                params=updated_node.params.with_changes(params=new_params)
            )
        except Exception:
            return updated_node
"""方法修复器

修复方法相关的问题，包括缺失的方法、方法签名、参数、返回类型等
"""

import re
from pathlib import Path

import libcst as cst

from ..base import BaseFixer, FixResult, ValidationIssue
from .transformers import (
    AddMethodTransformer,
    FixMethodAsyncTransformer,
    FixMethodParametersTransformer,
    FixReturnTypeTransformer,
)


class MethodFixer(BaseFixer):
    """方法修复器"""

    def can_fix(self, issue: ValidationIssue) -> bool:
        """判断是否可以修复

        Args:
            issue: 验证问题

        Returns:
            bool: 是否可以修复
        """
        fixable_patterns = [
            "缺少必需的方法",
            "应该是异步方法",
            "不应该是异步方法",
            "缺少必需参数",
            "参数过多",
            "缺少返回类型注解",
        ]
        return any(pattern in issue.message for pattern in fixable_patterns)

    def fix(self, issues: list[ValidationIssue]) -> FixResult:
        """执行修复

        Args:
            issues: 需要修复的问题列表

        Returns:
            FixResult: 修复结果
        """
        self.result = FixResult(fixer_name=self.__class__.__name__)

        for issue in issues:
            if self.can_fix(issue):
                try:
                    self._fix_method_issue(issue)
                except Exception as e:
                    self.result.add_failure(f"修复方法失败: {issue.message} - {e}")

        return self.result

    def _fix_method_issue(self, issue: ValidationIssue) -> None:
        """修复方法问题

        Args:
            issue: 验证问题
        """
        if "缺少必需的方法" in issue.message:
            self._fix_missing_method(issue)
        elif "应该是异步方法" in issue.message or "不应该是异步方法" in issue.message:
            self._fix_method_async(issue)
        elif "缺少必需参数" in issue.message or "参数过多" in issue.message:
            self._fix_method_parameters(issue)
        elif "缺少返回类型注解" in issue.message:
            self._fix_method_return_type(issue)

    def _fix_missing_method(self, issue: ValidationIssue) -> None:
        """修复缺失的方法

        Args:
            issue: 验证问题
        """
        match = re.search(r"组件\s+(\w+)\s+缺少必需的方法[：:]\s*(\w+)", issue.message)
        if match:
            class_name = match.group(1)
            method_name = match.group(2)
            file_path = self._resolve_file_path(issue.file_path)

            if file_path and file_path.exists():
                self._add_method_to_class(file_path, class_name, method_name, issue)

    def _fix_method_async(self, issue: ValidationIssue) -> None:
        """修复方法的异步性

        Args:
            issue: 验证问题
        """
        match = re.search(r"组件\s+(\w+)\s+的方法\s+(\w+)", issue.message)
        if match:
            class_name = match.group(1)
            method_name = match.group(2)
            file_path = self._resolve_file_path(issue.file_path)
            should_be_async = "应该是异步方法" in issue.message

            if file_path and file_path.exists():
                source = file_path.read_text(encoding="utf-8")
                module = cst.parse_module(source)

                transformer = FixMethodAsyncTransformer(class_name, method_name, should_be_async)
                modified = module.visit(transformer)

                if transformer.modified:
                    file_path.write_text(modified.code, encoding="utf-8")
                    async_str = "异步" if should_be_async else "同步"
                    self.result.add_fix(f"修复 {file_path.name} 中 {class_name}.{method_name} 为{async_str}方法", issue)
                else:
                    self.result.add_failure(f"未能修复方法 {class_name}.{method_name}")

    def _fix_method_parameters(self, issue: ValidationIssue) -> None:
        """修复方法参数

        Args:
            issue: 验证问题
        """
        match = re.search(r"组件\s+(\w+)\s+的方法\s+(\w+)", issue.message)
        if match:
            class_name = match.group(1)
            method_name = match.group(2)
            file_path = self._resolve_file_path(issue.file_path)

            if file_path and file_path.exists() and issue.suggestion:
                # 从建议中提取参数列表
                param_match = re.search(r"def\s+\w+\(self,\s*([^)]+)\)", issue.suggestion)
                if not param_match:
                    param_match = re.search(r"应包含[：:]\s*([^。\n]+)", issue.suggestion)

                if param_match:
                    params_str = param_match.group(1).strip()

                    source = file_path.read_text(encoding="utf-8")
                    module = cst.parse_module(source)

                    transformer = FixMethodParametersTransformer(class_name, method_name, params_str)
                    modified = module.visit(transformer)

                    if transformer.modified:
                        file_path.write_text(modified.code, encoding="utf-8")
                        self.result.add_fix(f"修复 {file_path.name} 中 {class_name}.{method_name} 的参数", issue)
                    else:
                        self.result.add_failure(f"未能修复方法 {class_name}.{method_name} 的参数")

    def _fix_method_return_type(self, issue: ValidationIssue) -> None:
        """修复方法的返回类型注解

        Args:
            issue: 验证问题
        """
        # 尝试匹配两种格式
        plugin_match = re.search(
            r"插件类\s+(\w+)\s+的\s+(\w+)\s+方法缺少返回类型注解，建议添加:\s*->\s*(.+)", issue.message
        )
        component_match = re.search(
            r"组件\s+(\w+)\s+的方法\s+(\w+)\s+缺少返回类型注解，建议添加:\s*->\s*(.+)", issue.message
        )

        if plugin_match:
            class_name = plugin_match.group(1)
            method_name = plugin_match.group(2)
            expected_type = plugin_match.group(3).strip()
            file_path = self.plugin_path / "plugin.py"
        elif component_match:
            class_name = component_match.group(1)
            method_name = component_match.group(2)
            expected_type = component_match.group(3).strip()
            file_path = self._resolve_file_path(issue.file_path)
        else:
            return

        if file_path and file_path.exists():
            source = file_path.read_text(encoding="utf-8")
            module = cst.parse_module(source)

            transformer = FixReturnTypeTransformer(class_name, method_name, expected_type)
            modified = module.visit(transformer)

            if transformer.modified:
                file_path.write_text(modified.code, encoding="utf-8")
                self.result.add_fix(
                    f"修复 {file_path.name} 中 {class_name}.{method_name} 的返回类型注解为 {expected_type}", issue
                )
            else:
                self.result.add_failure(f"未能修复方法 {class_name}.{method_name} 的返回类型")

    def _add_method_to_class(self, file_path: Path, class_name: str, method_name: str, issue: ValidationIssue) -> None:
        """添加方法到类

        Args:
            file_path: 文件路径
            class_name: 类名
            method_name: 方法名
            issue: 验证问题
        """
        source = file_path.read_text(encoding="utf-8")
        module = cst.parse_module(source)

        # 从建议中提取方法模板
        method_template = self._generate_method_template(method_name, issue.suggestion)

        transformer = AddMethodTransformer(class_name, method_name, method_template)
        modified = module.visit(transformer)

        if transformer.modified:
            file_path.write_text(modified.code, encoding="utf-8")
            self.result.add_fix(f"在 {file_path.name} 的类 {class_name} 中添加方法 {method_name}", issue)
        else:
            self.result.add_failure(f"未能在类 {class_name} 中添加方法 {method_name}")

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
        common_async_methods = ["execute", "go_activate", "from_platform_message"]
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

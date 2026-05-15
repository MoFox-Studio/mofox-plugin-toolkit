"""属性修复器

修复类属性相关的问题
"""

import ast
import re
from pathlib import Path

import libcst as cst

from ..base import BaseFixer, FixResult, ValidationIssue
from .transformers import AddClassAttributeTransformer


class AttributeFixer(BaseFixer):
    """类属性修复器"""

    def can_fix(self, issue: ValidationIssue) -> bool:
        """判断是否可以修复

        Args:
            issue: 验证问题

        Returns:
            bool: 是否可以修复
        """
        # 插件类属性
        if any(attr in issue.message for attr in ["plugin_name", "plugin_description", "plugin_version"]):
            if "缺少" in issue.message or "未定义" in issue.message:
                return True

        # 组件类属性
        if "缺少必需的类属性" in issue.message:
            return True

        return False

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
                    self._fix_missing_attribute(issue)
                except Exception as e:
                    self.result.add_failure(f"修复属性失败: {issue.message} - {e}")

        return self.result

    def _fix_missing_attribute(self, issue: ValidationIssue) -> None:
        """修复缺失的属性

        Args:
            issue: 验证问题
        """
        # 插件类属性
        if any(attr in issue.message for attr in ["plugin_name", "plugin_description", "plugin_version"]):
            match = re.search(r"(plugin_name|plugin_description|plugin_version)", issue.message)
            if match:
                attr_name = match.group(1)
                plugin_file = self.plugin_path / "plugin.py"
                if plugin_file.exists():
                    plugin_name = self.plugin_path.name
                    default_value = self._get_default_value_for_plugin_attribute(attr_name, plugin_name)
                    self._add_class_attribute(plugin_file, attr_name, issue, class_name=None, default_value=default_value)

        # 组件类属性
        elif "缺少必需的类属性" in issue.message:
            match = re.search(r"组件\s+(\w+)\s+缺少必需的类属性[：:]\s*(\w+)", issue.message)
            if match:
                class_name = match.group(1)
                field_name = match.group(2)
                file_path = self._resolve_file_path(issue.file_path)

                if file_path and file_path.exists():
                    self._add_class_attribute(file_path, field_name, issue, class_name=class_name)

    def _add_class_attribute(
        self,
        file_path: Path,
        field_name: str,
        issue: ValidationIssue,
        class_name: str | None = None,
        default_value: str | None = None,
    ) -> None:
        """添加类属性

        Args:
            file_path: 文件路径
            field_name: 字段名
            issue: 验证问题
            class_name: 类名（可选）
            default_value: 默认值（可选，如果不提供则自动推断）
        """
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
            self.result.add_failure(f"未找到类定义: {class_name or '任意类'}")
            return

        # 使用 libcst 添加属性
        module = cst.parse_module(source)

        # 使用提供的默认值或自动推断
        attr_value = default_value if default_value is not None else self._get_default_value_for_field(field_name)

        transformer = AddClassAttributeTransformer(target_class.name, field_name, attr_value)
        modified = module.visit(transformer)

        if transformer.modified:
            file_path.write_text(modified.code, encoding="utf-8")
            self.result.add_fix(f"在 {file_path.name} 的类 {target_class.name} 中添加属性 {field_name}", issue)
        else:
            self.result.add_failure(f"未能修改类 {target_class.name}")

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

    def _get_default_value_for_plugin_attribute(self, attr_name: str, plugin_name: str) -> str:
        """获取插件类属性的默认值

        Args:
            attr_name: 属性名
            plugin_name: 插件名称

        Returns:
            默认值字符串
        """
        defaults = {
            "plugin_name": f'"{plugin_name}"',
            "plugin_description": f'"{plugin_name} 插件"',
            "plugin_version": '"1.0.0"',
            "plugin_author": '"Your Name"',
            "configs": "[]",
            "dependent_components": "[]",
        }
        return defaults.get(attr_name, '""')

    def _get_default_value_for_field(self, field_name: str) -> str:
        """获取字段的默认值

        Args:
            field_name: 字段名

        Returns:
            默认值字符串
        """
        # 根据字段名推断默认值
        name_fields = [
            "name",
            "action_name",
            "command_name",
            "handler_name",
            "adapter_name",
            "prompt_name",
            "chatter_name",
            "component_name",
        ]
        desc_fields = [
            "description",
            "action_description",
            "command_description",
            "handler_description",
            "adapter_description",
            "chatter_description",
            "component_description",
        ]

        if field_name in name_fields:
            return f'"{field_name.replace("_", " ").title()}"'
        elif field_name in desc_fields:
            return '"待完善的描述"'
        elif "version" in field_name.lower():
            return '"0.1.0"'
        elif "author" in field_name.lower():
            return '""'
        else:
            return '""'

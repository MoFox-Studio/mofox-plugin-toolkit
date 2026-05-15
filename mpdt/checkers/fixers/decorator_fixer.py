"""装饰器修复器

修复插件类装饰器相关的问题
"""

from pathlib import Path

import libcst as cst

from ..base import BaseFixer, FixResult, ValidationIssue
from .transformers import AddRegisterPluginDecoratorTransformer


class DecoratorFixer(BaseFixer):
    """装饰器修复器"""

    def can_fix(self, issue: ValidationIssue) -> bool:
        """判断是否可以修复

        Args:
            issue: 验证问题

        Returns:
            bool: 是否可以修复
        """
        return "register_plugin" in issue.message and "装饰器" in issue.message

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
                    plugin_file = self.plugin_path / "plugin.py"
                    if plugin_file.exists():
                        self._add_register_decorator(plugin_file, issue)
                except Exception as e:
                    self.result.add_failure(f"添加 @register_plugin 装饰器失败: {e}")

        return self.result

    def _add_register_decorator(self, file_path: Path, issue: ValidationIssue) -> None:
        """为插件类添加 @register_plugin 装饰器

        Args:
            file_path: plugin.py 文件路径
            issue: 验证问题
        """
        source = file_path.read_text(encoding="utf-8")
        module = cst.parse_module(source)

        # 检查是否已有 register_plugin 导入
        has_import = "from src.core.components.loader import register_plugin" in source

        transformer = AddRegisterPluginDecoratorTransformer(has_import=has_import)
        modified = module.visit(transformer)

        if transformer.modified:
            file_path.write_text(modified.code, encoding="utf-8")
            self.result.add_fix("为插件类添加 @register_plugin 装饰器", issue)
        else:
            self.result.add_failure("未能添加 @register_plugin 装饰器")

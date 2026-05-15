"""代码风格修复器

使用 ruff 自动修复代码风格和格式问题
"""

import re
import subprocess

from ..base import BaseFixer, FixResult, ValidationIssue


class StyleFixer(BaseFixer):
    """代码风格修复器"""

    def can_fix(self, issue: ValidationIssue) -> bool:
        """判断是否可以修复

        Args:
            issue: 验证问题

        Returns:
            bool: 是否可以修复
        """
        # ruff 错误格式：字母+数字开头，如 "F401:", "E501:"
        return bool(re.match(r"^[A-Z]\d+:", issue.message))

    def fix(self, issues: list[ValidationIssue]) -> FixResult:
        """执行修复

        Args:
            issues: 需要修复的问题列表

        Returns:
            FixResult: 修复结果
        """
        self.result = FixResult(fixer_name=self.__class__.__name__)

        # 检查是否有代码风格问题
        has_style_issues = any(self.can_fix(issue) for issue in issues)

        if not has_style_issues:
            return self.result

        # 检查 ruff 是否安装
        if not self._is_ruff_installed():
            self.result.add_failure("未安装 ruff，无法自动修复代码风格问题")
            return self.result

        try:
            # 运行 ruff check --fix
            cmd = ["ruff", "check", "--fix", str(self.plugin_path)]
            subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")

            # 运行 ruff format
            cmd_format = ["ruff", "format", str(self.plugin_path)]
            subprocess.run(cmd_format, capture_output=True, text=True, encoding="utf-8", errors="ignore")

            self.result.add_fix("使用 ruff 自动修复了代码风格问题")

        except Exception as e:
            self.result.add_failure(f"运行 ruff 自动修复失败: {e}")

        return self.result

    def _is_ruff_installed(self) -> bool:
        """检查 ruff 是否安装"""
        try:
            subprocess.run(["ruff", "--version"], capture_output=True, check=True, encoding="utf-8", errors="ignore")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

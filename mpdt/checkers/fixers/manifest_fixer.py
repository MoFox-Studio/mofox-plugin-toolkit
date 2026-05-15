"""Manifest 修复器

修复 manifest.json 文件相关的问题
"""

from pathlib import Path

from mpdt.utils.managers.manifest_manager import ManifestManager

from ..base import BaseFixer, FixResult, ValidationIssue


class ManifestFixer(BaseFixer):
    """Manifest 文件修复器"""

    def can_fix(self, issue: ValidationIssue) -> bool:
        """判断是否可以修复

        Args:
            issue: 验证问题

        Returns:
            bool: 是否可以修复
        """
        return "manifest.json" in issue.message and "不存在" in issue.message

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
                    self._create_manifest_file(issue)
                except Exception as e:
                    self.result.add_failure(f"创建 manifest.json 失败: {e}")

        return self.result

    def _create_manifest_file(self, issue: ValidationIssue) -> None:
        """创建 manifest.json 文件

        Args:
            issue: 验证问题
        """
        manifest_manager = ManifestManager(self.plugin_path)

        if manifest_manager.exists:
            return

        # 获取插件名称
        plugin_name = self.plugin_path.name

        # 使用 ManifestManager 创建 manifest
        manifest_manager.create(
            name=plugin_name,
            version="1.0.0",
            description=f"{plugin_name} 插件",
            author="Your Name",
            template="basic",
        )
        manifest_manager.save()

        self.result.add_fix("创建 manifest.json 文件", issue)

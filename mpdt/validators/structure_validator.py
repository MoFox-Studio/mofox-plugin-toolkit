"""
插件结构验证器
"""

from .base import BaseValidator, ValidationResult


class StructureValidator(BaseValidator):
    """插件结构验证器

    检查插件的目录结构和必需文件
    """

    # 必需的文件
    REQUIRED_FILES = ["__init__.py", "plugin.py"]

    # 推荐的文件
    RECOMMENDED_FILES = ["README.md", "pyproject.toml", "requirements.txt"]

    # 推荐的目录
    RECOMMENDED_DIRS = ["tests", "docs"]

    def validate(self) -> ValidationResult:
        """执行结构验证

        Returns:
            ValidationResult: 验证结果
        """
        # 获取插件名称
        plugin_name = self._get_plugin_name()
        if not plugin_name:
            self.result.add_error(
                "无法确定插件名称，请确保插件目录结构正确",
                suggestion="插件应该有 plugin.py 文件",
            )
            return self.result

        # 插件代码目录就是根目录
        plugin_code_dir = self.plugin_path

        # 检查必需的文件
        for file_name in self.REQUIRED_FILES:
            file_path = plugin_code_dir / file_name
            if not file_path.exists():
                self.result.add_error(
                    f"缺少必需文件: {file_name}",
                    file_path=str(file_path.relative_to(self.plugin_path)),
                )

        # 检查推荐的文件
        for file_name in self.RECOMMENDED_FILES:
            file_path = self.plugin_path / file_name
            if not file_path.exists():
                self.result.add_warning(
                    f"缺少推荐文件: {file_name}",
                    file_path=file_name,
                    suggestion=f"建议添加 {file_name} 以提供更好的文档或依赖管理",
                )

        # 检查推荐的目录
        for dir_name in self.RECOMMENDED_DIRS:
            dir_path = self.plugin_path / dir_name
            if not dir_path.exists():
                self.result.add_warning(
                    f"缺少推荐目录: {dir_name}/",
                    file_path=dir_name,
                    suggestion=f"建议添加 {dir_name}/ 目录",
                )

        return self.result

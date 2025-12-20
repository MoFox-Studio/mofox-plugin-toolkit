"""
配置文件验证器
"""

from ..utils.code_parser import CodeParser
from .base import BaseValidator, ValidationResult


class ConfigValidator(BaseValidator):
    """配置文件验证器

    仅检查插件类中定义的 config_schema 是否正确
    不验证 config.toml 文件（因为它会在运行时自动生成）
    """

    def validate(self) -> ValidationResult:
        """执行配置验证

        Returns:
            ValidationResult: 验证结果
        """
        # 获取插件名称
        plugin_name = self._get_plugin_name()
        if not plugin_name:
            self.result.add_error("无法确定插件名称")
            return self.result

        plugin_file = self.plugin_path / "plugin.py"

        if not plugin_file.exists():
            self.result.add_error("插件文件不存在: plugin.py")
            return self.result

        # 解析 plugin.py 查找 config_schema
        config_schema = self._extract_config_schema(plugin_file, plugin_name)

        if config_schema is None:
            # 没有定义 config_schema，这是正常的
            self.result.add_warning(
                "插件未定义配置 schema",
                file_path="plugin.py",
                suggestion="最好定义config_schema启用插件配置系统",                        
            )
            return self.result

        # 验证 config_schema 的结构
        if not config_schema:
            self.result.add_warning(
                "config_schema 已定义但为空",
                file_path="plugin.py",
                suggestion="最好往里面加入一些配置项",
            )
            return self.result

        # 检查是否定义了 config_file_name
        has_config_file_name = self._check_config_file_name(plugin_file, plugin_name)
        if not has_config_file_name:
            self.result.add_warning(
                "定义了 config_schema 但未定义 config_file_name",
                file_path="plugin.py",
                suggestion="请在插件类中添加: config_file_name = 'config.toml'",
            )

        # 验证每个配置节
        for section_name, section_content in config_schema.items():
            if not section_name:
                self.result.add_error(
                    "config_schema 中存在空的配置节名",
                    file_path="plugin.py",
                )
            elif not isinstance(section_content, dict):
                self.result.add_warning(
                    f"config_schema 中的 [{section_name}] 节格式不正确",
                    file_path="plugin.py",
                    suggestion="每个配置节应该是一个字典，包含 ConfigField 定义",
                )

        self.result.add_info(f"config_schema 定义了 {len(config_schema)} 个配置节")
        return self.result

    def _check_config_file_name(self, plugin_file, plugin_name: str) -> bool:
        """检查是否定义了 config_file_name

        Args:
            plugin_file: plugin.py 文件路径
            plugin_name: 插件名称

        Returns:
            是否定义了 config_file_name
        """
        try:
            parser = CodeParser.from_file(plugin_file)
            return parser.has_class_attribute(
                attribute_name="config_file_name",
                base_class="BasePlugin"
            )
        except Exception:
            return False

    def _extract_config_schema(self, plugin_file, plugin_name: str) -> dict | None:
        """从 plugin.py 中提取 config_schema 定义

        Args:
            plugin_file: plugin.py 文件路径
            plugin_name: 插件名称

        Returns:
            config_schema 字典，如果未定义返回 None
        """
        try:
            parser = CodeParser.from_file(plugin_file)
            config_schema = parser.find_class_attribute(
                base_class="BasePlugin",
                attribute_name="config_schema"
            )
            return config_schema
        except Exception as e:
            self.result.add_error(f"解析 plugin.py 失败: {e}")
            return None

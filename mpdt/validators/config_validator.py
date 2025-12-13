"""
配置文件验证器
"""

import ast

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
            self.result.add_info("插件未定义配置 schema")
            return self.result

        # 验证 config_schema 的结构
        if not config_schema:
            self.result.add_warning(
                "config_schema 已定义但为空",
                file_path="plugin.py",
                suggestion="如果不需要配置，可以删除 config_schema 定义",
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
            with open(plugin_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(plugin_file))
        except Exception:
            return False

        # 查找插件类和 config_file_name 定义
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否继承自 BasePlugin
                if any(
                    (isinstance(base, ast.Name) and base.id == "BasePlugin")
                    or (isinstance(base, ast.Attribute) and base.attr == "BasePlugin")
                    for base in node.bases
                ):
                    # 在类中查找 config_file_name
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            if item.target.id == "config_file_name":
                                return True
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name) and target.id == "config_file_name":
                                    return True

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
            with open(plugin_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(plugin_file))
        except Exception as e:
            self.result.add_error(f"解析 plugin.py 失败: {e}")
            return None

        # 查找插件类和 config_schema 定义
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否继承自 BasePlugin
                if any(
                    (isinstance(base, ast.Name) and base.id == "BasePlugin")
                    or (isinstance(base, ast.Attribute) and base.attr == "BasePlugin")
                    for base in node.bases
                ):
                    # 在类中查找 config_schema
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            if item.target.id == "config_schema" and item.value:
                                return self._extract_schema_structure(item.value)
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name) and target.id == "config_schema":
                                    return self._extract_schema_structure(item.value)

        return None

    def _extract_schema_structure(self, node: ast.AST) -> dict:
        """提取 config_schema 的结构（只提取节名）

        Args:
            node: config_schema 的赋值节点

        Returns:
            包含节名的字典
        """
        if isinstance(node, ast.Dict):
            schema = {}
            for key in node.keys:
                if isinstance(key, ast.Constant):
                    section_name = str(key.value)
                    schema[section_name] = {}
                elif isinstance(key, ast.Str):  # Python 3.7 兼容
                    section_name = str(key.s)
                    schema[section_name] = {}
            return schema

        return {}

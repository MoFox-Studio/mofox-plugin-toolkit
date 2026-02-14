"""
配置文件验证器
"""

from pathlib import Path

from ..utils.code_parser import CodeParser
from .base import BaseValidator, ValidationResult


class ConfigValidator(BaseValidator):
    """配置文件验证器

    通过插件类的 configs 属性找到配置类定义，然后验证配置类的结构
    支持配置类在同一文件或不同文件中的情况
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

        # 从插件类中获取 configs 属性
        config_classes = self._extract_config_classes(plugin_file)

        if not config_classes:
            self.result.add_warning(
                "插件未定义配置类",
                file_path="plugin.py",
                suggestion="在插件类中添加 configs = [YourConfigClass] 以启用配置系统",
            )
            return self.result

        self.result.add_info(f"找到 {len(config_classes)} 个配置类: {', '.join(config_classes)}")

        # 验证每个配置类
        for config_class_name in config_classes:
            self._validate_config_class(config_class_name, plugin_file)

        return self.result

    def _extract_config_classes(self, plugin_file: Path) -> list[str]:
        """从插件类中提取 configs 属性

        Args:
            plugin_file: plugin.py 文件路径

        Returns:
            配置类名列表
        """
        try:
            parser = CodeParser.from_file(plugin_file)
            configs_value = parser.find_class_attribute(base_class="BasePlugin", attribute_name="configs")

            if not configs_value:
                return []

            # configs 应该是一个列表
            if not isinstance(configs_value, list):
                self.result.add_error(
                    "configs 属性应该是一个列表",
                    file_path="plugin.py",
                    suggestion="请使用格式: configs = [YourConfigClass]",
                )
                return []

            # 提取配置类名（列表中的每一项应该是类名字符串）
            # 注意：code_parser 会将 [NapcatAdapterConfig] 解析为 [None]（因为是引用而非字面量）
            # 所以我们需要直接解析 AST 来获取类名
            return self._extract_config_class_names_from_ast(plugin_file)

        except Exception as e:
            self.result.add_error(f"解析插件文件失败: {e}")
            return []

    def _extract_config_class_names_from_ast(self, plugin_file: Path) -> list[str]:
        """从 AST 中提取 configs 列表中的类名

        Args:
            plugin_file: plugin.py 文件路径

        Returns:
            配置类名列表
        """
        try:
            import libcst as cst

            parser = CodeParser.from_file(plugin_file)
            classes = parser.find_class(base_class="BasePlugin")

            if not classes:
                return []

            # 在插件类中查找 configs 属性
            for cls in classes:
                for statement in cls.body.body:
                    if isinstance(statement, cst.SimpleStatementLine):
                        for node in statement.body:
                            # 查找 configs = [...]
                            if isinstance(node, cst.Assign):
                                for target in node.targets:
                                    if isinstance(target.target, cst.Name) and target.target.value == "configs":
                                        # 提取列表中的类名
                                        if isinstance(node.value, cst.List):
                                            names = []
                                            for element in node.value.elements:
                                                if isinstance(element, cst.Element):
                                                    if isinstance(element.value, cst.Name):
                                                        names.append(element.value.value)
                                            return names

            return []

        except Exception as e:
            self.result.add_error(f"提取配置类名失败: {e}")
            return []

    def _validate_config_class(self, config_class_name: str, plugin_file: Path) -> None:
        """验证配置类的结构

        Args:
            config_class_name: 配置类名
            plugin_file: plugin.py 文件路径
        """
        # 查找配置类定义的位置
        config_file = self._find_config_class_file(config_class_name, plugin_file)

        if not config_file:
            self.result.add_error(
                f"无法找到配置类 {config_class_name} 的定义",
                file_path="plugin.py",
                suggestion=f"请确保 {config_class_name} 已定义或正确导入",
            )
            return

        # 解析配置类文件
        try:
            parser = CodeParser.from_file(config_file)

            # 检查配置类是否继承 BaseConfig
            classes = parser.find_class(class_name=config_class_name, base_class="BaseConfig")
            if not classes:
                self.result.add_error(
                    f"配置类 {config_class_name} 未继承 BaseConfig",
                    file_path=config_file.name,
                    suggestion=f"请确保 {config_class_name} 继承自 BaseConfig",
                )
                return

            # 检查是否定义了 config_name
            config_name = parser.find_class_attribute(
                class_name=config_class_name,
                attribute_name="config_name",
            )
            if not config_name:
                self.result.add_warning(
                    f"配置类 {config_class_name} 未定义 config_name",
                    file_path=config_file.name,
                    suggestion="建议添加 config_name: ClassVar[str] = 'config' 以指定配置文件名",
                )

            # 检查是否定义了配置节（嵌套类）
            config_sections = self._find_config_sections(parser, config_class_name)
            if not config_sections:
                self.result.add_warning(
                    f"配置类 {config_class_name} 未定义任何配置节",
                    file_path=config_file.name,
                    suggestion="建议使用 @config_section 装饰器定义配置节",
                )
            else:
                self.result.add_info(
                    f"配置类 {config_class_name} 定义了 {len(config_sections)} 个配置节: {', '.join(config_sections)}"
                )

            # 验证每个配置节
            for section_name in config_sections:
                self._validate_config_section(parser, config_class_name, section_name, config_file)

        except Exception as e:
            self.result.add_error(f"验证配置类 {config_class_name} 失败: {e}")

    def _find_config_class_file(self, config_class_name: str, plugin_file: Path) -> Path | None:
        """查找配置类定义的文件位置

        Args:
            config_class_name: 配置类名
            plugin_file: plugin.py 文件路径

        Returns:
            配置类文件路径，未找到返回 None
        """
        # 1. 首先在 plugin.py 中查找
        try:
            parser = CodeParser.from_file(plugin_file)
            classes = parser.find_class(class_name=config_class_name)
            if classes:
                return plugin_file
        except Exception:
            pass

        # 2. 查找 import 语句，确定配置类从哪里导入
        try:
            parser = CodeParser.from_file(plugin_file)
            imported_names = parser.get_imported_names()

            if config_class_name in imported_names:
                module_name = imported_names[config_class_name]
                # 将模块名转换为文件路径（相对于插件目录）
                # 例如：.config -> config.py
                if module_name.startswith("."):
                    # 相对导入
                    module_path = module_name[1:].replace(".", "/") + ".py"
                    config_file = self.plugin_path / module_path
                    if config_file.exists():
                        return config_file
        except Exception:
            pass

        # 3. 在插件目录中搜索所有 .py 文件
        for py_file in self.plugin_path.glob("**/*.py"):
            if py_file.name == "__init__.py":
                continue
            try:
                parser = CodeParser.from_file(py_file)
                classes = parser.find_class(class_name=config_class_name)
                if classes:
                    return py_file
            except Exception:
                continue

        return None

    def _find_config_sections(self, parser: CodeParser, config_class_name: str) -> list[str]:
        """查找配置类中定义的配置节（嵌套类）

        Args:
            parser: 代码解析器
            config_class_name: 配置类名

        Returns:
            配置节名称列表
        """
        try:
            import libcst as cst

            classes = parser.find_class(class_name=config_class_name)
            if not classes:
                return []

            sections = []
            for cls in classes:
                for statement in cls.body.body:
                    # 查找嵌套类定义
                    if isinstance(statement, cst.ClassDef):
                        # 检查是否继承 SectionBase
                        for base in statement.bases:
                            if isinstance(base.value, cst.Name) and base.value.value == "SectionBase":
                                sections.append(statement.name.value)
                                break

            return sections

        except Exception:
            return []

    def _validate_config_section(
        self, parser: CodeParser, config_class_name: str, section_name: str, config_file: Path
    ) -> None:
        """验证配置节的结构

        Args:
            parser: 代码解析器
            config_class_name: 配置类名
            section_name: 配置节名称
            config_file: 配置文件路径
        """
        try:
            import libcst as cst

            classes = parser.find_class(class_name=config_class_name)
            if not classes:
                return

            # 查找配置节类
            for cls in classes:
                for statement in cls.body.body:
                    if isinstance(statement, cst.ClassDef) and statement.name.value == section_name:
                        # 检查配置节中是否有字段定义
                        has_fields = False
                        for nested_statement in statement.body.body:
                            if isinstance(nested_statement, cst.SimpleStatementLine):
                                for node in nested_statement.body:
                                    # 查找带类型注解的赋值（字段定义）
                                    if isinstance(node, cst.AnnAssign):
                                        has_fields = True
                                        break
                            if has_fields:
                                break

                        if not has_fields:
                            self.result.add_warning(
                                f"配置节 {section_name} 未定义任何字段",
                                file_path=config_file.name,
                                suggestion=f"在 {section_name} 中添加字段定义，使用 Field() 指定默认值和描述",
                            )

        except Exception as e:
            self.result.add_warning(f"验证配置节 {section_name} 失败: {e}")

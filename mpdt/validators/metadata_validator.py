"""
插件元数据验证器
"""

from ..utils.code_parser import CodeParser
from .base import BaseValidator, ValidationResult


class MetadataValidator(BaseValidator):
    """插件元数据验证器

    检查 plugin.py 中的 PluginMetadata 是否完整
    """

    # 必需的元数据字段
    REQUIRED_FIELDS = ["name", "description", "usage"]

    # 推荐的元数据字段
    RECOMMENDED_FIELDS = ["version", "author", "license"]

    def validate(self) -> ValidationResult:
        """执行元数据验证

        Returns:
            ValidationResult: 验证结果
        """
        # 获取插件名称
        plugin_name = self._get_plugin_name()
        if not plugin_name:
            self.result.add_error("无法确定插件名称")
            return self.result

        # 元数据在 __init__.py 中
        init_file = self.plugin_path / "__init__.py"
        if not init_file.exists():
            self.result.add_error(
                "__init__.py 文件不存在",
                suggestion="请创建 __init__.py 文件并定义 __plugin_meta__",
            )
            return self.result

        # 使用 CodeParser 解析
        try:
            parser = CodeParser.from_file(init_file)
        except SyntaxError as e:
            self.result.add_error(
                f"__init__.py 存在语法错误: {e.msg}",
                file_path="__init__.py",
                line_number=e.lineno if hasattr(e, 'lineno') else None,
            )
            return self.result
        except Exception as e:
            self.result.add_error(f"读取 __init__.py 失败: {e}")
            return self.result

        # 查找 __plugin_meta__ 赋值
        metadata_values = parser.find_assignments("__plugin_meta__")
        
        if not metadata_values:
            self.result.add_error(
                "未找到 __plugin_meta__ 变量或 PluginMetadata 实例",
                file_path="__init__.py",
                suggestion="请在 __init__.py 中定义: __plugin_meta__ = PluginMetadata(...)",
            )
            return self.result

        # 使用增强的 CodeParser 解析 PluginMetadata 的参数
        metadata_args = parser.find_call_arguments("__plugin_meta__", "PluginMetadata")
        
        if metadata_args is None:
            self.result.add_error(
                "未找到 __plugin_meta__ 的 PluginMetadata 调用",
                file_path="__init__.py",
                suggestion="请使用 PluginMetadata(...) 构造 __plugin_meta__",
            )
            return self.result

        self.result.add_info("找到 __plugin_meta__ 定义")

        # 检查必需字段
        missing_required = parser.get_missing_call_arguments(
            "__plugin_meta__", 
            self.REQUIRED_FIELDS,
            "PluginMetadata"
        )
        
        if missing_required:
            for field in missing_required:
                self.result.add_error(
                    f"PluginMetadata 缺少必需字段: {field}",
                    file_path="__init__.py",
                    suggestion=f"请在 PluginMetadata 中添加 {field}=\"...\" 参数",
                )
        else:
            self.result.add_info("所有必需的元数据字段都已提供")

        # 检查推荐字段
        missing_recommended = []
        for field in self.RECOMMENDED_FIELDS:
            if field not in metadata_args or not metadata_args[field]:
                missing_recommended.append(field)
        
        if missing_recommended:
            self.result.add_warning(
                f"建议添加以下元数据字段: {', '.join(missing_recommended)}",
                file_path="__init__.py",
                suggestion=f"在 PluginMetadata 中添加: {', '.join(f'{f}=\"...\"' for f in missing_recommended)}",
            )

        return self.result

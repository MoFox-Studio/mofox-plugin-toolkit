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

        # 元数据应该是一个字典（通过 PluginMetadata 构造）
        # 由于我们的 CodeParser 不能轻易提取函数调用的参数
        # 我们只能做基础检查，标记为已找到
        self.result.add_info("找到 __plugin_meta__ 定义")
        self.result.add_info("注意: 详细的元数据字段验证需要运行时检查")

        return self.result

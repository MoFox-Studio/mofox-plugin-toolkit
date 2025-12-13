"""
插件元数据验证器
"""

import ast

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

        # 读取并解析 __init__.py
        try:
            with open(init_file, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(init_file))
        except SyntaxError as e:
            self.result.add_error(
                f"__init__.py 存在语法错误: {e.msg}",
                file_path="__init__.py",
                line_number=e.lineno,
            )
            return self.result
        except Exception as e:
            self.result.add_error(f"读取 __init__.py 失败: {e}")
            return self.result

        # 查找 __plugin_meta__ 变量赋值
        metadata_found = False
        metadata_node = None

        for node in ast.walk(tree):
            # 查找 __plugin_meta__ = PluginMetadata(...) 赋值
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__plugin_meta__":
                        if isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Name) and node.value.func.id == "PluginMetadata":
                                metadata_found = True
                                metadata_node = node.value
                                break

        if not metadata_found:
            self.result.add_error(
                "未找到 __plugin_meta__ 变量或 PluginMetadata 实例",
                file_path="__init__.py",
                suggestion="请在 __init__.py 中定义: __plugin_meta__ = PluginMetadata(...)",
            )
            return self.result

        # 提取元数据字段
        metadata_fields = {}
        if metadata_node:
            # 处理关键字参数
            for keyword in metadata_node.keywords:
                if keyword.arg:
                    # 尝试获取值
                    value = self._extract_value(keyword.value)
                    metadata_fields[keyword.arg] = value

        # 检查必需字段
        for field in self.REQUIRED_FIELDS:
            if field not in metadata_fields:
                self.result.add_error(
                    f"PluginMetadata 缺少必需字段: {field}",
                    file_path="__init__.py",
                )
            elif not metadata_fields[field]:
                self.result.add_warning(
                    f"PluginMetadata 字段 {field} 为空",
                    file_path="__init__.py",
                )

        # 检查推荐字段
        for field in self.RECOMMENDED_FIELDS:
            if field not in metadata_fields:
                self.result.add_warning(
                    f"PluginMetadata 缺少推荐字段: {field}",
                    file_path="__init__.py",
                    suggestion=f"建议添加 {field} 字段",
                )

        return self.result

    def _extract_value(self, node: ast.AST) -> str | None:
        """提取 AST 节点的值"""
        if isinstance(node, ast.Constant):
            return str(node.value) if node.value else None
        elif isinstance(node, ast.Str):  # Python 3.7 兼容
            return str(node.s) if node.s else None
        elif isinstance(node, ast.List):
            return "[...]"  # 列表类型
        elif isinstance(node, ast.Dict):
            return "{...}"  # 字典类型
        return None

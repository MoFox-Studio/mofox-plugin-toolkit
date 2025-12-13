"""自动修复验证器

提供自动修复常见问题的功能
"""

import ast
from pathlib import Path

from .base import BaseValidator, ValidationResult


class AutoFixValidator(BaseValidator):
    """自动修复验证器

    自动修复插件中的常见问题
    """

    def __init__(self, plugin_path: Path):
        super().__init__(plugin_path)
        self.fixes_applied = []

    def validate(self) -> ValidationResult:
        """执行自动修复（实际上是 fix 而非 validate）"""
        result = ValidationResult(
            validator_name="AutoFixValidator",
            success=True
        )

        plugin_name = self._get_plugin_name()
        if not plugin_name:
            result.add_error("无法确定插件名称")
            return result

        # 修复缺失的元数据
        self._fix_missing_metadata(result)

        # 修复导入顺序
        self._fix_import_order(result)

        # 汇总修复结果
        if self.fixes_applied:
            result.add_info(f"应用了 {len(self.fixes_applied)} 个自动修复")
            for fix in self.fixes_applied:
                result.add_info(fix)
        else:
            result.add_info("未发现可自动修复的问题")

        return result

    def _fix_missing_metadata(self, result: ValidationResult) -> None:
        """修复缺失的元数据字段"""
        init_file = self.plugin_path / "__init__.py"
        if not init_file.exists():
            return

        try:
            content = init_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            # 查找 __plugin_meta__ 定义
            meta_found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__plugin_meta__":
                            meta_found = True
                            break

            if not meta_found:
                # 添加基本的 __plugin_meta__ 定义
                plugin_name = self._get_plugin_name()
                meta_template = f'''
from src.plugin_system import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="{plugin_name}",
    description="插件描述",
    usage="插件使用说明",
    version="0.1.0",
    author="",
    license="MIT"
)
'''
                # 在文件开头添加
                new_content = meta_template + "\n" + content
                init_file.write_text(new_content, encoding="utf-8")
                self.fixes_applied.append("添加缺失的 __plugin_meta__ 定义到 __init__.py")

        except Exception as e:
            result.add_warning(f"无法自动修复元数据: {e}")

    def _fix_import_order(self, result: ValidationResult) -> None:
        """修复导入顺序（使用 ruff --fix）"""
        try:
            import subprocess

            # 查找所有 Python 文件
            python_files = list(self.plugin_path.rglob("*.py"))

            for py_file in python_files:
                # 使用 ruff 的 isort 规则修复导入顺序
                subprocess.run(
                    ["ruff", "check", "--select", "I", "--fix", str(py_file)],
                    capture_output=True,
                    check=False  # 不因错误退出而失败
                )

            self.fixes_applied.append("修复导入顺序")

        except Exception:
            # 如果 ruff 未安装，静默失败
            pass

    def fix_component_metadata(self, component_file: Path, component_class: str, missing_fields: list[str]) -> bool:
        """修复组件缺失的元数据字段

        Args:
            component_file: 组件文件路径
            component_class: 组件类名
            missing_fields: 缺失的字段列表

        Returns:
            是否成功修复
        """
        try:
            content = component_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            # 查找组件类
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == component_class:
                    # 在类定义中添加缺失的字段
                    indent = "    "  # 4 个空格缩进
                    fields_to_add = []

                    for field in missing_fields:
                        # 根据字段类型生成默认值
                        if field.endswith("_name"):
                            value = f'"{component_class.lower().replace("_", "-")}"'
                        elif field.endswith("_description"):
                            value = f'"{component_class} 组件"'
                        else:
                            value = '""'

                        fields_to_add.append(f"{indent}{field}: str = {value}")

                    # 找到类体的第一行（文档字符串后）
                    lines = content.split('\n')
                    class_line = None
                    for i, line in enumerate(lines):
                        if f"class {component_class}" in line:
                            class_line = i
                            break

                    if class_line is not None:
                        # 找到插入位置（类定义后，第一个方法前）
                        insert_line = class_line + 1

                        # 跳过文档字符串
                        if insert_line < len(lines) and '"""' in lines[insert_line]:
                            while insert_line < len(lines) and not lines[insert_line].strip().endswith('"""'):
                                insert_line += 1
                            insert_line += 1

                        # 插入字段
                        for field_def in fields_to_add:
                            lines.insert(insert_line, field_def)
                            insert_line += 1

                        # 写回文件
                        new_content = '\n'.join(lines)
                        component_file.write_text(new_content, encoding="utf-8")

                        self.fixes_applied.append(
                            f"为 {component_class} 添加缺失的元数据字段: {', '.join(missing_fields)}"
                        )
                        return True

            return False

        except Exception:
            return False

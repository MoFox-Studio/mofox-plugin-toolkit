"""
导入规范验证器模块

该模块提供导入规范验证功能，用于检查插件内部是否错误地使用了绝对导入。
主要验证内容包括：
- 检测插件内部文件是否使用了 from plugin_name.xxx import xxx 形式的导入
- 这种导入应该改为相对导入（如 from .xxx import xxx 或 from ..xxx import xxx）
"""

from pathlib import Path

from ...utils.code_parser import CodeParser
from ..base import BaseValidator, ValidationLevel, ValidationResult


class ImportValidator(BaseValidator):
    """导入规范验证器类

    该验证器负责检查插件内部文件是否使用了不规范的绝对导入。
    在插件内部，应该使用相对导入而不是绝对导入，以避免：
    - 插件名称变更时需要修改大量导入语句
    - 可能与其他插件产生命名冲突
    - 降低代码的可移植性

    验证流程：
    1. 获取插件名称
    2. 递归扫描插件目录下所有 .py 文件
    3. 对每个文件检查是否有 from plugin_name.xxx import xxx 形式的导入
    4. 记录所有不规范的导入位置
    """

    def validate(self) -> ValidationResult:
        """执行导入规范验证流程

        Returns:
            ValidationResult: 验证结果对象，包含所有错误、警告和建议
        """
        # 获取插件名称
        plugin_name = self._get_plugin_name()
        if not plugin_name:
            self.result.add_error(
                message="无法获取插件名称，跳过导入检查",
            )
            return self.result

        plugin_dir = self.plugin_path

        # 递归扫描所有 Python 文件
        python_files = list(plugin_dir.rglob("*.py"))

        if not python_files:
            self.result.add_error(
                message="未找到任何 Python 文件",
            )
            return self.result

        # 检查每个文件
        for py_file in python_files:
            self._check_file_imports(py_file, plugin_name, plugin_dir)

        return self.result

    def _check_file_imports(self, file_path: Path, plugin_name: str, plugin_dir: Path) -> None:
        """检查单个文件中的导入语句

        Args:
            file_path: Python 文件路径
            plugin_name: 插件名称
            plugin_dir: 插件根目录路径
        """
        try:
            parser = CodeParser.from_file(file_path)
        except Exception as e:
            self.result.add_error(
                message=f"无法解析文件: {e}",
                file_path=str(file_path.relative_to(plugin_dir)),
            )
            return

        # 查找所有 from import 语句
        all_imports = parser.find_imports()

        for import_info in all_imports:
            # 只检查 from import 语句
            if import_info["type"] != "from_import":
                continue

            module = import_info.get("module", "")

            # 检查是否是插件内部的绝对导入
            if module.startswith(f"{plugin_name}.") or module == plugin_name:
                # 计算应该使用的相对导入路径
                suggested_import = self._suggest_relative_import(
                    file_path, module, plugin_name, plugin_dir
                )

                relative_path = file_path.relative_to(plugin_dir)
                imported_names = ", ".join(import_info.get("names", []))

                self.result.add_error(
                    message=f"插件内部使用了绝对导入: from {module} import {imported_names}",
                    file_path=str(relative_path),
                    suggestion=f"应该使用相对导入: {suggested_import}",
                )

    def _suggest_relative_import(
        self, file_path: Path, module: str, plugin_name: str, plugin_dir: Path
    ) -> str:
        """根据文件位置和导入模块，建议使用的相对导入路径

        Args:
            file_path: 当前文件路径
            module: 原始导入模块名（如 plugin_name.components.actions）
            plugin_name: 插件名称
            plugin_dir: 插件根目录

        Returns:
            建议的相对导入语句字符串
        """
        # 移除插件名称前缀，获取相对模块路径
        if module == plugin_name:
            relative_module = ""
        else:
            relative_module = module[len(plugin_name) + 1 :]  # +1 for the dot

        # 获取当前文件相对于插件根目录的路径
        file_relative = file_path.relative_to(plugin_dir)
        current_dir = file_relative.parent

        # 计算从当前目录到目标模块的相对路径
        if not relative_module:
            # 如果导入的是插件根目录，需要向上导航
            dots = "." * (len(current_dir.parts) + 1)
            return f"from {dots} import ..."
        else:
            # 将模块路径转换为路径对象
            module_parts = relative_module.split(".")
            target_path = Path(*module_parts)

            # 如果目标模块在当前目录
            if not current_dir.parts:
                # 当前文件在根目录
                return f"from .{relative_module} import ..."
            
            # 如果目标模块在当前目录的子目录
            if str(target_path).startswith(str(current_dir)):
                # 计算相对路径
                try:
                    rel_path = target_path.relative_to(current_dir)
                    return f"from .{'.'.join(rel_path.parts)} import ..."
                except ValueError:
                    pass

            # 如果目标模块在父目录或兄弟目录
            # 计算需要向上的层级
            common_parts = 0
            for i, part in enumerate(current_dir.parts):
                if i < len(module_parts) and part == module_parts[i]:
                    common_parts += 1
                else:
                    break

            # 计算向上的层级数（当前层 + 需要向上的层数）
            up_levels = len(current_dir.parts) - common_parts + 1
            dots = "." * up_levels

            # 计算剩余的模块路径
            remaining_parts = module_parts[common_parts:]
            if remaining_parts:
                return f"from {dots}{'.'.join(remaining_parts)} import ..."
            else:
                return f"from {dots} import ..."

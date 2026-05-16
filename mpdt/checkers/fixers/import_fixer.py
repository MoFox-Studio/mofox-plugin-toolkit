"""
导入规范修复器模块

该模块提供导入规范自动修复功能，用于将插件内部的绝对导入转换为相对导入。
"""

from pathlib import Path

import libcst as cst

from ...utils.code_parser import CodeParser
from ..base import BaseFixer, FixResult, ValidationIssue


class ImportFixer(BaseFixer):
    """导入规范修复器类

    该修复器负责自动修复插件内部使用绝对导入的问题，将其转换为相对导入。

    修复策略：
    1. 解析文件的 CST（保留格式和注释）
    2. 找到所有 from plugin_name.xxx import yyy 形式的导入
    3. 计算正确的相对导入路径
    4. 替换导入语句
    5. 保存修改后的文件
    """

    def can_fix(self, issue: ValidationIssue) -> bool:
        """判断是否可以修复某个问题

        Args:
            issue: 验证问题

        Returns:
            bool: 是否可以修复
        """
        # 检查是否是导入相关的问题
        return "插件内部使用了绝对导入" in issue.message

    def fix(self, issues: list[ValidationIssue]) -> FixResult:
        """执行导入修复

        Args:
            issues: 验证问题列表

        Returns:
            FixResult: 修复结果对象
        """
        result = FixResult(fixer_name="ImportFixer")

        # 获取插件名称
        plugin_name = self._get_plugin_name()
        if not plugin_name:
            result.add_failure("无法获取插件名称，无法执行导入修复")
            return result

        plugin_dir = self.plugin_path

        # 按文件分组问题
        issues_by_file: dict[str, list[ValidationIssue]] = {}
        for issue in issues:
            if issue.file_path:
                issues_by_file.setdefault(issue.file_path, []).append(issue)

        # 处理每个文件
        for relative_path, file_issues in issues_by_file.items():
            file_path = plugin_dir / relative_path
            if not file_path.exists():
                result.add_failure(f"{relative_path}: 文件不存在")
                continue

            try:
                self._fix_file_imports(file_path, plugin_name, plugin_dir, result, file_issues)
            except Exception as e:
                import traceback
                result.add_failure(f"{relative_path}: 修复失败: {e}\n{traceback.format_exc()}")

        return result

    def _fix_file_imports(
        self, file_path: Path, plugin_name: str, plugin_dir: Path, result: FixResult,
        file_issues: list[ValidationIssue]
    ) -> None:
        """修复单个文件中的导入语句

        Args:
            file_path: Python 文件路径
            plugin_name: 插件名称
            plugin_dir: 插件根目录路径
            result: 修复结果对象
            file_issues: 该文件的问题列表
        """
        try:
            parser = CodeParser.from_file(file_path)
        except Exception as e:
            result.add_failure(f"{file_path.relative_to(plugin_dir)}: 无法解析文件: {e}")
            return

        # 创建转换器
        transformer = ImportTransformer(file_path, plugin_name, plugin_dir)
        
        try:
            modified_tree = parser.module.visit(transformer)
        except Exception as e:
            import traceback
            result.add_failure(
                f"{file_path.relative_to(plugin_dir)}: CST转换失败: {e}\n{traceback.format_exc()}"
            )
            return

        # 检查是否有修改
        if not transformer.changes_made:
            return

        # 保存修改后的文件
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_tree.code)

            relative_path = file_path.relative_to(plugin_dir)
            # 记录修复的导入语句
            for old_import, new_import in transformer.fixed_imports:
                result.add_fix(
                    f"{relative_path}: {old_import} -> {new_import}"
                )
            
            # 将修复的问题添加到 fixed_issues 列表
            for issue in file_issues:
                result.add_fix(
                    f"{relative_path}: 已修复导入问题",
                    issue=issue
                )
        except Exception as e:
            import traceback
            result.add_failure(
                f"{file_path.relative_to(plugin_dir)}: 保存文件失败: {e}\n{traceback.format_exc()}"
            )


class ImportTransformer(cst.CSTTransformer):
    """导入语句转换器

    使用 libcst 的转换器模式，遍历 CST 并修改导入语句。
    """

    def __init__(self, file_path: Path, plugin_name: str, plugin_dir: Path):
        """初始化转换器

        Args:
            file_path: 当前处理的文件路径
            plugin_name: 插件名称
            plugin_dir: 插件根目录路径
        """
        self.file_path = file_path
        self.plugin_name = plugin_name
        self.plugin_dir = plugin_dir
        self.changes_made = False
        self.fixed_imports: list[tuple[str, str]] = []  # (原导入, 新导入) 列表

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ) -> cst.ImportFrom:
        """处理 from import 语句

        Args:
            original_node: 原始节点
            updated_node: 更新后的节点

        Returns:
            修改后的节点（如果需要修改）或原节点
        """
        # 获取模块名
        if updated_node.module is None:
            return updated_node

        module_name = self._get_module_name(updated_node.module)

        # 检查是否是插件内部的绝对导入
        if not (module_name.startswith(f"{self.plugin_name}.") or module_name == self.plugin_name):
            return updated_node

        # 计算相对导入路径
        relative_import = self._calculate_relative_import(module_name)

        if relative_import is None:
            return updated_node

        # 记录修改
        old_import = self._format_import(module_name, updated_node)
        new_import = self._format_import(relative_import, updated_node)
        self.fixed_imports.append((old_import, new_import))
        self.changes_made = True

        # 创建新的导入节点
        # 解析相对导入路径，计算点号数量和剩余模块路径
        dots_count = 0
        for char in relative_import:
            if char == ".":
                dots_count += 1
            else:
                break

        remaining_module = relative_import[dots_count:]

        # 创建相对导入
        if remaining_module:
            # 有剩余模块路径，如 from ..components.actions import xxx
            new_module = self._build_module_node(remaining_module)
        else:
            # 只有点号，如 from .. import xxx
            new_module = None

        new_node = updated_node.with_changes(
            module=new_module,
            relative=[cst.Dot() for _ in range(dots_count)],
        )

        return new_node

    def _get_module_name(self, module_node: cst.BaseExpression) -> str:
        """从 CST 节点提取模块名称

        Args:
            module_node: 模块节点

        Returns:
            模块名称字符串
        """
        if isinstance(module_node, cst.Name):
            return module_node.value
        elif isinstance(module_node, cst.Attribute):
            return CodeParser.get_dotted_name(module_node)
        return ""

    def _calculate_relative_import(self, module: str) -> str | None:
        """计算相对导入路径

        Args:
            module: 原始绝对导入模块名

        Returns:
            相对导入路径字符串（如 "..components.actions"），失败返回 None
        """
        # 移除插件名称前缀
        if module == self.plugin_name:
            relative_module = ""
        else:
            relative_module = module[len(self.plugin_name) + 1 :]

        # 获取当前文件相对于插件根目录的路径
        file_relative = self.file_path.relative_to(self.plugin_dir)
        current_dir = file_relative.parent

        # 计算相对路径
        if not relative_module:
            # 导入插件根目录
            dots = "." * (len(current_dir.parts) + 1)
            return dots.rstrip(".")  # 移除末尾的点

        # 将模块路径转换为路径对象
        module_parts = relative_module.split(".")
        target_path = Path(*module_parts)

        # 如果当前文件在根目录
        if not current_dir.parts:
            return f".{relative_module}"

        # 如果目标模块在当前目录的子目录
        if str(target_path).startswith(str(current_dir)):
            try:
                rel_path = target_path.relative_to(current_dir)
                return f".{'.'.join(rel_path.parts)}"
            except ValueError:
                pass

        # 如果目标模块在父目录或兄弟目录
        # 计算共同的父目录
        common_parts = 0
        for i, part in enumerate(current_dir.parts):
            if i < len(module_parts) and part == module_parts[i]:
                common_parts += 1
            else:
                break

        # 计算向上的层级数
        up_levels = len(current_dir.parts) - common_parts + 1
        dots = "." * up_levels

        # 计算剩余的模块路径
        remaining_parts = module_parts[common_parts:]
        if remaining_parts:
            return f"{dots}{'.'.join(remaining_parts)}"
        else:
            return dots.rstrip(".")

    def _build_module_node(self, module_path: str) -> cst.BaseExpression:
        """构建模块路径的 CST 节点

        Args:
            module_path: 模块路径字符串（如 "components.actions"）

        Returns:
            CST 节点
        """
        parts = module_path.split(".")
        if len(parts) == 1:
            return cst.Name(parts[0])

        # 构建嵌套的 Attribute 节点
        node = cst.Name(parts[0])
        for part in parts[1:]:
            node = cst.Attribute(value=node, attr=cst.Name(part))
        return node

    def _build_dotted_name(self, name: str) -> cst.BaseExpression:
        """构建点号分隔的名称节点（辅助方法）"""
        return self._build_module_node(name)

    def _format_import(self, module: str, node: cst.ImportFrom) -> str:
        """格式化导入语句为字符串（用于记录）

        Args:
            module: 模块名
            node: 导入节点

        Returns:
            格式化的导入语句字符串
        """
        # 提取导入的名称
        names = []
        if isinstance(node.names, cst.ImportStar):
            names_str = "*"
        else:
            for name in node.names:
                if isinstance(name, cst.ImportAlias):
                    names.append(name.name.value)
            names_str = ", ".join(names)

        return f"from {module} import {names_str}"

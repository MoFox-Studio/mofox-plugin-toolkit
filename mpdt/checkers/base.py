"""
验证器基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..utils.plugin_parser import extract_plugin_name


class ValidationLevel(str, Enum):
    """验证级别"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """验证问题"""

    level: ValidationLevel
    message: str
    file_path: str | None = None
    line_number: int | None = None
    suggestion: str | None = None


@dataclass
class ValidationResult:
    """验证结果"""

    validator_name: str
    issues: list[ValidationIssue] = field(default_factory=list)
    success: bool = True
    fixes_applied: list[str] = field(default_factory=list)
    fixes_failed: list[str] = field(default_factory=list)
    fixed_issues: list[ValidationIssue] = field(default_factory=list)

    def add_error(self, message: str, file_path: str | None = None, line_number: int | None = None, suggestion: str | None = None) -> None:
        """添加错误"""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.ERROR,
                message=message,
                file_path=file_path,
                line_number=line_number,
                suggestion=suggestion,
            )
        )
        self.success = False

    def add_warning(self, message: str, file_path: str | None = None, line_number: int | None = None, suggestion: str | None = None) -> None:
        """添加警告"""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.WARNING,
                message=message,
                file_path=file_path,
                line_number=line_number,
                suggestion=suggestion,
            )
        )

    def add_info(self, message: str, file_path: str | None = None, line_number: int | None = None) -> None:
        """添加信息"""
        self.issues.append(
            ValidationIssue(
                level=ValidationLevel.INFO,
                message=message,
                file_path=file_path,
                line_number=line_number,
            )
        )

    @property
    def error_count(self) -> int:
        """错误数量"""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.ERROR)

    @property
    def warning_count(self) -> int:
        """警告数量"""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.WARNING)

    @property
    def info_count(self) -> int:
        """信息数量"""
        return sum(1 for issue in self.issues if issue.level == ValidationLevel.INFO)

    def _update_counts(self) -> None:
        """更新成功状态（根据错误数量）"""
        if self.error_count > 0:
            self.success = False
        elif self.error_count == 0 and not self.success:
            # 如果没有错误了，且之前是失败状态，更新为成功
            self.success = True


@dataclass
class FixResult:
    """修复结果"""

    fixer_name: str
    fixes_applied: list[str] = field(default_factory=list)
    fixes_failed: list[str] = field(default_factory=list)
    fixed_issues: list[ValidationIssue] = field(default_factory=list)
    success: bool = True

    def add_fix(self, message: str, issue: ValidationIssue | None = None) -> None:
        """添加成功的修复

        Args:
            message: 修复描述
            issue: 被修复的问题（可选）
        """
        self.fixes_applied.append(message)
        if issue:
            self.fixed_issues.append(issue)

    def add_failure(self, message: str) -> None:
        """添加失败的修复

        Args:
            message: 失败原因描述
        """
        self.fixes_failed.append(message)
        self.success = False

    @property
    def fix_count(self) -> int:
        """成功修复数量"""
        return len(self.fixes_applied)

    @property
    def failure_count(self) -> int:
        """失败修复数量"""
        return len(self.fixes_failed)


class BaseValidator(ABC):
    """验证器基类"""

    def __init__(self, plugin_path: Path):
        """初始化验证器

        Args:
            plugin_path: 插件路径
        """
        self.plugin_path = plugin_path
        self.result = ValidationResult(validator_name=self.__class__.__name__)

    @abstractmethod
    def validate(self) -> ValidationResult:
        """执行验证

        Returns:
            ValidationResult: 验证结果
        """
        pass

    def _get_plugin_name(self) -> str | None:
        """获取插件名称（从目录名）

        插件结构: my_plugin/plugin.py
        """
        return extract_plugin_name(self.plugin_path)


class BaseFixer(ABC):
    """修复器基类"""

    def __init__(self, plugin_path: Path):
        """初始化修复器

        Args:
            plugin_path: 插件路径
        """
        self.plugin_path = plugin_path
        self.result = FixResult(fixer_name=self.__class__.__name__)

    @abstractmethod
    def fix(self, issues: list[ValidationIssue]) -> FixResult:
        """执行修复

        Args:
            issues: 需要修复的问题列表

        Returns:
            FixResult: 修复结果
        """
        pass

    def can_fix(self, issue: ValidationIssue) -> bool:
        """判断是否可以修复某个问题

        Args:
            issue: 验证问题

        Returns:
            bool: 是否可以修复
        """
        return False

    def _get_plugin_name(self) -> str | None:
        """获取插件名称（从目录名）

        插件结构: my_plugin/plugin.py
        """
        return extract_plugin_name(self.plugin_path)
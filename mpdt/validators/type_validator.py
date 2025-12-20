"""类型检查验证器

使用 mypy 进行类型检查
"""

import re
import subprocess
from pathlib import Path

from .base import BaseValidator, ValidationResult


class TypeValidator(BaseValidator):
    """类型检查验证器

    使用 mypy 进行静态类型检查
    """

    def __init__(self, plugin_path: Path):
        super().__init__(plugin_path)
        # 尝试找到 MoFox 主项目路径
        self.MoFox_root = self._find_mofox_root()

    def validate(self) -> ValidationResult:
        """执行类型检查"""
        result = ValidationResult(
            validator_name="TypeValidator",
            success=True
        )

        plugin_name = self._get_plugin_name()
        if not plugin_name:
            result.add_error("无法确定插件名称")
            return result

        # 检查 mypy 是否安装
        if not self._is_mypy_installed():
            result.add_warning(
                "未安装 mypy，跳过类型检查",
                suggestion="运行 'pip install mypy' 安装"
            )
            return result

        # 运行 mypy
        issues = self._run_mypy_check()

        if issues:
            for issue in issues:
                # 根据严重程度决定是错误还是警告
                if issue.get("severity") == "error":
                    result.add_error(
                        issue["message"],
                        file_path=issue.get("file"),
                        line_number=issue.get("line"),
                        suggestion=issue.get("suggestion")
                    )
                else:
                    result.add_warning(
                        issue["message"],
                        file_path=issue.get("file"),
                        line_number=issue.get("line"),
                        suggestion=issue.get("suggestion")
                    )

        return result

    def _is_mypy_installed(self) -> bool:
        """检查 mypy 是否安装"""
        try:
            subprocess.run(
                ["mypy", "--version"],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _find_mofox_root(self) -> Path | None:
        """尝试找到 MoFox 主项目根目录

        从插件路径向上查找，直到找到包含 src/ 目录的父目录
        """
        current = self.plugin_path.parent

        # 最多向上查找 5 层
        for _ in range(5):
            if not current or current == current.parent:
                break

            # 检查是否存在 src/ 目录且包含 plugin_system 等模块
            src_dir = current / "src"
            if src_dir.exists() and src_dir.is_dir():
                # 验证是否是 MMC 项目
                if (src_dir / "plugin_system").exists() or (src_dir / "common").exists():
                    return current

            current = current.parent

        return None

    def _run_mypy_check(self) -> list[dict]:
        """运行 mypy 检查

        Returns:
            问题列表
        """
        issues = []

        try:
            # 构建命令
            cmd = [
                "mypy",
                str(self.plugin_path),
                "--no-error-summary",
                "--show-column-numbers",
                "--show-error-codes",
                "--no-namespace-packages",  # 避免包命名空间问题
            ]

            # 如果找到了 MMC 主项目，添加到 Python 路径
            if self.MoFox_root:
                cmd.extend(["--python-path", str(self.MoFox_root)])

            # 运行 mypy
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )

            # 解析输出
            if result.stdout.strip():
                for line in result.stdout.strip().split('\n'):
                    issue = self._parse_mypy_line(line)
                    if issue:
                        # 如果找不到 MoFox 根目录，过滤掉所有 src.* 模块的导入错误
                        if not self.MoFox_root:
                            # 检查是否是 src.* 模块的导入错误
                            if "Cannot find implementation" in issue["message"] and '"src.' in issue["message"]:
                                continue  # 跳过这个错误
                            # 检查是否是因为基类是 Any 导致的错误（因为导入失败）
                            if "has type \"Any\"" in issue["message"]:
                                continue  # 跳过这个错误
                        issues.append(issue)

        except Exception as e:
            issues.append({
                "file": None,
                "line": None,
                "message": f"运行 mypy 时出错: {e}",
                "severity": "error",
                "suggestion": None
            })

        return issues

    def _parse_mypy_line(self, line: str) -> dict | None:
        """解析 mypy 输出的一行

        格式: file.py:123:45: error: Message [error-code]

        Args:
            line: mypy 输出的一行

        Returns:
            解析后的问题字典，如果解析失败返回 None
        """
        # 匹配 mypy 输出格式
        pattern = r'^(.+?):(\d+):(?:\d+:)?\s+(error|warning|note):\s+(.+?)(?:\s+\[(.+?)\])?$'
        match = re.match(pattern, line)

        if not match:
            return None

        file_path, line_num, severity, message, error_code = match.groups()

        try:
            # 转换为相对路径
            rel_path = str(Path(file_path).relative_to(self.plugin_path))
        except ValueError:
            rel_path = file_path

        issue = {
            "file": rel_path,
            "line": int(line_num),
            "message": message.strip(),
            "severity": severity,
            "suggestion": None
        }

        # 添加错误代码到消息中
        if error_code:
            issue["message"] = f"[{error_code}] {issue['message']}"

        # 根据常见错误提供建议
        issue["suggestion"] = self._get_type_hint_suggestion(message, error_code)

        return issue

    def _get_type_hint_suggestion(self, message: str, error_code: str | None) -> str | None:
        """根据错误消息提供类型提示建议"""
        if not error_code:
            return None

        suggestions = {
            "no-untyped-def": "为函数添加类型注解",
            "no-untyped-call": "被调用的函数缺少类型注解",
            "assignment": "检查赋值的类型是否匹配",
            "return-value": "检查返回值类型是否与声明一致",
            "arg-type": "检查参数类型是否正确",
            "attr-defined": "检查属性是否存在",
            "name-defined": "检查名称是否定义",
            "import": "检查导入是否正确"
        }

        for code, suggestion in suggestions.items():
            if code in error_code:
                return suggestion

        return None

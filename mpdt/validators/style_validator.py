"""代码风格验证器

使用 ruff 检查代码风格问题
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from .base import BaseValidator, ValidationResult


class StyleValidator(BaseValidator):
    """代码风格验证器

    使用 ruff 检查代码风格和代码质量问题
    """

    def __init__(self, plugin_path: Path, auto_fix: bool = False):
        super().__init__(plugin_path)
        self.auto_fix = auto_fix

    def validate(self) -> ValidationResult:
        """执行代码风格检查"""
        result = ValidationResult(
            validator_name="StyleValidator",
            success=True
        )

        plugin_name = self._get_plugin_name()
        if not plugin_name:
            result.add_error("无法确定插件名称")
            return result

        # 检查 ruff 是否安装
        if not self._is_ruff_installed():
            result.add_warning("未安装 ruff，跳过代码风格检查", suggestion="运行 'pip install ruff' 安装")
            return result

        # 运行 ruff check
        issues = self._run_ruff_check()

        if issues:
            for issue in issues:
                result.add_warning(
                    issue["message"],
                    file_path=issue.get("file"),
                    line_number=issue.get("line"),
                    suggestion=issue.get("suggestion"),
                )
        else:
            result.add_info("代码风格检查通过，未发现问题")

        return result

    def _is_ruff_installed(self) -> bool:
        """检查 ruff 是否安装"""
        try:
            subprocess.run(["ruff", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _run_ruff_check(self) -> list[dict[str, Any]]:
        """运行 ruff 检查

        Returns:
            问题列表
        """
        issues = []

        try:
            # 构建命令
            cmd = ["ruff", "check"]
            if self.auto_fix:
                cmd.append("--fix")
            cmd.extend(["--output-format", "json", str(self.plugin_path)])

            # 运行 ruff
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            # 解析输出
            if result.stdout.strip():
                try:
                    ruff_output = json.loads(result.stdout)
                    for item in ruff_output:
                        issues.append(
                            {
                                "file": str(Path(item["filename"]).relative_to(self.plugin_path)),
                                "line": item["location"]["row"],
                                "message": f"{item['code']}: {item['message']}",
                                "suggestion": self._get_fix_suggestion(item),
                            }
                        )
                except json.JSONDecodeError:
                    # 如果不是 JSON 格式，尝试解析纯文本
                    pass

        except Exception as e:
            # 不抛出异常，只记录问题
            issues.append({
                "file": None,
                "line": None,
                "message": f"运行 ruff 时出错: {e}",
                "suggestion": None
            })

        return issues

    def _get_fix_suggestion(self, item: dict) -> str | None:
        """获取修复建议"""
        if item.get("fix"):
            return "可自动修复，使用 --fix 选项"
        return None

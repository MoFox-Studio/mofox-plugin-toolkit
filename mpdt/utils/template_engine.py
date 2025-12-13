"""
模板引擎
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template


class TemplateEngine:
    """模板引擎类"""

    def __init__(self, template_dir: Path | str | None = None):
        """
        初始化模板引擎

        Args:
            template_dir: 模板目录路径
        """
        if template_dir:
            self.template_dir = Path(template_dir)
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            # 使用默认模板目录
            default_template_dir = Path(__file__).parent.parent / "templates"
            self.template_dir = default_template_dir

            if default_template_dir.exists():
                self.env = Environment(
                    loader=FileSystemLoader(str(default_template_dir)),
                    trim_blocks=True,
                    lstrip_blocks=True,
                )
            else:
                self.env = None

    def render_string(self, template_string: str, context: dict[str, Any]) -> str:
        """
        渲染字符串模板

        Args:
            template_string: 模板字符串
            context: 模板变量

        Returns:
            渲染后的字符串
        """
        template = Template(template_string, trim_blocks=True, lstrip_blocks=True)
        return template.render(**context)

    def render_file(self, template_name: str, context: dict[str, Any]) -> str:
        """
        渲染文件模板

        Args:
            template_name: 模板文件名
            context: 模板变量

        Returns:
            渲染后的字符串
        """
        if self.env is None:
            raise ValueError("模板目录不存在，无法加载文件模板")

        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_to_file(self, template_name: str, context: dict[str, Any], output_path: Path | str) -> None:
        """
        渲染模板并写入文件

        Args:
            template_name: 模板文件名
            context: 模板变量
            output_path: 输出文件路径
        """
        content = self.render_file(template_name, context)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")


def prepare_common_context(**kwargs: Any) -> dict[str, Any]:
    """
    准备通用模板变量

    Args:
        **kwargs: 额外的变量

    Returns:
        模板变量字典
    """
    from datetime import datetime

    from mpdt.utils.file_ops import get_git_user_info

    git_info = get_git_user_info()

    context = {
        "timestamp": datetime.now().isoformat(),
        "year": datetime.now().year,
        "author": git_info.get("name", ""),
        "author_email": git_info.get("email", ""),
    }

    context.update(kwargs)
    return context

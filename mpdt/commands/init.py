"""
初始化命令实现
"""

from pathlib import Path
from typing import Any

import questionary

from mpdt.utils.color_printer import (
    console,
    print_error,
    print_panel,
    print_step,
    print_success,
    print_tree,
)
from mpdt.utils.file_ops import ensure_dir, get_git_user_info, safe_write_file, validate_plugin_name
from mpdt.utils.license_generator import get_license_text


def init_plugin(
    plugin_name: str | None = None,
    template: str = "basic",
    author: str | None = None,
    license_type: str = "GPL-v3.0",
    with_examples: bool = False,
    with_docs: bool = False,
    output_dir: str | None = None,
    init_git: bool | None = None,
    verbose: bool = False,
) -> None:
    """
    初始化新插件

    Args:
        plugin_name: 插件名称
        template: 模板类型
        author: 作者名称
        license_type: 开源协议
        with_examples: 是否包含示例
        with_docs: 是否创建文档
        output_dir: 输出目录
        init_git: 是否初始化 Git 仓库 (None 表示交互式询问)
        verbose: 是否详细输出
    """
    print_step("开始初始化插件...")

    # 交互式获取插件信息
    if not plugin_name:
        plugin_info = _interactive_init()
        plugin_name = plugin_info["plugin_name"]
        template = plugin_info["template"]
        author = plugin_info.get("author")
        license_type = plugin_info["license"]
        with_examples = plugin_info.get("with_examples", False)
        with_docs = plugin_info.get("with_docs", False)
        init_git = plugin_info.get("init_git", False)

    # 此时 plugin_name 必定不为 None
    assert plugin_name is not None

    # 验证插件名称
    if not validate_plugin_name(plugin_name):
        print_error("插件名称无效！必须使用小写字母、数字和下划线,以字母开头")
        return

    # 确定输出目录
    if output_dir:
        base_dir = Path(output_dir)
    else:
        base_dir = Path.cwd()

    plugin_dir = base_dir / plugin_name

    # 检查目录是否已存在
    if plugin_dir.exists():
        print_error(f"目录已存在: {plugin_dir}")
        return

    # 创建插件结构
    _create_plugin_structure(
        plugin_dir=plugin_dir,
        plugin_name=plugin_name,
        template=template,
        author=author,
        license_type=license_type,
        with_examples=with_examples,
        with_docs=with_docs,
        verbose=verbose,
    )

    # 初始化 Git 仓库
    if init_git is None:
        # 如果未指定，则询问用户
        init_git = questionary.confirm(
            "是否初始化 Git 仓库?",
            default=True,
        ).ask()

    if init_git:
        _init_git_repository(plugin_dir, verbose)

    # 打印成功信息
    print_success("插件创建成功！")
    print_tree(
        plugin_name,
        {
            ".gitignore": None,
            "__init__.py": None,
            plugin_name: {
                "__init__.py": None,
                "plugin.py": None,
                "components": ["actions", "plus_command", "tools", "events"],
                "utils": ["__init__.py"],
            },
            "docs": ["README.md"] if with_docs else [],
            "pyproject.toml": None,
            "requirements.txt": None,
            "README.md": None,
            "LICENSE": None,
        },
    )

    # 打印下一步指引
    next_steps = f"""
1. cd {plugin_name}
2. mpdt generate action MyAction  # 创建 Action 组件
3. mpdt dev                        # 启动开发模式
4. mpdt check                      # 运行检查
"""
    print_panel("📝 下一步", next_steps, style="cyan")


def _interactive_init() -> dict[str, Any]:
    """交互式初始化"""
    console.print("\n[bold cyan]🚀 欢迎使用 MPDT 插件初始化向导[/bold cyan]\n")

    git_info = get_git_user_info()

    answers = questionary.form(
        plugin_name=questionary.text(
            "插件名称 (使用下划线命名):",
            validate=lambda x: validate_plugin_name(x) or "插件名称格式无效",
        ),
        display_name=questionary.text(
            "显示名称 (用户可见):",
        ),
        description=questionary.text(
            "插件描述:",
        ),
        template=questionary.select(
            "选择插件模板:",
            choices=[
                questionary.Choice("基础插件", value="basic"),
                questionary.Choice("Action 插件", value="action"),
                questionary.Choice("Tool 插件", value="tool"),
                questionary.Choice("Plus_Command 插件", value="plus_command"),
                questionary.Choice("完整插件", value="full"),
                questionary.Choice("Adapter 插件", value="adapter"),
            ],
        ),
        author=questionary.text(
            "作者名称:",
            default=git_info.get("name", ""),
        ),
        license=questionary.select(
            "选择开源协议:",
            choices=["GPL-v3.0", "MIT", "Apache-2.0", "BSD-3-Clause"],
        ),
        with_examples=questionary.confirm(
            "包含示例代码?",
            default=True,
        ),
        with_docs=questionary.confirm(
            "创建文档文件?",
            default=True,
        ),
        init_git=questionary.confirm(
            "初始化 Git 仓库?",
            default=True,
        ),
    ).ask()

    return answers


def _create_plugin_structure(
    plugin_dir: Path,
    plugin_name: str,
    template: str,
    author: str | None,
    license_type: str,
    with_examples: bool,
    with_docs: bool,
    verbose: bool,
) -> None:
    """创建插件目录结构"""

    # 创建主目录
    ensure_dir(plugin_dir)

    # 创建根目录下的 __init__.py (给 MoFox-Plugin-Repo读取)
    root_init_content = _generate_init_file(plugin_name, author, license_type)
    safe_write_file(plugin_dir / "__init__.py", root_init_content)

    # 创建插件代码子目录
    plugin_code_dir = ensure_dir(plugin_dir / plugin_name)

    # 创建插件代码目录下的 __init__.py (给插件系统读取，内容与根目录的相同)
    safe_write_file(plugin_code_dir / "__init__.py", root_init_content)

    # 创建 plugin.py
    plugin_content = _generate_plugin_file(plugin_name, template)
    safe_write_file(plugin_code_dir / "plugin.py", plugin_content)

    # 创建 components 目录
    components_dir = ensure_dir(plugin_code_dir / "components")
    safe_write_file(components_dir / "__init__.py", '"""\n组件模块\n"""\n')

    for comp_type in ["actions", "plus_command", "tools", "events"]:
        comp_dir = ensure_dir(components_dir / comp_type)
        safe_write_file(comp_dir / "__init__.py", f'"""\n{comp_type.title()} 组件\n"""\n')

    # 创建 utils 目录
    utils_dir = ensure_dir(plugin_code_dir / "utils")
    safe_write_file(utils_dir / "__init__.py", '"""\n工具函数\n"""\n')

    # 创建文档目录
    if with_docs:
        docs_dir = ensure_dir(plugin_dir / "docs")
        safe_write_file(docs_dir / "README.md", _generate_readme_file(plugin_name))

    # 创建 pyproject.toml
    pyproject_content = _generate_pyproject_file(plugin_name, author, license_type)
    safe_write_file(plugin_dir / "pyproject.toml", pyproject_content)

    # 创建 requirements.txt
    safe_write_file(plugin_dir / "requirements.txt", "# 插件依赖列表\n")

    # 创建 README.md
    readme_content = _generate_main_readme_file(plugin_name, license_type)
    safe_write_file(plugin_dir / "README.md", readme_content)

    # 创建 LICENSE 文件
    license_content = get_license_text(license_type, author or "")
    safe_write_file(plugin_dir / "LICENSE", license_content)
    if verbose:
        console.print(f"[dim]✓ 生成许可证文件: {license_type}[/dim]")


def _generate_init_file(plugin_name: str, author: str | None, license_type: str) -> str:
    """生成 __init__.py 文件内容"""
    from mpdt.utils.template_engine import prepare_common_context

    context = prepare_common_context(
        plugin_name=plugin_name,
        author=author or "",
        license=license_type,
    )

    return f'''"""
{plugin_name} - MoFox-Bot Plugin

Author: {context['author']}
License: {context['license']}
"""

from src.plugin_system.base.plugin_metadata import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="{plugin_name}",
    description="插件描述",
    usage="该插件提供 XXX 功能",
    version="1.0.0",
    author="{context['author']}",
    license="{context['license']}",
    repository_url="https://github.com/{context['author']}/{plugin_name}",
    keywords=[],
    categories=[],
    extra={{"is_built_in": False}},
)
'''


def _generate_plugin_file(plugin_name: str, template: str) -> str:
    """生成 plugin.py 文件内容"""
    return f'''"""
{plugin_name} 插件主类
"""

from src.common.logger import get_logger
from src.plugin_system import BasePlugin, ComponentInfo, register_plugin

logger = get_logger("{plugin_name}")


@register_plugin
class {_to_pascal_case(plugin_name)}Plugin(BasePlugin):
    """
    {plugin_name} 插件
    """

    plugin_name: str = "{plugin_name}"
    enable_plugin: bool = True
    dependencies: list[str] = []
    config_file_name: str = "config.toml"
    config_schema: dict = {{}}

    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """
        获取插件包含的组件列表

        Returns:
            组件信息和组件类的列表
        """
        components = []

        # TODO: 在这里添加你的组件

        return components
'''


def _generate_readme_file(plugin_name: str) -> str:
    """生成 docs/README.md 文件内容"""
    return f'''# {plugin_name} 文档

## 功能说明

TODO: 描述插件功能

## 使用方法

TODO: 说明使用方法

## API 参考

TODO: API 文档
'''


def _generate_pyproject_file(plugin_name: str, author: str | None, license_type: str) -> str:
    """生成 pyproject.toml 文件内容"""
    return f'''[project]
name = "{plugin_name}"
version = "1.0.0"
description = "MoFox-Bot 插件"
authors = [
    {{name = "{author or 'Your Name'}", email = "your.email@example.com"}}
]
license = {{text = "{license_type}"}}
requires-python = ">=3.11"

dependencies = []
'''


def _generate_main_readme_file(plugin_name: str, license_type: str = "GPL-v3.0") -> str:
    """生成主 README.md 文件内容"""
    return f'''# {plugin_name}

MoFox-Bot 插件

## 安装

将{plugin_name}文件夹放入 `plugins/` 目录中。

## 配置

编辑 `config/config.toml` 文件进行配置。

## 使用

TODO: 添加使用说明

## 开发

```bash
# 生成组件
mpdt generate action MyAction

# 运行检查
mpdt check

# 运行测试
mpdt test
```

## 许可证

本项目基于 {license_type} 许可证开源,详见 [LICENSE](./LICENSE) 文件。
'''


def _to_pascal_case(snake_str: str) -> str:
    """将 snake_case 转换为 PascalCase"""
    return "".join(word.capitalize() for word in snake_str.split("_"))


def _init_git_repository(plugin_dir: Path, verbose: bool) -> None:
    """
    初始化 Git 仓库

    Args:
        plugin_dir: 插件目录
        verbose: 是否详细输出
    """
    import subprocess

    try:
        # 初始化 Git 仓库
        subprocess.run(
            ["git", "init"],
            cwd=plugin_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # 创建 .gitignore 文件
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# MoFox-Bot specific
config/local_*.toml
*.log
"""
        safe_write_file(plugin_dir / ".gitignore", gitignore_content)

        # 执行初始提交
        subprocess.run(
            ["git", "add", "."],
            cwd=plugin_dir,
            check=True,
            capture_output=True,
        )

        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=plugin_dir,
            check=True,
            capture_output=True,
        )

        if verbose:
            console.print("[dim]✓ 初始化 Git 仓库[/dim]")
        print_success("Git 仓库初始化成功")

    except subprocess.CalledProcessError as e:
        print_error(f"Git 初始化失败: {e}")
    except FileNotFoundError:
        print_error("未找到 Git 命令，请确保已安装 Git")


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

    # 根据模板类型构建目录树显示
    components_tree = _build_components_tree(template)

    print_tree(
        plugin_name,
        {
            ".gitignore": None,
            "__init__.py": None,
            plugin_name: {
                "__init__.py": None,
                "plugin.py": None,
                "components": components_tree,
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

    # 根据模板类型自动生成示例组件
    _generate_example_components(
        components_dir=components_dir,
        plugin_name=plugin_name,
        template=template,
        author=author,
        verbose=verbose,
    )

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

    # 根据模板类型生成导入语句和组件注册
    imports, component_registrations = _get_component_imports_and_registrations(plugin_name, template)

    return f'''"""
{plugin_name} 插件主类
"""

from src.common.logger import get_logger
from src.plugin_system import BasePlugin, ComponentInfo, register_plugin
{imports}
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

{component_registrations}
        return components
'''


def _get_component_imports_and_registrations(plugin_name: str, template: str) -> tuple[str, str]:
    """
    根据模板类型获取组件导入语句和注册代码

    Args:
        plugin_name: 插件名称
        template: 模板类型

    Returns:
        (导入语句, 组件注册代码)
    """
    # 模板类型与组件配置的映射
    # (组件类型, 模块名, 类名, 目录名, 获取info的方法名)
    template_components = {
        "basic": [],
        "action": [
            ("action", "example_action", "ExampleActionAction", "actions", "get_action_info"),
        ],
        "tool": [
            ("tool", "example_tool", "ExampleToolTool", "tools", "get_tool_info"),
        ],
        "plus_command": [
            ("plus_command", "example_command", "ExampleCommandPlusCommand", "plus_command", "get_plus_command_info"),
        ],
        "adapter": [
            ("adapter", "example_adapter", "ExampleAdapterAdapter", "adapters", "get_adapter_info"),
        ],
        "full": [
            ("action", "example_action", "ExampleActionAction", "actions", "get_action_info"),
            ("tool", "example_tool", "ExampleToolTool", "tools", "get_tool_info"),
            ("plus_command", "example_command", "ExampleCommandPlusCommand", "plus_command", "get_plus_command_info"),
            ("event", "example_event", "ExampleEventEventHandler", "events", "get_handler_info"),
        ],
    }

    components = template_components.get(template, [])

    if not components:
        return "", "        # TODO: 在这里添加你的组件\n"

    # 生成导入语句
    import_lines = []
    for comp_type, module_name, class_name, folder, _ in components:
        import_lines.append(
            f"from {plugin_name}.components.{folder}.{module_name} import {class_name}"
        )

    imports = "\n" + "\n".join(import_lines) + "\n"

    # 生成组件注册代码
    registration_lines = []
    for comp_type, module_name, class_name, folder, info_method in components:
        comp_type_display = comp_type.replace("_", " ").title()
        registration_lines.append(
            f"        # 注册 {comp_type_display} 组件\n"
            f"        components.append(({class_name}.{info_method}(), {class_name}))\n"
        )

    registrations = "\n".join(registration_lines)

    return imports, registrations


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


def _build_components_tree(template: str) -> dict[str, list[str]] | list[str]:
    """
    根据模板类型构建组件目录树

    Args:
        template: 模板类型

    Returns:
        组件目录树结构
    """
    # 基础目录结构
    base_tree = {
        "actions": ["__init__.py"],
        "plus_command": ["__init__.py"],
        "tools": ["__init__.py"],
        "events": ["__init__.py"],
    }

    # 根据模板类型添加示例文件
    if template == "action":
        base_tree["actions"].append("example_action.py")
    elif template == "tool":
        base_tree["tools"].append("example_tool.py")
    elif template == "plus_command":
        base_tree["plus_command"].append("example_command.py")
    elif template == "adapter":
        base_tree["adapters"] = ["__init__.py", "example_adapter.py"]
    elif template == "full":
        base_tree["actions"].append("example_action.py")
        base_tree["tools"].append("example_tool.py")
        base_tree["plus_command"].append("example_command.py")
        base_tree["events"].append("example_event.py")

    return base_tree


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
            encoding='utf-8',
            errors='ignore'
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
            encoding='utf-8',
            errors='ignore'
        )

        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=plugin_dir,
            check=True,
            capture_output=True,
            encoding='utf-8',
            errors='ignore'
        )

        if verbose:
            console.print("[dim]✓ 初始化 Git 仓库[/dim]")
        print_success("Git 仓库初始化成功")

    except subprocess.CalledProcessError as e:
        print_error(f"Git 初始化失败: {e}")
    except FileNotFoundError:
        print_error("未找到 Git 命令，请确保已安装 Git")


def _generate_example_components(
    components_dir: Path,
    plugin_name: str,
    template: str,
    author: str | None,
    verbose: bool,
) -> None:
    """
    根据模板类型生成示例组件文件

    Args:
        components_dir: 组件目录
        plugin_name: 插件名称
        template: 模板类型 (basic, action, tool, plus_command, full, adapter)
        author: 作者
        verbose: 是否详细输出
    """
    from mpdt.templates import get_component_template, prepare_component_context

    # 模板类型与组件类型的映射
    template_component_map = {
        "basic": [],  # 基础模板不生成示例
        "action": [("action", "example_action", "示例 Action 组件")],
        "tool": [("tool", "example_tool", "示例 Tool 组件")],
        "plus_command": [("plus_command", "example_command", "示例 PlusCommand 组件")],
        "adapter": [("adapter", "example_adapter", "示例 Adapter 组件")],
        "full": [
            ("action", "example_action", "示例 Action 组件"),
            ("tool", "example_tool", "示例 Tool 组件"),
            ("plus_command", "example_command", "示例 PlusCommand 组件"),
            ("event", "example_event", "示例 Event 组件"),
        ],
    }

    # 组件类型与目录名的映射
    component_dir_map = {
        "action": "actions",
        "tool": "tools",
        "plus_command": "plus_command",
        "event": "events",
        "adapter": "adapters",
    }

    components_to_create = template_component_map.get(template, [])

    for comp_type, comp_name, comp_desc in components_to_create:
        try:
            # 获取模板
            template_str = get_component_template(comp_type)

            # 准备上下文
            context = prepare_component_context(
                component_type=comp_type,
                component_name=comp_name,
                plugin_name=plugin_name,
                author=author or "",
                description=comp_desc,
            )

            # 渲染模板
            content = template_str.format(**context)

            # 确定目标目录
            target_dir = components_dir / component_dir_map.get(comp_type, f"{comp_type}s")
            if not target_dir.exists():
                ensure_dir(target_dir)
                safe_write_file(target_dir / "__init__.py", f'"""\n{comp_type.title()} 组件\n"""\n')

            # 写入文件
            file_path = target_dir / f"{comp_name}.py"
            safe_write_file(file_path, content)

            if verbose:
                console.print(f"[dim]✓ 生成示例组件: {comp_name}.py[/dim]")

        except Exception as e:
            if verbose:
                console.print(f"[dim yellow]⚠ 生成组件 {comp_name} 失败: {e}[/dim yellow]")

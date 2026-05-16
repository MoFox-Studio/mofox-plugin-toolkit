"""
初始化命令实现

代码结构：
1. 主入口函数 - 插件初始化的核心逻辑
2. 交互式处理 - 用户交互相关函数
3. 目录结构创建 - 创建插件文件和目录
4. 文件内容生成器 - 各类配置和代码文件的生成
5. Git 仓库管理 - Git 初始化相关
6. 工具函数 - 辅助函数和转换工具
"""

#todo:move git system into a new file

from pathlib import Path
from typing import Any

import questionary

from mpdt.utils.color_printer import (
    print_colored,
    print_empty_line,
    print_error,
    print_panel,
    print_step,
    print_success,
    print_tree,
)
from mpdt.utils.file_ops import ensure_dir, safe_write_file, validate_plugin_name
from mpdt.utils.license_generator import get_license_text
from mpdt.utils.managers.manifest_manager import ALLOWED_CATEGORIES, ManifestManager
from mpdt.utils.managers.git_manager import GitManager

# ============================================================================
# 主入口函数
# ============================================================================


def init_plugin(
    plugin_name: str | None = None,
    template: str = "basic",
    author: str | None = None,
    email: str | None = None,
    license_type: str = "GPL-v3.0",
    with_docs: bool = False,
    output_dir: str | None = None,
    init_git: bool | None = None,
    categories: str | None = None,
    tags: str | None = None,
) -> None:
    """
    初始化新插件

    Args:
        plugin_name: 插件名称
        template: 模板类型
        author: 作者名称
        email: 作者邮箱
        license_type: 开源协议
        with_docs: 是否创建文档
        output_dir: 输出目录
        init_git: 是否初始化 Git 仓库 (None 表示交互式询问)
        categories: 插件分类（单个值，从允许的分类中选择）
        tags: 插件标签（逗号分隔的字符串）
    """
    print_step("开始初始化插件...")

    # 交互式获取插件信息
    if not plugin_name:
        plugin_info = _interactive_init()
        plugin_name = plugin_info["plugin_name"]
        template = plugin_info["template"]
        author = plugin_info.get("author")
        email = plugin_info.get("email")
        license_type = plugin_info["license"]
        with_docs = plugin_info.get("with_docs", False)
        init_git = plugin_info.get("init_git", False)
        categories = plugin_info.get("categories")
        tags = plugin_info.get("tags")

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
        email=email,
        license_type=license_type,
        with_docs=with_docs,
        categories=categories,
        tags=tags,
    )

    # 初始化 Git 仓库
    if init_git is None:
        # 如果未指定，则询问用户
        init_git = questionary.confirm(
            "是否初始化 Git 仓库?",
            default=True,
        ).ask()

    if init_git:
        git_manager = GitManager(plugin_dir)
        success, message = git_manager.init_repository()
        if success:
            print_success(message)
        else:
            print_error(message)

    # 打印成功信息
    print_success("插件创建成功！")

    # 根据用户选择动态构建目录树
    plugin_tree = _build_plugin_tree(
        plugin_name=plugin_name,
        template=template,
        with_docs=with_docs,
        init_git=init_git or False,
    )

    print_tree(plugin_name, plugin_tree)

    # 打印下一步指引
    next_steps = f"""
1. cd {plugin_name}
2. mpdt plugin generate action MyAction  # 创建 Action 组件
3. mpdt plugin dev                  # 启动开发模式
4. mpdt plugin check                # 运行检查
"""
    print_panel("📝 下一步", next_steps, style="cyan")


# ============================================================================
# 交互式处理
# ============================================================================


def _interactive_init() -> dict[str, Any]:
    """交互式初始化"""
    print_colored("🚀 欢迎使用 MPDT 插件初始化向导", color="cyan", bold=True)
    print_empty_line()

    git_info = GitManager.get_user_info()

    answers = questionary.form(
        plugin_name=questionary.text(
            "插件名称 (使用 snake_case: 小写字母、数字、下划线，以字母开头):",
            validate=lambda x: validate_plugin_name(x) or "插件名称格式无效！必须使用小写字母、数字、下划线，以字母开头，例如: my_plugin",
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
                questionary.Choice("Collection 插件", value="collection"),
                questionary.Choice("Router 插件", value="router"),
                questionary.Choice("Plus_Command 插件", value="plus_command"),
                questionary.Choice("Event Handler 插件", value="event_handler"),
                questionary.Choice("完整插件", value="full"),
                questionary.Choice("Adapter 插件", value="adapter"),
                questionary.Choice("Chatter 插件", value="chatter"),
            ],
        ),
        author=questionary.text(
            "作者名称:",
            default=git_info.get("name", ""),
        ),
        email=questionary.text(
            "邮箱地址:",
            default=git_info.get("email", ""),
        ),
        categories=questionary.select(
            "选择插件分类 (categories):",
            choices=[questionary.Choice(item, value=item) for item in ALLOWED_CATEGORIES],
        ),
        tags=questionary.text(
            "填写插件标签 (tags，多个标签用逗号分隔):",
            validate=lambda x: bool(x.strip()) or "至少填写一个标签",
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

        # ============================================================================
        # 目录结构创建
        # ============================================================================


def _create_plugin_structure(
    plugin_dir: Path,
    plugin_name: str,
    template: str,
    author: str | None,
    email: str | None,
    license_type: str,
    with_docs: bool,
    categories: str | None,
    tags: str | None,
) -> None:
    """创建插件目录结构"""

    # 创建主目录
    ensure_dir(plugin_dir)

    # 创建 manifest.json
    manifest_manager = ManifestManager(plugin_dir)
    manifest_manager.create(
        name=plugin_name,
        author=author or "Your Name",
        template=template,
        description="",
    )
    
    # 设置分类和标签
    if categories:
        manifest_manager.set_categories([categories])
    if tags:
        normalized_tags = ManifestManager.normalize_tags(tags)
        manifest_manager.set_tags(normalized_tags)
    
    manifest_manager.save()

    # 创建 plugin.py
    plugin_content = _generate_plugin_file(plugin_name, template)
    safe_write_file(plugin_dir / "plugin.py", plugin_content)

    # 创建 components 目录
    components_dir = ensure_dir(plugin_dir / "components")
    safe_write_file(components_dir / "__init__.py", '"""\n组件模块\n"""\n')

    for comp_type in [
        "actions",
        "plus_command",
        "tools",
        "collections",
        "events",
        "configs",
        "services",
        "adapters",
        "chatters",
        "routers",
    ]:
        comp_dir = ensure_dir(components_dir / comp_type)
        safe_write_file(comp_dir / "__init__.py", f'"""\n{comp_type.title()} 组件\n"""\n')

    # 创建 utils 目录
    utils_dir = ensure_dir(plugin_dir / "utils")
    safe_write_file(utils_dir / "__init__.py", '"""\n工具函数\n"""\n')

    # 根据模板类型自动生成示例组件
    _generate_example_components(
        components_dir=components_dir,
        plugin_name=plugin_name,
        template=template,
        author=author,
    )

    # 创建文档目录
    if with_docs:
        docs_dir = ensure_dir(plugin_dir / "docs")
        safe_write_file(docs_dir / "README.md", _generate_readme_file(plugin_name))

    # 创建 pyproject.toml
    pyproject_content = _generate_pyproject_file(plugin_name, author, email, license_type)
    safe_write_file(plugin_dir / "pyproject.toml", pyproject_content)

    # 创建 requirements.txt
    safe_write_file(plugin_dir / "requirements.txt", "# 插件依赖列表\n")

    # 创建 README.md
    readme_content = _generate_main_readme_file(plugin_name, license_type)
    safe_write_file(plugin_dir / "README.md", readme_content)

    # 创建 LICENSE 文件
    license_content = get_license_text(license_type, author or "")
    safe_write_file(plugin_dir / "LICENSE", license_content)


# _generate_manifest_file 函数已被 ManifestManager 替代，不再需要


def _generate_plugin_file(plugin_name: str, template: str) -> str:
    """生成 plugin.py 文件内容（适配 Neo-MoFox 架构）"""

    # 根据模板类型生成导入语句和组件类列表
    imports, component_list = _get_component_imports_and_list(template)

    return f'''"""
{plugin_name} 插件主类
"""

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BasePlugin
from src.core.components.loader import register_plugin
{imports}
logger = get_logger("{plugin_name}")


@register_plugin
class {_to_pascal_case(plugin_name)}Plugin(BasePlugin):
    """
    {plugin_name} 插件
    """

    plugin_name = "{plugin_name}"
    plugin_version = "1.0.0"
    plugin_author = "Your Name"
    plugin_description = "{plugin_name} 插件"
    configs = [Config]

    def get_components(self) -> list[type]:
        """获取插件内所有组件类

        Returns:
            list[type]: 插件内所有组件类的列表
        """
        return [{component_list}]
'''


def _get_component_imports_and_list(template: str) -> tuple[str, str]:
    """
    根据模板类型获取组件导入语句和组件类列表（适配 Neo-MoFox 架构）
    使用相对导入，不依赖插件名称

    Args:
        template: 模板类型

    Returns:
        (导入语句, 组件类列表字符串)
    """
    # 模板类型与组件配置的映射
    # (组件类型, 模块名, 类名, 目录名)
    template_components = {
        "basic": [
            ("config", "config", "Config", "configs"),
        ],
        "action": [
            ("config", "config", "Config", "configs"),
            ("action", "example_action", "ExampleAction", "actions"),
        ],
        "tool": [
            ("config", "config", "Config", "configs"),
            ("tool", "example_tool", "ExampleTool", "tools"),
        ],
        "collection": [
            ("config", "config", "Config", "configs"),
            ("collection", "example_collection", "ExampleCollection", "collections"),
        ],
        "plus_command": [
            ("config", "config", "Config", "configs"),
            ("plus_command", "example_command", "ExampleCommand", "plus_command"),
        ],
        "adapter": [
            ("config", "config", "Config", "configs"),
            ("adapter", "example_adapter", "ExampleAdapter", "adapters"),
        ],
        "chatter": [
            ("config", "config", "Config", "configs"),
            ("chatter", "example_chatter", "ExampleChatter", "chatters"),
        ],
        "router": [
            ("config", "config", "Config", "configs"),
            ("router", "example_router", "ExampleRouter", "routers"),
        ],
        "event_handler": [
            ("config", "config", "Config", "configs"),
            ("event_handler", "example_event", "ExampleEvent", "events"),
        ],
        "full": [
            ("config", "config", "Config", "configs"),
            ("action", "example_action", "ExampleAction", "actions"),
            ("tool", "example_tool", "ExampleTool", "tools"),
            ("collection", "example_collection", "ExampleCollection", "collections"),
            ("plus_command", "example_command", "ExampleCommand", "plus_command"),
            ("event_handler", "example_event", "ExampleEvent", "events"),
            ("service", "example_service", "ExampleService", "services"),
        ],
    }

    components = template_components.get(template, [])

    if not components:
        return "", ""

    # 生成导入语句（使用相对导入）
    import_lines = []
    for (
        comp_type,
        module_name,
        class_name,
        folder,
    ) in components:
        import_lines.append(f"from .components.{folder}.{module_name} import {class_name}")

    imports = "\n" + "\n".join(import_lines) + "\n" if import_lines else ""

    # 生成组件类列表（排除 Config，因为它通过 config 属性声明）
    class_names = [class_name for comp_type, _, class_name, _ in components if comp_type != "config"]
    component_list = ", ".join(class_names) if class_names else ""

    return imports, component_list


def _generate_readme_file(plugin_name: str) -> str:
    """生成 docs/README.md 文件内容"""
    return f"""# {plugin_name} 文档

## 功能说明

TODO: 描述插件功能

## 使用方法

TODO: 说明使用方法

## API 参考

TODO: API 文档
"""


def _generate_pyproject_file(plugin_name: str, author: str | None, email: str | None, license_type: str) -> str:
    """生成 pyproject.toml 文件内容"""
    return f'''[project]
name = "{plugin_name}"
version = "1.0.0"
description = "MoFox-Bot 插件"
authors = [
    {{name = "{author or "Your Name"}", email = "{email or "your.email@example.com"}"}}
]
license = {{text = "{license_type}"}}
requires-python = ">=3.11"

dependencies = []
'''


def _generate_main_readme_file(plugin_name: str, license_type: str = "GPL-v3.0") -> str:
    """生成主 README.md 文件内容"""
    return f"""# {plugin_name}

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
"""


def _to_pascal_case(snake_str: str) -> str:
    """将 snake_case 转换为 PascalCase"""
    return "".join(word.capitalize() for word in snake_str.split("_"))


#====================================
#           动态构建完整的插件目录树
#====================================

def _build_plugin_tree(
    plugin_name: str,
    template: str,
    with_docs: bool,
    init_git: bool,
) -> dict[str, Any]:
    """
    根据用户选择动态构建完整的插件目录树

    Args:
        plugin_name: 插件名称
        template: 模板类型
        with_docs: 是否包含文档
        init_git: 是否初始化 Git

    Returns:
        完整的目录树结构
    """
    # 构建组件目录树
    components_tree = _build_components_tree(template)

    # 构建基础树结构
    tree: dict[str, Any] = {}

    # Git 相关文件
    if init_git:
        tree[".gitignore"] = None

    # 核心文件
    tree["manifest.json"] = None
    tree["plugin.py"] = None

    # 组件和工具目录
    tree["components"] = components_tree
    tree["utils"] = ["__init__.py"]

    # 文档目录（根据 with_docs 决定）
    if with_docs:
        tree["docs"] = ["README.md"]

    # 项目配置文件
    tree["pyproject.toml"] = None
    tree["requirements.txt"] = None
    tree["README.md"] = None
    tree["LICENSE"] = None

    return tree


def _build_components_tree(template: str) -> dict[str, list[str]] | list[str]:
    """
    根据模板类型构建组件目录树

    Args:
        template: 模板类型

    Returns:
        组件目录树结构
    """
    # 初始化基础目录结构（所有模板都需要的基础目录）
    base_tree: dict[str, list[str]] = {
        "configs": ["__init__.py", "config.py"],
        "actions": ["__init__.py"],
        "plus_command": ["__init__.py"],
        "tools": ["__init__.py"],
        "collections": ["__init__.py"],
        "events": ["__init__.py"],
        "services": ["__init__.py"],
        "adapters": ["__init__.py"],
        "chatters": ["__init__.py"],
        "routers": ["__init__.py"],
    }

    # 根据模板类型添加示例文件
    if template == "basic":
        # 基础模板仅保留必需的目录
        return {
            "configs": ["__init__.py", "config.py"],
            "actions": ["__init__.py"],
            "plus_command": ["__init__.py"],
            "tools": ["__init__.py"],
            "collections": ["__init__.py"],
            "events": ["__init__.py"],
            "services": ["__init__.py"],
            "adapters": ["__init__.py"],
            "chatters": ["__init__.py"],
            "routers": ["__init__.py"],
        }
    elif template == "action":
        base_tree["actions"].append("example_action.py")
    elif template == "tool":
        base_tree["tools"].append("example_tool.py")
    elif template == "collection":
        base_tree["collections"].append("example_collection.py")
    elif template == "plus_command":
        base_tree["plus_command"].append("example_command.py")
    elif template == "adapter":
        base_tree["adapters"].append("example_adapter.py")
    elif template == "chatter":
        base_tree["chatters"].append("example_chatter.py")
    elif template == "router":
        base_tree["routers"].append("example_router.py")
    elif template == "event_handler":
        base_tree["events"].append("example_event.py")
    elif template == "full":
        base_tree["actions"].append("example_action.py")
        base_tree["tools"].append("example_tool.py")
        base_tree["collections"].append("example_collection.py")
        base_tree["plus_command"].append("example_command.py")
        base_tree["events"].append("example_event.py")
        base_tree["services"].append("example_service.py")

    return base_tree


# _init_git_repository 函数已被 GitManager 替代，不再需要


def _generate_example_components(
    components_dir: Path,
    plugin_name: str,
    template: str,
    author: str | None,
) -> None:
    """
    根据模板类型生成示例组件文件

    Args:
        components_dir: 组件目录
        plugin_name: 插件名称
        template: 模板类型 (basic, action, tool, plus_command, full, adapter)
        author: 作者
    """
    from mpdt.templates import get_component_template, prepare_component_context

    # 模板类型与组件类型的映射
    template_component_map = {
        "basic": [("config", "config", "插件配置")],  # 基础模板至少生成config
        "action": [
            ("config", "config", "插件配置"),
            ("action", "example_action", "示例 Action 组件"),
        ],
        "tool": [
            ("config", "config", "插件配置"),
            ("tool", "example_tool", "示例 Tool 组件"),
        ],
        "collection": [
            ("config", "config", "插件配置"),
            ("collection", "example_collection", "示例 Collection 组件"),
        ],
        "plus_command": [
            ("config", "config", "插件配置"),
            ("plus_command", "example_command", "示例 PlusCommand 组件"),
        ],
        "adapter": [
            ("config", "config", "插件配置"),
            ("adapter", "example_adapter", "示例 Adapter 组件"),
        ],
        "chatter": [
            ("config", "config", "插件配置"),
            ("chatter", "example_chatter", "示例 Chatter 组件"),
        ],
        "router": [
            ("config", "config", "插件配置"),
            ("router", "example_router", "示例 Router 组件"),
        ],
        "event_handler": [
            ("config", "config", "插件配置"),
            ("event", "example_event", "示例 Event Handler 组件"),
        ],
        "full": [
            ("config", "config", "插件配置"),
            ("action", "example_action", "示例 Action 组件"),
            ("tool", "example_tool", "示例 Tool 组件"),
            ("collection", "example_collection", "示例 Collection 组件"),
            ("plus_command", "example_command", "示例 PlusCommand 组件"),
            ("event", "example_event", "示例 Event 组件"),
            ("service", "example_service", "示例 Service 组件"),
        ],
    }

    # 组件类型与目录名的映射
    component_dir_map = {
        "action": "actions",
        "tool": "tools",
        "collection": "collections",
        "plus_command": "plus_command",
        "event": "events",
        "event_handler": "events",
        "adapter": "adapters",
        "service": "services",
        "config": "configs",
        "chatter": "chatters",
        "router": "routers",
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

        except Exception as e:
            print_colored(f"⚠ 生成组件 {comp_name} 失败: {e}", color="yellow", dim=True)

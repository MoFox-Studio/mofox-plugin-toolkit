"""
插件名称解析器
使用 AST 解析插件文件，提取运行时插件名称
"""

import ast
from pathlib import Path


def extract_plugin_name(plugin_path: Path) -> str | None:
    """从插件目录提取运行时插件名称

    Args:
        plugin_path: 插件目录路径

    Returns:
        插件名称，如果解析失败返回 None

    Example:
        >>> extract_plugin_name(Path("my_awesome_plugin"))
        "awesome_plugin"  # 从 plugin.py 中的 plugin_name 属性读取
    """
    plugin_file = plugin_path / "plugin.py"

    if not plugin_file.exists():
        return None

    try:
        with open(plugin_file, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # 查找 BasePlugin 的子类
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否继承自 BasePlugin
                is_base_plugin = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BasePlugin":
                        is_base_plugin = True
                        break

                if not is_base_plugin:
                    continue

                # 查找 plugin_name 属性
                for item in node.body:
                    # 处理普通赋值: plugin_name = "xxx"
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "plugin_name":
                                if isinstance(item.value, ast.Constant):
                                    return item.value.value

                    # 处理带类型注解的赋值: plugin_name: str = "xxx"
                    elif isinstance(item, ast.AnnAssign):
                        if isinstance(item.target, ast.Name) and item.target.id == "plugin_name":
                            if item.value and isinstance(item.value, ast.Constant):
                                return item.value.value

        return None

    except Exception:
        return None


def get_plugin_info(plugin_path: Path) -> dict:
    """获取插件详细信息

    Args:
        plugin_path: 插件目录路径

    Returns:
        包含插件信息的字典:
        {
            "dir_name": "my_awesome_plugin",
            "plugin_name": "awesome_plugin",
            "class_name": "MyAwesomePlugin",
            "path": "/path/to/plugin",
            "has_plugin_file": True,
            "parse_success": True
        }
    """
    info = {
        "dir_name": plugin_path.name,
        "plugin_name": None,
        "class_name": None,
        "path": str(plugin_path.absolute()),
        "has_plugin_file": False,
        "parse_success": False,
    }

    plugin_file = plugin_path / "plugin.py"

    if not plugin_file.exists():
        return info

    info["has_plugin_file"] = True

    try:
        with open(plugin_file, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        # 查找 BasePlugin 的子类
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # 检查是否继承自 BasePlugin
                is_base_plugin = False
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BasePlugin":
                        is_base_plugin = True
                        break

                if not is_base_plugin:
                    continue

                info["class_name"] = node.name

                # 查找 plugin_name 属性
                for item in node.body:
                    # 处理普通赋值: plugin_name = "xxx"
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "plugin_name":
                                if isinstance(item.value, ast.Constant):
                                    info["plugin_name"] = item.value.value
                                    info["parse_success"] = True
                                    break

                    # 处理带类型注解的赋值: plugin_name: str = "xxx"
                    elif isinstance(item, ast.AnnAssign):
                        if isinstance(item.target, ast.Name) and item.target.id == "plugin_name":
                            if item.value and isinstance(item.value, ast.Constant):
                                info["plugin_name"] = item.value.value
                                info["parse_success"] = True
                                break

                # 找到 BasePlugin 子类后跳出
                if info["class_name"]:
                    break

        return info

    except Exception as e:
        info["error"] = str(e)
        return info


def validate_plugin_structure(plugin_path: Path) -> tuple[bool, list[str]]:
    """验证插件目录结构

    Args:
        plugin_path: 插件目录路径

    Returns:
        (是否有效, 错误/警告消息列表)
    """
    messages = []

    if not plugin_path.is_dir():
        return False, ["路径不是一个目录"]

    # 检查必需文件
    required_files = {"plugin.py": "插件主文件", "__init__.py": "包初始化文件"}

    for filename, description in required_files.items():
        file_path = plugin_path / filename
        if not file_path.exists():
            messages.append(f"缺少 {description}: {filename}")

    # 如果缺少必需文件，直接返回
    if messages:
        return False, messages

    # 检查 plugin.py 是否可以解析
    plugin_name = extract_plugin_name(plugin_path)
    if not plugin_name:
        messages.append("无法从 plugin.py 中提取 plugin_name")
        messages.append("请确保有一个继承自 BasePlugin 的类，并定义了 plugin_name 属性")
        return False, messages

    # 检查推荐文件
    recommended_files = {"config.toml": "配置文件", "README.md": "说明文档"}

    for filename, description in recommended_files.items():
        file_path = plugin_path / filename
        if not file_path.exists():
            messages.append(f"建议添加 {description}: {filename}")

    # 如果只有建议性消息，仍然返回有效
    has_errors = any("缺少" in msg or "无法" in msg for msg in messages)
    return not has_errors, messages

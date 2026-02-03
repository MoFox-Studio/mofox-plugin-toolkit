"""
插件名称解析器
使用统一的 CodeParser 解析插件文件，提取运行时插件名称
"""

from pathlib import Path

from .code_parser import CodeParser


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
        parser = CodeParser.from_file(plugin_file)
        return parser.find_class_attribute(base_class="BasePlugin", attribute_name="plugin_name")
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
        parser = CodeParser.from_file(plugin_file)

        # 查找 BasePlugin 的子类
        classes = parser.find_class(base_class="BasePlugin")

        if classes:
            # 获取第一个匹配的类
            cls = classes[0]
            info["class_name"] = cls.name.value

            # 提取 plugin_name 属性
            plugin_name = parser.find_class_attribute(base_class="BasePlugin", attribute_name="plugin_name")

            if plugin_name:
                info["plugin_name"] = plugin_name
                info["parse_success"] = True

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

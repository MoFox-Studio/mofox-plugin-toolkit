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
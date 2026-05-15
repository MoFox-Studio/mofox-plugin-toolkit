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
        # 如果没有 plugin.py，尝试返回目录名作为后备
        if plugin_path.is_dir():
            return plugin_path.name
        return None

    try:
        parser = CodeParser.from_file(plugin_file)
        plugin_name = parser.find_class_attribute(base_class="BasePlugin", attribute_name="plugin_name")
        
        # 如果找到了 plugin_name 属性，使用它
        if plugin_name:
            return plugin_name
        
        # 否则，使用目录名作为后备
        return plugin_path.name
    except Exception:
        # 出错时，尝试使用目录名
        if plugin_path.is_dir():
            return plugin_path.name
        return None
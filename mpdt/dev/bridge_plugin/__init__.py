"""开发模式桥接插件

这是一个特殊的插件，在开发模式下临时注入到主程序。
负责文件监控和插件热重载，配置由 mpdt dev 在注入时写入 dev_config.py。
"""

from src.plugin_system.base.plugin_metadata import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="dev_bridge",
    description="开发模式桥接插件，提供文件监控和热重载功能",
    usage="在开发模式下临时注入，监控目标插件文件变化并自动重载。",
    version="1.0.0",
    author="MoFox Team",
    dependencies=[],
    python_dependencies=["watchdog"],
)

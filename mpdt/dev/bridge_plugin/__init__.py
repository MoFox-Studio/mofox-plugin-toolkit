"""开发模式桥接插件

这是一个特殊的插件，在开发模式下临时注入到主程序。
通过 WebSocket 与 mpdt dev 通信，提供插件重载等功能。
"""

from src.plugin_system.base.plugin_metadata import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="dev_bridge",
    description="开发模式桥接插件，提供 WebSocket 热重载接口",
    usage="在开发模式下临时注入，提供热重载和调试桥接接口。",
    version="1.0.0",
    author="MoFox Team",
    dependencies=[],
    python_dependencies=[],
)

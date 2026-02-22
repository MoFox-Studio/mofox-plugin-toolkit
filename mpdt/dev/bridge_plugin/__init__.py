"""开发模式桥接插件

这是一个特殊的插件，在开发模式下临时注入到主程序。
负责文件监控和插件热重载，配置由 mpdt dev 在注入时写入 dev_config.py。

Neo-MoFox 版本：使用 manifest.json 代替 PluginMetadata，符合新版插件系统规范。
"""

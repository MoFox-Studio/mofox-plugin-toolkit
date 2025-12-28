"""
开发模式配置文件
此文件在 mpdt dev 注入时会被修改，用于传递开发插件的配置信息
"""

# ==================== 开发目标插件配置 ====================
# 以下常量会在 mpdt dev 注入时被自动修改

# 目标插件的绝对路径
TARGET_PLUGIN_PATH: str = ""

# 目标插件名称
TARGET_PLUGIN_NAME: str = ""

# 是否启用文件监控
ENABLE_FILE_WATCHER: bool = True

# 文件监控防抖延迟（秒）
DEBOUNCE_DELAY: float = 0.3

# ==================== 其他配置 ====================

# 发现服务器端口
DISCOVERY_PORT: int = 12318

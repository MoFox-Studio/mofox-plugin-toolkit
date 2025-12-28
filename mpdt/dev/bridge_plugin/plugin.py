"""
DevBridge 插件 - 完整的开发模式插件
负责文件监控、插件重载等所有开发操作
配置通过 dev_config.py 中的常量传递（mpdt dev 注入时动态修改）
"""

import asyncio
from pathlib import Path
from typing import ClassVar

from src.common.logger import get_logger
from src.plugin_system import (
    BasePlugin,
    register_plugin,
)

# 导入配置（由 mpdt dev 注入时修改）
from .dev_config import (
    TARGET_PLUGIN_PATH,
    TARGET_PLUGIN_NAME,
    ENABLE_FILE_WATCHER,
    DEBOUNCE_DELAY,
)

logger = get_logger("dev_bridge")


@register_plugin
class DevBridgePlugin(BasePlugin):
    """开发模式桥接插件

    这是一个完整的开发模式插件，负责：
    1. 监控目标插件的文件变化
    2. 自动重载目标插件
    
    配置通过 dev_config.py 传递，mpdt dev 在注入时会修改这些常量。
    """

    plugin_name = "dev_bridge"
    enable_plugin = True
    config_file_name = "config.toml"
    dependencies: ClassVar = []
    python_dependencies: ClassVar = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._file_watcher = None
        self._target_plugin_name = TARGET_PLUGIN_NAME
        self._target_plugin_path = TARGET_PLUGIN_PATH

    def get_plugin_components(self) -> list:
        """无需注册组件"""
        return []

    async def on_plugin_loaded(self):
        """插件加载完成后启动文件监控"""
        from .file_watcher import FileWatcher

        logger.info("=" * 60)
        logger.info("🚀 DevBridge 开发模式插件已加载")
        logger.info(f"📦 目标插件: {self._target_plugin_name}")
        logger.info(f"📂 目标路径: {self._target_plugin_path}")
        logger.info("=" * 60)

        # 启动文件监控
        if ENABLE_FILE_WATCHER and self._target_plugin_path:
            plugin_path = Path(self._target_plugin_path)
            if plugin_path.exists():
                self._file_watcher = FileWatcher(
                    plugin_path,
                    self._on_file_changed,
                    DEBOUNCE_DELAY
                )
                # 获取当前事件循环并启动监控
                try:
                    loop = asyncio.get_running_loop()
                    self._file_watcher.start(loop)
                    logger.info("👀 文件监控已启动")
                    logger.info("📝 修改 Python 文件将自动重载插件")
                except Exception as e:
                    logger.error(f"启动文件监控失败: {e}")
            else:
                logger.warning(f"目标插件路径不存在: {plugin_path}")
        else:
            logger.info("文件监控已禁用或未配置目标路径")

    async def _on_file_changed(self, rel_path: str):
        """文件变化回调 - 自动重载目标插件"""
        if not self._target_plugin_name:
            logger.warning("未配置目标插件名称，跳过重载")
            return

        logger.info(f"📝 检测到文件变化: {rel_path}")
        logger.info(f"🔄 正在重载插件: {self._target_plugin_name}...")

        try:
            from src.plugin_system.apis import plugin_manage_api
            
            success = await plugin_manage_api.reload_plugin(self._target_plugin_name)
            
            if success:
                logger.info(f"✅ 插件 {self._target_plugin_name} 重载成功")
            else:
                logger.error(f"❌ 插件 {self._target_plugin_name} 重载失败")

        except Exception as e:
            logger.error(f"❌ 重载插件时出错: {e}")
            import traceback
            traceback.print_exc()

    async def on_plugin_unload(self):
        """插件卸载时停止文件监控"""
        # 停止文件监控
        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher = None
            logger.info("文件监控已停止")

        logger.info("DevBridge 插件已卸载")

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
    DEBOUNCE_DELAY,
    ENABLE_FILE_WATCHER,
    TARGET_PLUGIN_NAME,
    TARGET_PLUGIN_PATH,
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
        """注册清理事件处理器"""
        from .cleanup_handler import CleanupHandler

        return [(CleanupHandler.get_handler_info(), CleanupHandler)]

    async def on_plugin_loaded(self):
        """插件加载完成后启动文件监控"""
        from .file_watcher import FileWatcher

        logger.info("=" * 60)
        logger.info("🚀 DevBridge 开发模式插件已加载")
        logger.info(f"📦 目标插件: {self._target_plugin_name}")
        logger.info(f"📂 目标路径: {self._target_plugin_path}")
        logger.info("=" * 60)

        # 检查目标插件是否成功加载
        await self._check_target_plugin_loaded()

        # 启动文件监控
        if ENABLE_FILE_WATCHER and self._target_plugin_path:
            plugin_path = Path(self._target_plugin_path)
            if plugin_path.exists():
                self._file_watcher = FileWatcher(plugin_path, self._on_file_changed, DEBOUNCE_DELAY)
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

    async def _check_target_plugin_loaded(self):
        """检查目标插件是否成功加载，未加载则报错提示"""
        if not self._target_plugin_name:
            logger.error("❌ 未配置目标插件名称")
            return

        try:
            from src.plugin_system.apis import plugin_manage_api

            is_loaded = plugin_manage_api.is_plugin_loaded(self._target_plugin_name)
            is_enabled = plugin_manage_api.is_plugin_enabled(self._target_plugin_name)

            if not is_loaded:
                logger.error("=" * 60)
                logger.error(f"❌ 目标插件 {self._target_plugin_name} 未加载！")
                logger.error("")
                if not is_enabled:
                    logger.error("📋 原因: 插件已被禁用")
                    logger.error("")
                    logger.error("🔧 解决方案:")
                    logger.error("   1. 检查插件的 config.toml 中 [plugin] enabled = true")
                    logger.error("   2. 或在 plugin.py 中设置 enable_plugin = True")
                    logger.error("   3. 或直接删除 enable_plugin 行（默认启用）")
                else:
                    logger.error("📋 原因: 插件加载失败，请检查插件代码是否有错误")
                logger.error("=" * 60)
            else:
                logger.info(f"✅ 目标插件 {self._target_plugin_name} 已成功加载")

        except ValueError:
            logger.error(f"❌ 目标插件 {self._target_plugin_name} 未注册")
        except Exception as e:
            logger.error(f"❌ 检查目标插件状态时出错: {e}")

    async def _on_file_changed(self, rel_path: str):
        """文件变化回调 - 同步文件并重载目标插件"""
        if not self._target_plugin_name:
            logger.warning("未配置目标插件名称，跳过重载")
            return

        logger.info(f"📝 检测到文件变化: {rel_path}")

        # 先同步文件到 plugins 目录
        try:
            self._sync_plugin_files()
            logger.info("📦 文件已同步到 plugins 目录")
        except Exception as e:
            logger.error(f"❌ 同步文件失败: {e}")
            return

        try:
            from src.plugin_system.apis import plugin_manage_api

            plugin_name = self._target_plugin_name
            is_loaded = plugin_manage_api.is_plugin_loaded(plugin_name)
            is_enabled = plugin_manage_api.is_plugin_enabled(plugin_name)

            if is_loaded:
                # 插件已加载，检查是否被禁用
                if not is_enabled:
                    logger.info(f"🔓 插件 {plugin_name} 已禁用，正在启用...")
                    await plugin_manage_api.enable_plugin(plugin_name)

                # 重载插件
                logger.info(f"🔄 正在重载插件: {plugin_name}...")
                success = await plugin_manage_api.reload_plugin(plugin_name)
                if success:
                    logger.info(f"✅ 插件 {plugin_name} 重载成功")
                else:
                    logger.error(f"❌ 插件 {plugin_name} 重载失败")
            else:
                # 插件未加载，使用 enable_plugin 来加载并启用
                # enable_plugin 会同时处理加载和启用，即使插件之前被禁用
                logger.info(f"📦 插件 {plugin_name} 未加载，正在启用并加载...")
                success = await plugin_manage_api.enable_plugin(plugin_name)
                if success:
                    logger.info(f"✅ 插件 {plugin_name} 启用并加载成功")
                else:
                    logger.error(f"❌ 插件 {plugin_name} 启用/加载失败")

        except ValueError as e:
            # 插件未注册，尝试扫描并加载
            logger.warning(f"⚠️ 插件未注册: {e}")
            logger.info("🔍 正在扫描插件目录...")
            try:
                from src.plugin_system.apis import plugin_manage_api

                plugin_manage_api.rescan_and_register_plugins(load_after_register=True)
                if plugin_manage_api.is_plugin_loaded(self._target_plugin_name):
                    logger.info(f"✅ 插件 {self._target_plugin_name} 扫描并加载成功")
                else:
                    logger.error(f"❌ 插件 {self._target_plugin_name} 扫描后仍未加载")
            except Exception as scan_e:
                logger.error(f"❌ 扫描插件目录失败: {scan_e}")
        except Exception as e:
            logger.error(f"❌ 操作插件时出错: {e}")
            import traceback

            traceback.print_exc()

    def _sync_plugin_files(self):
        """将源插件目录同步到 plugins 目录"""
        import shutil

        source_path = Path(self._target_plugin_path)
        # plugins 目录是 dev_bridge 所在目录的父目录
        plugins_dir = Path(__file__).parent.parent
        target_path = plugins_dir / self._target_plugin_name

        # 如果源插件已经在 plugins 目录下，不需要同步
        if source_path.parent.resolve() == plugins_dir.resolve():
            return

        if not source_path.exists():
            raise FileNotFoundError(f"源插件目录不存在: {source_path}")

        # 删除旧的目标目录
        if target_path.exists():
            shutil.rmtree(target_path)

        # 复制新文件
        shutil.copytree(source_path, target_path)

    async def on_plugin_unload(self):
        """插件卸载时停止文件监控"""
        # 停止文件监控
        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher = None
            logger.info("文件监控已停止")

        logger.info("DevBridge 插件已卸载")

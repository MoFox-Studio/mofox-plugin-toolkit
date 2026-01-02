"""
DevBridge 清理事件处理器
在程序停止时清理 DevBridge 插件和目标插件
"""

import shutil
from pathlib import Path
from typing import ClassVar

from src.common.logger import get_logger
from src.plugin_system.base import BaseEventHandler
from src.plugin_system.base.component_types import EventType

from .dev_config import TARGET_PLUGIN_NAME, TARGET_PLUGIN_PATH

logger = get_logger("dev_bridge_cleanup")


class CleanupHandler(BaseEventHandler):
    """清理事件处理器 - 在程序停止时清理插件文件"""

    handler_name = "dev_bridge_cleanup"
    handler_description = "DevBridge 清理处理器"
    weight = -100  # 负权重，确保最后执行
    init_subscribe: ClassVar[list[EventType | str]] = [EventType.ON_STOP]

    def __init__(self):
        super().__init__()
        self._target_plugin_name = TARGET_PLUGIN_NAME
        self._target_plugin_path = TARGET_PLUGIN_PATH

    async def execute(self, kwargs: dict | None) -> tuple[bool, bool, str | None]:
        """程序停止时执行清理（同步删除）"""
        logger.info("🛑 收到停止事件，准备清理 DevBridge...")
        
        self._delete_plugins()
        
        return True, True, None

    def _delete_plugins(self):
        """同步删除插件目录"""
        plugin_dir = Path(__file__).parent
        # 目标插件在 plugins 目录中的路径
        plugins_dir = plugin_dir.parent  # plugins 目录
        source_path = Path(self._target_plugin_path)
        target_plugin_dir = plugins_dir / self._target_plugin_name if self._target_plugin_name else None

        # 判断目标插件是否本来就在 plugins 目录下
        is_in_plugins_dir = source_path.parent.resolve() == plugins_dir.resolve()

        # 删除目标开发插件（仅当它是复制进来的时候）
        if not is_in_plugins_dir and target_plugin_dir and target_plugin_dir.exists():
            try:
                shutil.rmtree(target_plugin_dir)
                logger.info(f"🧹 目标插件已清理: {target_plugin_dir}")
            except Exception as e:
                logger.warning(f"⚠️ 清理目标插件失败: {e}")
        
        # 删除 DevBridge 自己
        try:
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)
                print(f"[DevBridge] 🧹 DevBridge 插件已清理: {plugin_dir}")
        except Exception as e:
            print(f"[DevBridge] ⚠️ 清理 DevBridge 插件失败: {e}")

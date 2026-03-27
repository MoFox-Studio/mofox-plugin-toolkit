"""
DevBridge 清理事件处理器
在程序停止时清理 DevBridge 插件和目标插件
"""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.core.components.base.event_handler import BaseEventHandler
from src.core.components.types import EventType
from src.kernel.event import EventDecision
from src.kernel.logger import get_logger

from .dev_config import TARGET_PLUGIN_NAME, TARGET_PLUGIN_PATH

if TYPE_CHECKING:
    from .plugin import DevBridgePlugin

logger = get_logger("dev_bridge_cleanup")


class CleanupHandler(BaseEventHandler):
    """清理事件处理器 - 在程序停止时清理插件文件"""

    handler_name = "dev_bridge_cleanup"
    handler_description = "DevBridge 清理处理器，在系统停止时移除临时插件文件"
    weight = -100  # 负权重，确保最后执行
    intercept_message = False
    init_subscribe: list[EventType | str] = [EventType.ON_STOP]

    def __init__(self, plugin: "DevBridgePlugin") -> None:
        """初始化清理处理器
        
        Args:
            plugin: DevBridge 插件实例
        """
        super().__init__(plugin)
        self._target_plugin_name = TARGET_PLUGIN_NAME
        self._target_plugin_path = TARGET_PLUGIN_PATH

    async def execute(
        self,
        event_name: str,
        params: dict[str, Any],
    ) -> tuple[EventDecision, dict[str, Any]]:
        """程序停止时执行清理（同步删除）
        
        Args:
            event_name: 事件名称（ON_STOP）
            params: 事件参数
            
        Returns:
            事件决策和更新后的参数
        """
        logger.info("🛑 收到停止事件，准备清理 DevBridge...")

        try:
            self._delete_plugins()
            logger.info("✅ DevBridge 清理完成")
        except Exception as e:
            logger.error(f"❌ DevBridge 清理失败: {e}", exc_info=True)

        # 返回 SUCCESS，继续执行后续清理处理器
        return EventDecision.SUCCESS, params

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

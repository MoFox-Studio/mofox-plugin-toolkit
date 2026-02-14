"""
Adapter 组件模板（Neo-MoFox 架构）
"""

ADAPTER_TEMPLATE = '''"""  {description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from mofox_wire import CoreSink, MessageEnvelope

from src.app.plugin_system.api.log_api import get_logger
from src.core.components.base import BaseAdapter

logger = get_logger(__name__)


class {class_name}(BaseAdapter):
    """
    {description}

    Adapter 组件用于连接外部平台（如QQ、微信等）与 MoFox-Bot 核心。
    """

    adapter_name = "{component_name}"
    adapter_version = "1.0.0"
    adapter_author = "{author}"
    adapter_description = "{description}"
    platform = "your_platform"  # 平台标识（如 qq, wechat 等）

    run_in_subprocess = False  # 是否在子进程中运行

    def __init__(self, core_sink: CoreSink, plugin):
        """初始化适配器

        Args:
            core_sink: 核心消息接收器
            plugin: 插件实例
        """
        # TODO: 配置传输方式（WebSocket/HTTP等）
        # 示例：
        # from mofox_wire import WebSocketAdapterOptions
        # transport = WebSocketAdapterOptions(
        #     mode="client",
        #     url="ws://127.0.0.1:8080",
        # )
        transport = None  # 请根据需要配置传输方式

        super().__init__(core_sink, plugin=plugin, transport=transport)

        # TODO: 初始化适配器特定的属性

    async def on_adapter_loaded(self) -> None:
        """适配器加载时的初始化"""
        logger.info(f"{{self.adapter_name}} 适配器正在启动...")
        # TODO: 实现加载逻辑
        logger.info(f"{{self.adapter_name}} 适配器已加载")

    async def on_adapter_unloaded(self) -> None:
        """适配器卸载时的清理"""
        logger.info(f"{{self.adapter_name}} 适配器正在关闭...")
        # TODO: 实现清理逻辑
        logger.info(f"{{self.adapter_name}} 适配器已关闭")

    async def from_platform_message(self, raw: dict[str, Any]) -> MessageEnvelope | None:
        """
        将平台原始消息转换为 MessageEnvelope

        Args:
            raw: 平台原始消息数据

        Returns:
            MessageEnvelope 对象，或 None（如果消息应被忽略）
        """
        try:
            # TODO: 实现消息转换逻辑
            # 示例：
            # envelope = MessageEnvelope(
            #     message_id=raw.get("id"),
            #     sender_id=raw.get("sender"),
            #     text=raw.get("text"),
            #     # ... 其他字段
            # )
            # return envelope
            logger.warning("from_platform_message 未实现")
            return None
        except Exception as e:
            logger.error(f"消息转换失败: {{e}}")
            return None

    async def _send_platform_message(self, envelope: MessageEnvelope) -> None:
        """
        将 MessageEnvelope 转换为平台消息并发送

        Args:
            envelope: MessageEnvelope 对象
        """
        try:
            # TODO: 实现消息发送逻辑
            logger.info(f"发送消息: {{envelope}}")
        except Exception as e:
            logger.error(f"发送消息失败: {{e}}")

    async def get_bot_info(self) -> dict[str, Any]:
        """获取 Bot 信息

        Returns:
            Bot 信息字典，应包含：
            - bot_id: Bot ID
            - bot_nickname: Bot 昵称
            - platform: 平台标识
        """
        # TODO: 返回实际的 Bot 信息
        return {{
            "bot_id": "your_bot_id",
            "bot_nickname": "Your Bot",
            "platform": self.platform,
        }}
'''


def get_adapter_template() -> str:
    """获取 Adapter 组件模板"""
    return ADAPTER_TEMPLATE

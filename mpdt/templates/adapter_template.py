"""
Adapter 组件模板
"""

ADAPTER_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from mofox_wire import MessageEnvelope
from src.common.logger import get_logger
from src.plugin_system import BaseAdapter

logger = get_logger(__name__)


class {class_name}(BaseAdapter):
    """
    {description}

    Adapter 组件用于连接不同的平台或服务。

    支持的场景：
    - QQ/微信等聊天平台
    - Discord/Telegram 等国际平台
    - 自定义 API 服务
    - WebSocket/HTTP 协议适配
    """

    # Adapter 元数据
    adapter_name: str = "{adapter_name}"
    adapter_version: str = "1.0.0"
    adapter_author: str = "{author}"
    adapter_description: str = "{description}"

    # 是否在子进程中运行
    run_in_subprocess: bool = False
    # 子进程启动脚本路径（相对于插件目录）
    subprocess_entry: str | None = None

    async def from_platform_message(self, raw: Any) -> MessageEnvelope:
        """
        将平台原始消息转换为标准 MessageEnvelope 格式

        Args:
            raw: 平台原始消息对象

        Returns:
            MessageEnvelope: 标准消息信封
        """
        try:
            logger.debug(f"转换平台消息: {{raw}}")

            # TODO: 解析平台消息并转换为 MessageEnvelope
            # 示例：
            # message_id = raw.get("message_id")
            # user_id = raw.get("user_id")
            # content = raw.get("content")
            # timestamp = raw.get("timestamp")
            #
            # return MessageEnvelope(
            #     message_id=message_id,
            #     user_id=user_id,
            #     content=content,
            #     timestamp=timestamp,
            #     platform="your_platform"
            # )

            raise NotImplementedError("需要实现 from_platform_message 方法")

        except Exception as e:
            logger.error(f"转换消息失败: {{e}}")
            raise

    async def _send_platform_message(self, envelope: MessageEnvelope) -> None:
        """
        发送消息到平台

        Args:
            envelope: 要发送的消息信封
        """
        try:
            logger.info(f"发送消息: {{envelope.message_id}}")

            # TODO: 实现发送消息逻辑
            # 将 MessageEnvelope 转换为平台格式并发送
            # 示例：
            # platform_message = {{
            #     "target_id": envelope.target_id,
            #     "content": envelope.content,
            #     "message_type": envelope.message_type
            # }}
            # await self.platform_api.send(platform_message)

            raise NotImplementedError("需要实现 _send_platform_message 方法")

        except Exception as e:
            logger.error(f"发送消息失败: {{e}}")
            raise

    async def on_adapter_loaded(self) -> None:
        """
        适配器加载时的钩子
        可以在这里执行初始化逻辑
        """
        logger.info(f"{{self.adapter_name}} 适配器加载完成")

        # TODO: 初始化逻辑
        # 例如：建立连接、加载配置、启动后台任务等

    async def on_adapter_unloaded(self) -> None:
        """
        适配器卸载时的钩子
        可以在这里执行清理逻辑
        """
        logger.info(f"{{self.adapter_name}} 适配器卸载")

        # TODO: 清理逻辑
        # 例如：关闭连接、保存状态、停止后台任务等
'''


def get_adapter_template() -> str:
    """获取 Adapter 组件模板"""
    return ADAPTER_TEMPLATE

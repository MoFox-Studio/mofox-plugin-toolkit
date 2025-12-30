"""
文件监控器模块
负责监控目标插件的文件变化并触发重载
"""

import asyncio
import time
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import TYPE_CHECKING, Any

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

if TYPE_CHECKING:
    pass

try:
    from src.common.logger import get_logger
    logger = get_logger("dev_watcher")
except ImportError:
    import logging
    logger = logging.getLogger("dev_watcher")


class PluginFileHandler(FileSystemEventHandler):
    """插件文件变化处理器"""

    def __init__(
        self,
        plugin_path: Path,
        callback: Callable[[str], Coroutine[Any, Any, None] | None],
        debounce_delay: float = 0.3
    ):
        self.plugin_path = plugin_path
        self.callback = callback
        self.debounce_delay = debounce_delay
        self.last_modified: dict[str, float] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """设置事件循环"""
        self._loop = loop

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def on_created(self, event: FileSystemEvent):
        if event.is_directory:
            return
        self._handle_change(event.src_path)

    def _handle_change(self, src_path: str):
        """处理文件变化"""
        # 只监控 Python 文件
        if not src_path.endswith(".py"):
            return

        # 防抖处理
        now = time.time()
        if src_path in self.last_modified:
            if now - self.last_modified[src_path] < self.debounce_delay:
                return

        self.last_modified[src_path] = now

        # 获取相对路径
        try:
            rel_path = Path(src_path).relative_to(self.plugin_path)
        except ValueError:
            rel_path = Path(src_path).name

        logger.info(f"检测到文件变化: {rel_path}")

        # 在事件循环中调度回调
        if self._loop and self.callback:
            asyncio.run_coroutine_threadsafe(
                self._async_callback(str(rel_path)),
                self._loop
            )

    async def _async_callback(self, rel_path: str):
        """异步回调包装"""
        try:
            result = self.callback(rel_path)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.error(f"文件变化回调执行失败: {e}")


class FileWatcher:
    """文件监控器"""

    def __init__(
        self,
        plugin_path: str | Path,
        on_change_callback: Callable[[str], Coroutine[Any, Any, None] | None],
        debounce_delay: float = 0.3
    ):
        self.plugin_path = Path(plugin_path)
        self.on_change_callback = on_change_callback
        self.debounce_delay = debounce_delay
        self._observer: Observer | None = None
        self._handler: PluginFileHandler | None = None
        self._running = False

    def start(self, loop: asyncio.AbstractEventLoop | None = None):
        """启动文件监控"""
        if self._running:
            logger.warning("文件监控器已在运行")
            return

        if not self.plugin_path.exists():
            logger.error(f"插件路径不存在: {self.plugin_path}")
            return

        # 创建处理器
        self._handler = PluginFileHandler(
            self.plugin_path,
            self.on_change_callback,
            self.debounce_delay
        )

        # 设置事件循环
        if loop:
            self._handler.set_event_loop(loop)
        else:
            try:
                self._handler.set_event_loop(asyncio.get_running_loop())
            except RuntimeError:
                pass

        # 创建并启动观察者
        self._observer = Observer()
        self._observer.schedule(
            self._handler,
            str(self.plugin_path),
            recursive=True
        )
        self._observer.start()
        self._running = True

        logger.info(f"文件监控已启动: {self.plugin_path}")

    def stop(self):
        """停止文件监控"""
        if not self._running:
            return

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._observer = None

        self._running = False
        logger.info("文件监控已停止")

    @property
    def is_running(self) -> bool:
        return self._running

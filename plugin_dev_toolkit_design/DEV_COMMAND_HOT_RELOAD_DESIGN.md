# mpdt dev 命令热重载设计方案

## 概述

`mpdt dev` 命令旨在为插件开发者提供便捷的开发体验，支持：
1. 监听插件文件变化
2. 自动热重载插件
3. 与主程序（mmc）集成

## 核心问题分析

### 1. 热重载的挑战

#### Python 模块重载的问题
- Python 的 `importlib.reload()` 有限制，无法处理类实例的更新
- 已创建的对象不会自动更新到新版本
- 需要显式管理新旧实例的切换

#### 状态迁移问题
- 插件运行时状态（内存数据、配置等）如何迁移
- 事件处理器、定时任务等如何平滑过渡
- 数据库连接、网络连接等资源的管理

### 2. 现有架构分析

从代码中可以看到：

```python
# mmc/src/plugin_system/core/plugin_manager.py
class PluginManager:
    def __init__(self):
        self.plugin_classes: dict[str, type[PluginBase]] = {}  # 插件类
        self.loaded_plugins: dict[str, PluginBase] = {}        # 插件实例
        
    async def reload_registered_plugin(self, plugin_name: str) -> bool:
        """重载插件模块"""
        if not await self.remove_registered_plugin(plugin_name):
            return False
        if not self.load_registered_plugin_classes(plugin_name)[0]:
            return False
        return True
```

已有基础的重载机制，但需要增强。

## 设计方案

### 方案一：独立开发服务器模式（推荐）

#### 架构设计

```
┌─────────────────────────────────────────────────────┐
│              mpdt dev 进程                           │
│  ┌──────────────────────────────────────────────┐  │
│  │        开发服务器 (DevServer)                 │  │
│  │  - 启动简化版 mmc 核心                        │  │
│  │  - 只加载开发中的插件                         │  │
│  │  - 文件监控 (watchdog)                       │  │
│  │  - 自动重载                                   │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │   热重载管理器 (HotReloadManager)            │  │
│  │  - 检测文件变化                              │  │
│  │  - 触发重载                                   │  │
│  │  - 状态迁移                                   │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │        Web 调试界面 (可选)                    │  │
│  │  - 实时日志查看                              │  │
│  │  - 插件状态监控                              │  │
│  │  - 手动重载控制                              │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

#### 优点
- **独立运行**：不依赖主程序，开发者可以快速启动测试
- **环境隔离**：开发环境与生产环境分离，不影响运行中的机器人
- **调试友好**：可以集成更多开发工具（调试器、性能分析等）
- **快速迭代**：文件保存即重载，即时看到效果

#### 缺点
- 需要实现一个简化版的 mmc 核心
- 可能无法完全模拟生产环境

### 方案二：注入式热重载（需主程序支持）

#### 架构设计

```
┌────────────────────────────────────────────────────┐
│              主程序 (mmc)                           │
│  ┌─────────────────────────────────────────────┐  │
│  │      PluginManager                          │  │
│  │  - 加载所有插件                             │  │
│  │  - 标记开发模式插件                         │  │
│  └─────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
                    ↑ IPC 通信
┌────────────────────────────────────────────────────┐
│            mpdt dev 进程                            │
│  ┌─────────────────────────────────────────────┐  │
│  │   开发模式守护进程                           │  │
│  │  - 监控插件文件                             │  │
│  │  - 通知主程序重载                           │  │
│  │  - 通过 RPC/WebSocket 与主程序通信          │  │
│  └─────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

#### 优点
- 完全在真实环境中测试
- 不需要模拟核心功能

#### 缺点
- 需要主程序支持开发模式
- IPC 通信增加复杂度
- 主程序崩溃影响开发体验

## 推荐实现：方案一的详细设计

### 1. 核心组件

#### 1.1 DevServer - 开发服务器

```python
# mpdt/commands/dev.py

import asyncio
from pathlib import Path
from typing import Optional

from rich.console import Console
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from mpdt.dev.hot_reload_manager import HotReloadManager
from mpdt.dev.mini_core import MiniCore

console = Console()


class DevServer:
    """插件开发服务器"""
    
    def __init__(
        self,
        plugin_path: Path,
        port: int = 8080,
        host: str = "127.0.0.1",
        auto_reload: bool = True,
        debug: bool = False,
    ):
        self.plugin_path = plugin_path
        self.port = port
        self.host = host
        self.auto_reload = auto_reload
        self.debug = debug
        
        # 初始化组件
        self.mini_core: Optional[MiniCore] = None
        self.reload_manager: Optional[HotReloadManager] = None
        self.observer: Optional[Observer] = None
        
    async def start(self):
        """启动开发服务器"""
        console.print(f"[green]🚀 启动开发服务器...[/green]")
        console.print(f"   插件路径: {self.plugin_path}")
        console.print(f"   监听地址: {self.host}:{self.port}")
        
        # 1. 初始化简化版核心
        self.mini_core = MiniCore(debug=self.debug)
        await self.mini_core.initialize()
        
        # 2. 加载插件
        success = await self.mini_core.load_plugin(self.plugin_path)
        if not success:
            console.print("[red]❌ 插件加载失败[/red]")
            return
        
        console.print("[green]✅ 插件加载成功[/green]")
        
        # 3. 启动热重载
        if self.auto_reload:
            self.reload_manager = HotReloadManager(
                plugin_path=self.plugin_path,
                mini_core=self.mini_core,
            )
            await self.reload_manager.start()
            console.print("[green]🔥 热重载已启用[/green]")
        
        # 4. 启动 Web 界面（可选）
        # await self._start_web_ui()
        
        console.print("\n[bold green]✨ 开发服务器就绪！[/bold green]")
        console.print("按 Ctrl+C 停止服务器\n")
        
        # 保持运行
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """停止开发服务器"""
        console.print("\n[yellow]⏳ 正在停止...[/yellow]")
        
        if self.reload_manager:
            await self.reload_manager.stop()
        
        if self.mini_core:
            await self.mini_core.shutdown()
        
        console.print("[green]👋 再见！[/green]")


async def dev_command(
    plugin_path: Path,
    port: int,
    host: str,
    no_reload: bool,
    debug: bool,
):
    """mpdt dev 命令实现"""
    server = DevServer(
        plugin_path=plugin_path,
        port=port,
        host=host,
        auto_reload=not no_reload,
        debug=debug,
    )
    await server.start()
```

#### 1.2 HotReloadManager - 热重载管理器

```python
# mpdt/dev/hot_reload_manager.py

import asyncio
from pathlib import Path
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from rich.console import Console

console = Console()


class PluginFileHandler(FileSystemEventHandler):
    """插件文件变化处理器"""
    
    def __init__(self, reload_callback):
        self.reload_callback = reload_callback
        self._debounce_task: Optional[asyncio.Task] = None
        
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if event.is_directory:
            return
        
        # 只关注 Python 文件和配置文件
        if not event.src_path.endswith(('.py', '.toml', '.yaml', '.json')):
            return
        
        # 防抖处理：避免连续触发
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
        
        self._debounce_task = asyncio.create_task(
            self._debounced_reload(event.src_path)
        )
    
    async def _debounced_reload(self, file_path: str):
        """防抖重载"""
        await asyncio.sleep(0.5)  # 等待 500ms
        await self.reload_callback(file_path)


class HotReloadManager:
    """热重载管理器"""
    
    def __init__(self, plugin_path: Path, mini_core):
        self.plugin_path = plugin_path
        self.mini_core = mini_core
        self.observer: Optional[Observer] = None
        
    async def start(self):
        """启动文件监控"""
        handler = PluginFileHandler(self._on_file_changed)
        
        self.observer = Observer()
        self.observer.schedule(
            handler,
            str(self.plugin_path),
            recursive=True
        )
        self.observer.start()
        
    async def stop(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
    
    async def _on_file_changed(self, file_path: str):
        """文件变化回调"""
        console.print(f"\n[yellow]📝 检测到文件变化: {Path(file_path).name}[/yellow]")
        console.print("[cyan]🔄 重新加载插件...[/cyan]")
        
        try:
            # 1. 卸载旧插件
            await self.mini_core.unload_plugin()
            
            # 2. 清除模块缓存
            self._clear_module_cache()
            
            # 3. 重新加载插件
            success = await self.mini_core.load_plugin(self.plugin_path)
            
            if success:
                console.print("[green]✅ 重载成功！[/green]\n")
            else:
                console.print("[red]❌ 重载失败，请检查错误信息[/red]\n")
                
        except Exception as e:
            console.print(f"[red]❌ 重载出错: {e}[/red]\n")
    
    def _clear_module_cache(self):
        """清除模块缓存"""
        import sys
        
        # 查找并删除插件相关的模块
        plugin_name = self.plugin_path.name
        modules_to_remove = [
            mod_name for mod_name in sys.modules
            if plugin_name in mod_name
        ]
        
        for mod_name in modules_to_remove:
            del sys.modules[mod_name]
```

#### 1.3 MiniCore - 简化版核心

```python
# mpdt/dev/mini_core.py

import sys
from pathlib import Path
from typing import Optional

from rich.console import Console

console = Console()


class MiniCore:
    """简化版 mmc 核心
    
    提供最小化的运行环境，用于插件开发测试
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.plugin_manager = None
        self.current_plugin = None
        
    async def initialize(self):
        """初始化核心组件"""
        # 动态导入 mmc 的核心组件
        # 注意：需要将 mmc 目录添加到 sys.path
        
        try:
            # 尝试导入 mmc 的插件管理器
            from src.plugin_system.core.plugin_manager import PluginManager
            
            self.plugin_manager = PluginManager()
            console.print("[green]✅ 核心初始化成功[/green]")
            
        except ImportError as e:
            console.print(f"[yellow]⚠️  无法导入 mmc 核心: {e}[/yellow]")
            console.print("[yellow]   将使用模拟模式[/yellow]")
            # 使用模拟的插件管理器
            self.plugin_manager = MockPluginManager()
    
    async def load_plugin(self, plugin_path: Path) -> bool:
        """加载插件"""
        try:
            # 添加插件父目录到 sys.path
            parent_path = str(plugin_path.parent)
            if parent_path not in sys.path:
                sys.path.insert(0, parent_path)
            
            # 使用插件管理器加载插件
            plugin_file = plugin_path / "plugin.py"
            if not plugin_file.exists():
                console.print(f"[red]❌ 找不到 plugin.py: {plugin_file}[/red]")
                return False
            
            # 这里需要调用插件管理器的加载逻辑
            # 具体实现取决于 PluginManager 的 API
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ 加载插件失败: {e}[/red]")
            if self.debug:
                import traceback
                console.print(traceback.format_exc())
            return False
    
    async def unload_plugin(self):
        """卸载插件"""
        if self.current_plugin:
            # 调用插件的 on_unload 钩子
            if hasattr(self.current_plugin, 'on_unload'):
                await self.current_plugin.on_unload()
            
            self.current_plugin = None
    
    async def shutdown(self):
        """关闭核心"""
        await self.unload_plugin()
        console.print("[green]✅ 核心已关闭[/green]")


class MockPluginManager:
    """模拟的插件管理器（当无法导入 mmc 核心时使用）"""
    
    def __init__(self):
        console.print("[yellow]⚠️  使用模拟插件管理器[/yellow]")
```

### 2. CLI 集成

```python
# mpdt/cli.py

@cli.command()
@click.option("--port", "-p", type=int, default=8080, help="开发服务器端口")
@click.option("--host", default="127.0.0.1", help="绑定的主机地址")
@click.option("--no-reload", is_flag=True, help="禁用自动重载")
@click.option("--debug", is_flag=True, help="启用调试模式")
@click.pass_context
def dev(ctx: click.Context, port: int, host: str, no_reload: bool, debug: bool) -> None:
    """启动开发模式，支持热重载"""
    
    # 获取当前工作目录
    plugin_path = Path.cwd()
    
    # 检查是否是有效的插件目录
    if not (plugin_path / "plugin.py").exists():
        console.print("[red]❌ 当前目录不是有效的插件目录[/red]")
        console.print("[yellow]   请在插件根目录（包含 plugin.py 的目录）中运行此命令[/yellow]")
        return
    
    # 启动开发服务器
    try:
        import asyncio
        from mpdt.commands.dev import dev_command
        
        asyncio.run(dev_command(
            plugin_path=plugin_path,
            port=port,
            host=host,
            no_reload=no_reload,
            debug=debug,
        ))
    except KeyboardInterrupt:
        pass
```

### 3. 依赖管理

```toml
# pyproject.toml

[project.optional-dependencies]
dev = [
    "watchdog>=3.0.0",      # 文件监控
    "aiohttp>=3.9.0",       # Web 服务器（可选）
]
```

## 使用流程

### 1. 开发者工作流

```bash
# 1. 创建插件
mpdt init my_awesome_plugin
cd my_awesome_plugin

# 2. 启动开发服务器
mpdt dev

# 3. 编辑插件代码
# 文件保存后自动重载

# 4. 测试插件功能
# 通过日志查看效果
```

### 2. 与主程序集成测试

```bash
# 方式一：使用软链接
ln -s /path/to/my_awesome_plugin /path/to/mmc/plugins/

# 方式二：使用 mpdt install（待实现）
mpdt install --dev /path/to/my_awesome_plugin

# 然后启动主程序进行完整测试
```

## 进阶功能

### 1. 状态持久化

```python
class HotReloadManager:
    async def _on_file_changed(self, file_path: str):
        # 保存插件状态
        state = await self.mini_core.save_plugin_state()
        
        # 重载插件
        await self.mini_core.reload_plugin()
        
        # 恢复状态
        await self.mini_core.restore_plugin_state(state)
```

### 2. Web 调试界面

提供一个简单的 Web 界面：
- 实时日志流
- 插件状态监控
- 手动触发重载
- 配置编辑器

### 3. 断点调试支持

集成 debugpy，支持 VS Code 远程调试：

```python
if debug:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    console.print("[cyan]🐛 调试端口已开启: 5678[/cyan]")
```

## 实现路线图

### Phase 1: 基础热重载 ✅
- [ ] 实现 `DevServer`
- [ ] 实现 `HotReloadManager` 
- [ ] 文件监控和自动重载
- [ ] CLI 命令集成

### Phase 2: 增强功能
- [ ] 实现 `MiniCore`（简化版核心）
- [ ] 模块缓存清理机制
- [ ] 状态迁移支持
- [ ] 错误恢复机制

### Phase 3: 开发体验优化
- [ ] Web 调试界面
- [ ] 实时日志流
- [ ] 性能监控
- [ ] 断点调试支持

## 注意事项

1. **模块重载限制**
   - Python 的热重载有固有限制
   - 某些情况下需要完全重启
   - 需要清晰的错误提示

2. **资源清理**
   - 确保旧实例的资源被正确释放
   - 数据库连接、文件句柄等

3. **向后兼容**
   - 不影响现有的插件加载机制
   - 开发模式是可选的

## 总结

推荐使用**方案一（独立开发服务器）**，因为：

1. ✅ **开发体验好**：保存即重载，快速迭代
2. ✅ **实现简单**：不需要修改主程序
3. ✅ **环境隔离**：开发与生产分离
4. ✅ **可扩展**：易于添加调试工具

主要工作量在于：
1. 实现简化版的 mmc 核心（MiniCore）
2. 完善模块重载机制
3. 提供友好的开发界面

这个设计既满足了热重载的需求，又保持了系统的灵活性和可维护性。

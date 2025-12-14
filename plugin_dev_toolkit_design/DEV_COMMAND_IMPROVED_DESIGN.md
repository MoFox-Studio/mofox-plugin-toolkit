# mpdt dev 命令改进设计（主程序集成方案）

## 核心思路

你说得对！与其在 mpdt 中重新实现一套环境，**不如直接利用主程序的完整基础设施**。

## 改进方案：主程序开发模式

### 架构设计

```
┌─────────────────────────────────────────────────────┐
│              主程序 (mmc)                            │
│  ┌──────────────────────────────────────────────┐  │
│  │      PluginManager (已有)                    │  │
│  │  - reload_registered_plugin() ✅             │  │
│  │  - load/unload 机制 ✅                       │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │   DevModeManager (新增)                     │  │
│  │  - 监控开发中的插件                          │  │
│  │  - 文件变化触发重载                          │  │
│  │  - 开发模式配置管理                          │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                    ↑
                    │ 配置文件
┌─────────────────────────────────────────────────────┐
│            mpdt dev (简化)                          │
│  1. 创建 .dev-mode.toml 配置                       │
│  2. 启动主程序（带 --dev 参数）                    │
│  3. 提供开发工具（可选的Web界面等）                │
└─────────────────────────────────────────────────────┘
```

## 具体实现

### 1. 主程序中添加 DevModeManager

```python
# mmc/src/plugin_system/dev/dev_mode_manager.py

import asyncio
from pathlib import Path
from typing import Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from src.common.logger import get_logger

logger = get_logger("dev_mode", color_tag="plugin_hot_reload")


class PluginFileWatcher(FileSystemEventHandler):
    """插件文件监控处理器"""
    
    def __init__(self, callback):
        self.callback = callback
        self._pending_reload: Optional[asyncio.Task] = None
        
    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
            
        # 只关注相关文件
        if not event.src_path.endswith(('.py', '.toml')):
            return
            
        # 防抖：避免频繁触发
        if self._pending_reload and not self._pending_reload.done():
            self._pending_reload.cancel()
            
        self._pending_reload = asyncio.create_task(
            self._debounced_reload(event.src_path)
        )
    
    async def _debounced_reload(self, file_path: str):
        """防抖处理"""
        await asyncio.sleep(0.3)  # 300ms 延迟
        await self.callback(file_path)


class DevModeManager:
    """开发模式管理器
    
    负责监控开发中的插件并自动重载
    """
    
    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager
        self.watched_plugins: Set[str] = set()  # 监控的插件名称
        self.observers: dict[str, Observer] = {}  # 插件路径 -> Observer
        self.enabled = False
        
    def enable_dev_mode(self, plugin_names: list[str] | None = None):
        """启用开发模式
        
        Args:
            plugin_names: 要监控的插件列表，None表示监控所有已加载的插件
        """
        self.enabled = True
        
        if plugin_names is None:
            # 监控所有已加载的插件
            plugin_names = self.plugin_manager.list_loaded_plugins()
        
        for plugin_name in plugin_names:
            self.watch_plugin(plugin_name)
        
        logger.info(f"🔥 开发模式已启用，监控 {len(self.watched_plugins)} 个插件")
    
    def watch_plugin(self, plugin_name: str):
        """监控指定插件"""
        plugin_path = self.plugin_manager.get_plugin_path(plugin_name)
        if not plugin_path:
            logger.warning(f"无法找到插件路径: {plugin_name}")
            return
        
        if plugin_name in self.watched_plugins:
            logger.debug(f"插件已在监控列表中: {plugin_name}")
            return
        
        # 创建文件监控
        handler = PluginFileWatcher(
            callback=lambda fp: self._on_plugin_file_changed(plugin_name, fp)
        )
        
        observer = Observer()
        observer.schedule(handler, plugin_path, recursive=True)
        observer.start()
        
        self.observers[plugin_name] = observer
        self.watched_plugins.add(plugin_name)
        
        logger.info(f"📂 开始监控插件: {plugin_name} ({plugin_path})")
    
    def unwatch_plugin(self, plugin_name: str):
        """停止监控指定插件"""
        if plugin_name not in self.watched_plugins:
            return
        
        if observer := self.observers.get(plugin_name):
            observer.stop()
            observer.join()
            del self.observers[plugin_name]
        
        self.watched_plugins.remove(plugin_name)
        logger.info(f"停止监控插件: {plugin_name}")
    
    async def _on_plugin_file_changed(self, plugin_name: str, file_path: str):
        """文件变化回调"""
        file_name = Path(file_path).name
        logger.info(f"📝 检测到文件变化: {plugin_name}/{file_name}")
        logger.info(f"🔄 重新加载插件: {plugin_name}...")
        
        try:
            # 使用 PluginManager 的重载方法
            success = await self.plugin_manager.reload_registered_plugin(plugin_name)
            
            if success:
                logger.info(f"✅ 插件重载成功: {plugin_name}")
            else:
                logger.error(f"❌ 插件重载失败: {plugin_name}")
                
        except Exception as e:
            logger.error(f"❌ 重载插件时出错: {plugin_name} - {e}")
            import traceback
            logger.debug(traceback.format_exc())
    
    def disable_dev_mode(self):
        """禁用开发模式"""
        self.enabled = False
        
        # 停止所有监控
        for plugin_name in list(self.watched_plugins):
            self.unwatch_plugin(plugin_name)
        
        logger.info("开发模式已禁用")
    
    def get_status(self) -> dict:
        """获取开发模式状态"""
        return {
            "enabled": self.enabled,
            "watched_plugins": list(self.watched_plugins),
            "total_watched": len(self.watched_plugins),
        }


# 全局实例（延迟初始化）
_dev_mode_manager: Optional[DevModeManager] = None


def get_dev_mode_manager() -> DevModeManager:
    """获取开发模式管理器实例"""
    global _dev_mode_manager
    if _dev_mode_manager is None:
        from src.plugin_system.core.plugin_manager import plugin_manager
        _dev_mode_manager = DevModeManager(plugin_manager)
    return _dev_mode_manager
```

### 2. 在 PluginManager 中集成

```python
# mmc/src/plugin_system/core/plugin_manager.py

class PluginManager:
    def __init__(self):
        # ... 现有代码 ...
        self._dev_mode_enabled = False
        self._dev_mode_manager = None
    
    def enable_dev_mode(self, plugin_names: list[str] | None = None):
        """启用开发模式"""
        if not self._dev_mode_enabled:
            from src.plugin_system.dev.dev_mode_manager import get_dev_mode_manager
            self._dev_mode_manager = get_dev_mode_manager()
            self._dev_mode_enabled = True
        
        if self._dev_mode_manager:
            self._dev_mode_manager.enable_dev_mode(plugin_names)
    
    def disable_dev_mode(self):
        """禁用开发模式"""
        if self._dev_mode_manager:
            self._dev_mode_manager.disable_dev_mode()
            self._dev_mode_enabled = False
```

### 3. 主程序启动时支持开发模式

```python
# mmc/main.py

import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dev', action='store_true', help='启用开发模式')
    parser.add_argument('--dev-plugins', nargs='+', help='指定要监控的插件')
    args = parser.parse_args()
    
    # ... 初始化代码 ...
    
    # 加载插件
    plugin_manager.load_all_plugins()
    
    # 如果启用了开发模式
    if args.dev:
        logger.info("🚀 开发模式已激活")
        plugin_manager.enable_dev_mode(args.dev_plugins)
    
    # ... 启动机器人 ...
```

### 4. mpdt dev 命令简化

```python
# mpdt/commands/dev.py

import subprocess
import sys
from pathlib import Path
import toml
from rich.console import Console

console = Console()


def dev_command(
    plugin_path: Path,
    mmc_path: Path | None = None,
    watch_only: bool = False,
):
    """启动开发模式
    
    Args:
        plugin_path: 插件路径
        mmc_path: mmc 主程序路径（可选）
        watch_only: 只监控，不启动主程序
    """
    
    # 1. 检测插件名称
    plugin_name = plugin_path.name
    console.print(f"[green]📦 插件: {plugin_name}[/green]")
    console.print(f"[cyan]📂 路径: {plugin_path}[/cyan]")
    
    # 2. 查找 mmc 主程序
    if not mmc_path:
        mmc_path = _find_mmc_path()
        if not mmc_path:
            console.print("[red]❌ 无法找到 mmc 主程序[/red]")
            console.print("[yellow]提示: 使用 --mmc-path 指定主程序路径[/yellow]")
            return
    
    console.print(f"[green]🎯 主程序: {mmc_path}[/green]")
    
    # 3. 创建软链接（如果插件不在 plugins 目录中）
    plugins_dir = mmc_path / "plugins"
    plugin_link = plugins_dir / plugin_name
    
    if not plugin_link.exists():
        console.print(f"[yellow]🔗 创建软链接到 {plugins_dir}[/yellow]")
        try:
            plugin_link.symlink_to(plugin_path, target_is_directory=True)
        except Exception as e:
            console.print(f"[red]创建软链接失败: {e}[/red]")
            console.print("[yellow]将尝试直接使用路径...[/yellow]")
    
    # 4. 启动主程序（开发模式）
    if not watch_only:
        console.print("\n[bold green]🚀 启动开发服务器...[/bold green]\n")
        
        cmd = [
            sys.executable,
            str(mmc_path / "main.py"),
            "--dev",
            "--dev-plugins", plugin_name
        ]
        
        try:
            subprocess.run(cmd, cwd=str(mmc_path))
        except KeyboardInterrupt:
            console.print("\n[yellow]👋 开发服务器已停止[/yellow]")
    else:
        # 只监控模式（高级用法）
        console.print("[cyan]👀 监控模式（主程序需单独启动）[/cyan]")
        # TODO: 实现独立的文件监控


def _find_mmc_path() -> Path | None:
    """自动查找 mmc 主程序路径"""
    # 尝试几个常见位置
    search_paths = [
        Path.cwd() / "mmc",  # 当前目录的 mmc 子目录
        Path.cwd().parent / "mmc",  # 父目录的 mmc
        Path(__file__).parent.parent.parent / "mmc",  # toolkit 同级
    ]
    
    for path in search_paths:
        if path.exists() and (path / "main.py").exists():
            return path
    
    return None
```

### 5. CLI 集成

```python
# mpdt/cli.py

@cli.command()
@click.option("--mmc-path", type=click.Path(exists=True), help="mmc 主程序路径")
@click.option("--watch-only", is_flag=True, help="只监控文件，不启动主程序")
@click.pass_context
def dev(ctx: click.Context, mmc_path: str | None, watch_only: bool) -> None:
    """启动开发模式，自动重载插件"""
    
    plugin_path = Path.cwd()
    
    # 检查是否是有效的插件目录
    if not (plugin_path / "plugin.py").exists():
        console.print("[red]❌ 当前目录不是有效的插件目录[/red]")
        return
    
    from mpdt.commands.dev import dev_command
    
    dev_command(
        plugin_path=plugin_path,
        mmc_path=Path(mmc_path) if mmc_path else None,
        watch_only=watch_only,
    )
```

## 使用流程

### 方式一：自动启动（推荐）

```bash
# 在插件目录中
cd my_awesome_plugin

# mpdt 自动找到 mmc 并启动
mpdt dev

# 或者指定 mmc 路径
mpdt dev --mmc-path /path/to/mmc
```

**mpdt 会：**
1. 创建软链接到 mmc/plugins
2. 启动 mmc（带 --dev 参数）
3. mmc 自动监控该插件并重载

### 方式二：手动启动

```bash
# 1. 手动启动 mmc（开发模式）
cd mmc
python main.py --dev --dev-plugins my_awesome_plugin

# 2. 编辑插件代码
# 保存后自动重载
```

### 方式三：监控指定插件

```bash
# 只监控特定插件
python main.py --dev --dev-plugins plugin1 plugin2
```

## 优势对比

### ✅ 新方案的优势

1. **无需导入问题**
   - 直接在主程序运行
   - 使用完整的真实环境
   - 所有依赖都已就绪

2. **利用现有基础设施**
   - PluginManager 已有重载机制
   - Component Registry 已有注册/注销
   - 不需要重新实现

3. **实现简单**
   - DevModeManager 只负责文件监控
   - 重载逻辑复用现有代码
   - mpdt dev 只是一个启动器

4. **完全真实的测试环境**
   - 所有功能都可以正常使用
   - 可以连接真实的适配器
   - 可以测试消息处理流程

### 📊 方案对比

| 特性 | 方案一（独立服务器） | 方案二（主程序集成）✅ |
|------|-------------------|---------------------|
| 实现复杂度 | 高（需要模拟环境） | 低（利用现有代码） |
| 测试环境 | 简化版 | 完整真实环境 |
| 导入问题 | 需要处理 sys.path | 无需处理 |
| 开发体验 | 独立，快速启动 | 与主程序一起运行 |
| 资源占用 | 低 | 中等（主程序） |

## 依赖管理

```toml
# mmc/pyproject.toml

[project.optional-dependencies]
dev = [
    "watchdog>=3.0.0",  # 文件监控
]
```

## 高级功能（可选）

### 1. HTTP API 控制

在主程序中添加开发模式控制接口：

```python
# mmc/src/web/dev_routes.py

from fastapi import APIRouter
from src.plugin_system.dev.dev_mode_manager import get_dev_mode_manager

router = APIRouter(prefix="/dev", tags=["开发模式"])

@router.post("/reload/{plugin_name}")
async def reload_plugin(plugin_name: str):
    """手动重载插件"""
    from src.plugin_system.core.plugin_manager import plugin_manager
    success = await plugin_manager.reload_registered_plugin(plugin_name)
    return {"success": success}

@router.get("/status")
def get_dev_status():
    """获取开发模式状态"""
    dev_manager = get_dev_mode_manager()
    return dev_manager.get_status()
```

然后 mpdt 可以通过 HTTP 控制：

```bash
# 手动触发重载
mpdt reload my_plugin

# 查看状态
mpdt dev-status
```

### 2. 配置文件支持

```toml
# .dev-mode.toml

[dev]
enabled = true
plugins = ["my_plugin"]
watch_config = true  # 监控配置文件
auto_reload_interval = 0.3  # 防抖延迟（秒）
```

## 实现路线图

### Phase 1: 基础功能 ✅
- [x] 实现 DevModeManager
- [x] 集成到 PluginManager
- [x] 主程序支持 --dev 参数
- [x] mpdt dev 命令（启动器）

### Phase 2: 增强体验
- [ ] 改进错误提示
- [ ] 支持配置文件
- [ ] 添加 Web 控制界面
- [ ] 状态查询命令

### Phase 3: 高级功能
- [ ] 多插件协同开发
- [ ] 断点调试支持
- [ ] 性能分析工具

## 总结

**这个改进方案的核心优势：**

1. ✅ **直接利用主程序** - 不需要导入和模拟
2. ✅ **实现简单** - 只需添加文件监控层
3. ✅ **真实环境** - 完整的测试能力
4. ✅ **易于维护** - 复用现有代码

你说得对，这个方案确实比独立服务器更实用！

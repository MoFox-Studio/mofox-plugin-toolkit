# mpdt dev 命令使用指南

## 快速开始

### 1. 首次配置

```bash
# 运行配置向导（仅需一次）
mpdt config init
```

按提示输入：
- **mmc 主程序路径**: 例如 `E:/delveoper/mmc010/mmc`
- **虚拟环境类型**: 选择 `venv`、`uv`、`conda`、`poetry` 或 `none`
- **虚拟环境路径**: 例如 `E:/delveoper/mmc010/venv`

### 2. 验证配置

```bash
# 查看配置
mpdt config show

# 测试配置
mpdt config test
```

### 3. 启动开发模式

```bash
# 进入插件目录
cd your_plugin

# 启动开发模式
mpdt dev
```

## 工作流程

```
┌─────────────────────────────────────┐
│  1. 解析插件名称                     │
│     从 plugin.py 提取 plugin_name   │
├─────────────────────────────────────┤
│  2. 注入 DevBridge 插件              │
│     复制到 mmc/plugins/dev_bridge    │
├─────────────────────────────────────┤
│  3. 启动主程序                       │
│     使用配置的虚拟环境               │
├─────────────────────────────────────┤
│  4. 连接发现服务器 (端口 12318)     │
│     获取主程序动态端口               │
├─────────────────────────────────────┤
│  5. 建立 WebSocket 连接              │
│     连接开发模式接口                 │
├─────────────────────────────────────┤
│  6. 等待插件加载通知                 │
│     确认插件是否成功加载             │
├─────────────────────────────────────┤
│  7. 启动文件监控                     │
│     监控 .py 文件变化                │
├─────────────────────────────────────┤
│  8. 自动重载                         │
│     文件变化 → 发送重载指令          │
└─────────────────────────────────────┘
```

## 配置命令

### 查看配置
```bash
mpdt config show
```

### 修改配置
```bash
# 设置 mmc 路径
mpdt config set-mmc /path/to/mmc

# 设置虚拟环境
mpdt config set-venv /path/to/venv --type venv
mpdt config set-venv /path/to/.venv --type uv
mpdt config set-venv --type none  # 使用系统 Python
```

### 测试配置
```bash
mpdt config test
```

## 开发模式命令

### 基本用法
```bash
# 在插件目录中
mpdt dev
```

### 指定路径
```bash
# 指定插件路径
mpdt dev --plugin-path /path/to/plugin

# 指定 mmc 路径（临时覆盖配置）
mpdt dev --mmc-path /path/to/mmc

# 同时指定
mpdt dev --plugin-path /path/to/plugin --mmc-path /path/to/mmc
```

## 输出示例

```
┌──────────────────────────────────────────┐
│ 🚀 MoFox Plugin Dev Server               │
│                                           │
│ 📂 目录: my_awesome_plugin                │
│ 📍 路径: E:/dev/my_awesome_plugin         │
└──────────────────────────────────────────┘

✓ 插件名: awesome_plugin
🔗 注入开发模式插件...
✓ DevBridge 插件已注入: E:/mmc/plugins/dev_bridge
🚀 启动主程序: E:/mmc/bot.py
✓ 主程序已启动
⏳ 等待主程序就绪...
✓ 发现主程序: http://127.0.0.1:8000
🔌 连接开发模式接口...
✓ 已连接到主程序
⏳ 等待插件加载...
✓ 插件已加载: awesome_plugin
👀 开始监控: E:/dev/my_awesome_plugin

✨ 开发服务器就绪！
监控文件变化中... (Ctrl+C 退出)

📝 检测到变化: plugin.py
🔄 重新加载 awesome_plugin...
✅ 插件 awesome_plugin 重载成功
```

## 架构说明

### DevBridge 插件

- **位置**: `mofox-plugin-toolkit/mpdt/dev/bridge_plugin/`
- **临时注入**: 启动时复制到 `mmc/plugins/dev_bridge/`
- **自动清理**: 退出时删除

### 发现服务器

- **固定端口**: `12318`
- **作用**: 提供主程序的动态端口信息
- **端点**:
  - `GET /api/health` - 健康检查
  - `GET /api/server-info` - 获取主程序地址

### WebSocket 通信

- **端点**: `ws://{host}:{port}/plugin-api/dev_bridge/dev_bridge_router/ws`
- **消息格式**:

```json
// 客户端 → 服务器
{"command": "reload", "plugin_name": "xxx"}
{"command": "status"}
{"command": "ping"}

// 服务器 → 客户端
{"type": "reload_result", "success": true, "message": "..."}
{"type": "plugins_loaded", "loaded": [...], "failed": [...]}
{"type": "pong"}
```

## 常见问题

### Q: 插件名称和目录名不一致？

**A**: mpdt 会自动解析 `plugin.py` 中的 `plugin_name` 属性，使用正确的插件名进行重载。

```python
# 目录名: my_awesome_plugin
# 插件名: awesome_plugin

class MyPlugin(BasePlugin):
    plugin_name = "awesome_plugin"  # 使用这个名称
```

### Q: 虚拟环境类型选择？

**A**: 根据你的项目选择：
- **venv**: 标准 Python venv
- **uv**: uv 创建的虚拟环境
- **conda**: Conda 环境
- **poetry**: Poetry 管理的项目
- **none**: 使用系统 Python

### Q: 主程序端口被占用？

**A**: 发现服务器会自动处理端口切换。如果 8000 被占用，主程序会切换到 8001，mpdt 会自动获取正确的端口。

### Q: 配置文件保存在哪里？

**A**: `~/.mpdt/config.toml` (用户主目录下的 .mpdt 文件夹)

### Q: 如何退出开发模式？

**A**: 按 `Ctrl+C`，mpdt 会：
1. 停止文件监控
2. 关闭 WebSocket 连接
3. 停止主程序
4. 清理 DevBridge 插件

## 技术特性

✅ **插件系统集成** - 使用 BaseRouterComponent 提供 WebSocket 支持  
✅ **智能端口发现** - 通过发现服务器动态获取主程序端口  
✅ **准确的插件识别** - AST 解析确保使用正确的插件名  
✅ **环境适配** - 支持多种虚拟环境类型  
✅ **文件监控** - watchdog 实时监控文件变化  
✅ **防抖处理** - 避免频繁重载  
✅ **双向通信** - WebSocket 实时反馈重载状态  
✅ **优雅清理** - 自动清理临时注入的插件  

## 依赖要求

```toml
dependencies = [
    "click>=8.1.7",
    "rich>=13.7.0",
    "watchdog>=3.0.0",
    "websockets>=12.0",
    "aiohttp>=3.9.0",
    "uvicorn>=0.24.0",
    "fastapi>=0.104.0",
    "tomli>=2.0.1",
    "tomli-w>=1.0.0",
]
```

## 下一步

1. ✅ 基础功能已完成
2. 🚧 可选增强功能：
   - 实时日志流
   - 多插件同时开发
   - 断点调试支持
   - 性能分析工具

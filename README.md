# MoFox Plugin Dev Toolkit (MPDT)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.1-orange.svg)](https://github.com/MoFox-Studio/mofox-plugin-toolkit)

一个类似于 Vite 的 Python 开发工具，专门为 MoFox-Bot 插件系统设计，提供快速创建、开发、检查和热重载的完整工具链。

## ✨ 特性

### 核心功能

- 🚀 **快速初始化** - 一键创建标准化的插件项目结构，支持 6 种模板（basic、action、tool、plus_command、full、adapter）
- 🎨 **代码生成** - 快速生成 8 种组件类型（Action、Tool、Event、Adapter、Prompt、PlusCommand、Router、Chatter），始终生成异步方法
- 🔍 **完整的静态检查系统** - 集成 6 层验证体系：
  - ✅ **结构检查** - 验证插件目录结构、必需文件和推荐文件
  - ✅ **元数据检查** - 检查 `__plugin_meta__` 配置的完整性和正确性
  - ✅ **组件检查** - 验证组件注册、命名规范和导入路径
  - ✅ **配置检查** - 检查 `config.toml` 的语法和必需配置
  - ✅ **类型检查** - 使用 mypy 进行严格的类型检查
  - ✅ **代码风格检查** - 使用 ruff 检查代码规范并自动修复
- 🔥 **热重载开发模式** - 基于 WebSocket 的实时热重载系统：
  - 🔄 文件变化自动检测和重载
  - 📡 通过 WebSocket 与主程序通信
  - 🚦 自动管理插件生命周期
  - 📊 实时显示重载状态和日志
- 🎯 **Git 集成** - 支持自动初始化 Git 仓库和提取用户信息
- 🎨 **美观的交互界面** - 基于 Rich 和 Questionary 的现代化命令行体验
- 📜 **多种许可证** - 支持 GPL-v3.0、MIT、Apache-2.0、BSD-3-Clause

## 📦 安装

```bash
# 从源码安装
cd mofox-plugin-toolkit
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

## 🚀 快速开始

### 1. 创建新插件

```bash
# 交互式创建
mpdt init

# 或直接指定插件名和模板
mpdt init my_awesome_plugin --template action

# 创建带示例和文档的完整插件
mpdt init my_plugin --template full --with-examples --with-docs

# 指定作者和许可证
mpdt init my_plugin --author "Your Name" --license MIT
```

支持的模板类型：
- `basic` - 基础插件模板（最小化结构）
- `action` - 包含 Action 组件的模板
- `tool` - 包含 Tool 组件的模板
- `plus_command` - 包含 PlusCommand 组件的模板
- `full` - 完整功能模板（包含多种组件示例）
- `adapter` - 适配器模板（用于创建平台适配器）

### 2. 生成组件

```bash
cd my_awesome_plugin

# 交互式生成（推荐）- 通过问答选择组件类型和配置
mpdt generate

# 生成 Action 组件
mpdt generate action SendMessage --description "发送消息"

# 生成 Tool 组件
mpdt generate tool MessageFormatter --description "消息格式化工具"

# 生成 PlusCommand 组件（用于 Plus 系统）
mpdt generate plus-command CustomCommand --description "自定义 Plus 命令"

# 生成其他组件
mpdt generate event MessageReceived --description "消息接收事件处理器"
mpdt generate adapter CustomAdapter --description "自定义适配器"
mpdt generate prompt SystemPrompt --description "系统提示词"
mpdt generate router MessageRouter --description "消息路由器"
mpdt generate chatter ChatHandler --description "对话处理器"
```

**支持的组件类型**：
- `action` - Action 组件（用于执行具体操作）
- `tool` - Tool 组件（可供 AI 调用的工具）
- `event` - Event Handler 组件（事件处理器）
- `adapter` - Adapter 组件（平台适配器）
- `prompt` - Prompt 组件（提示词模板）
- `plus-command` - PlusCommand 组件（Plus 系统命令）
- `router` - Router 组件（路由器）
- `chatter` - Chatter 组件（对话处理器）

**注意**：所有生成的组件方法都是异步的（async），符合 MoFox-Bot 的异步架构。

### 3. 开发模式（热重载）

```bash
# 启动开发模式（需要先配置 MoFox-Bot 主程序路径）
mpdt dev

# 首次运行会提示配置
# 之后会自动：
# 1. 注入开发桥接插件到主程序
# 2. 启动主程序
# 3. 建立 WebSocket 连接
# 4. 监控文件变化
# 5. 自动热重载插件

# 开发模式功能：
# - 🔄 文件保存后自动重载插件
# - 📊 实时显示重载状态和耗时
# - 🚦 自动管理插件生命周期
# - 📝 实时查看主程序日志
# - ⚡ 无需手动重启主程序
```

### 4. 检查插件

```bash
# 运行所有检查（包含 6 个检查器）
mpdt check

# 自动修复可修复的问题
mpdt check --fix

# 只显示错误级别的问题
mpdt check --level error

# 生成 Markdown 格式的检查报告
mpdt check --report markdown --output check_report.md

# 跳过特定检查
mpdt check --no-type        # 跳过类型检查
mpdt check --no-style       # 跳过代码风格检查
mpdt check --no-component   # 跳过组件检查

# 组合使用
mpdt check --fix --level warning --report markdown -o report.md
```

**检查项说明**：
- **结构检查** (structure) - 验证目录结构、必需文件（`__init__.py`、`plugin.py`、`config/config.toml`）和推荐文件（`README.md`、`pyproject.toml`、`tests/`）
- **元数据检查** (metadata) - 检查 `__plugin_meta__` 的存在性、类型和必需字段（name、description、usage）
- **组件检查** (component) - 验证组件注册、命名规范、导入路径和类型正确性
- **配置检查** (config) - 检查 `config.toml` 的语法、必需配置项和数据类型
- **类型检查** (type) - 使用 mypy 进行严格的类型检查，确保类型安全
- **代码风格检查** (style) - 使用 ruff 检查代码规范，支持自动修复格式问题

## 📖 命令参考

### `mpdt init` - 初始化插件

创建新的插件项目，支持多种模板和自动化配置。

```bash
mpdt init [PLUGIN_NAME] [OPTIONS]

选项:
  -t, --template TEXT       模板类型: basic, action, tool, plus_command, full, adapter
  -a, --author TEXT         作者名称（可从 Git 配置自动获取）
  -l, --license TEXT        开源协议: GPL-v3.0, MIT, Apache-2.0, BSD-3-Clause
  --with-examples           包含示例代码和用法说明
  --with-docs              创建文档目录和基础文档文件
  --init-git               初始化 Git 仓库（默认）
  --no-init-git            不初始化 Git 仓库
  -o, --output PATH        输出目录（默认为当前目录）

示例:
  mpdt init my_plugin                           # 交互式创建
  mpdt init my_plugin -t action -a "张三"       # 指定参数创建
  mpdt init my_plugin -t full --with-examples   # 创建完整模板
```

### `mpdt generate` - 生成组件

生成插件组件代码，始终生成异步方法，支持交互式和命令行两种模式。

```bash
mpdt generate [COMPONENT_TYPE] [COMPONENT_NAME] [OPTIONS]

组件类型:
  action          Action 组件 - 执行具体操作
  tool            Tool 组件 - 可供 AI 调用的工具
  event           Event Handler 组件 - 事件处理器
  adapter         Adapter 组件 - 平台适配器
  prompt          Prompt 组件 - 提示词模板
  plus-command    PlusCommand 组件 - Plus 系统命令
  router          Router 组件 - 路由器
  chatter         Chatter 组件 - 对话处理器

选项:
  -d, --description TEXT    组件描述信息
  -o, --output PATH        输出目录（默认自动选择对应组件目录）
  -f, --force              覆盖已存在的文件

示例:
  mpdt generate                                  # 交互式生成
  mpdt generate action SendMsg -d "发送消息"    # 命令行生成
  mpdt generate tool Formatter --force           # 强制覆盖
```

**注意**：不提供参数时将进入交互式问答模式，更易于使用。

### `mpdt dev` - 开发模式

启动带热重载的开发模式，实时监控文件变化并自动重载插件。

```bash
mpdt dev [OPTIONS]
```

功能特性:
  - 🔄 自动检测文件变化并热重载
  - 📡 基于 WebSocket 与主程序通信
  - 🚦 自动管理插件生命周期
  - 📊 实时显示重载状态和耗时
  - 📝 显示主程序运行日志

首次运行:
  首次运行会提示配置 MoFox 主程序路径
  配置将保存到 ~/.mpdt/config.toml 或者 

工作流程:
  1. 自动注入开发桥接插件到主程序
  2. 启动主程序并建立连接
  3. 监控插件目录的文件变化
  4. 检测到变化时通过 WebSocket 通知主程序重载
  5. 主程序自动卸载旧版本并加载新版本

示例:
  mpdt dev                # 在插件目录中运行

### `mpdt check` - 检查插件

对插件进行全面的静态检查，包括 6 个检查器。

```bash
mpdt check [PATH] [OPTIONS]

选项:
  -l, --level TEXT         显示问题级别: error, warning, info（默认显示所有）
  --fix                    自动修复可修复的问题（主要是代码风格）
  --report TEXT            报告格式: console（默认）, markdown
  -o, --output PATH        报告输出路径（仅用于 markdown 格式）
  --no-structure           跳过结构检查
  --no-metadata            跳过元数据检查
  --no-component           跳过组件检查
  --no-config              跳过配置检查
  --no-type                跳过类型检查
  --no-style               跳过代码风格检查

检查器说明:
  structure   - 检查目录结构、必需文件和推荐文件
  metadata    - 检查 __plugin_meta__ 的完整性
  component   - 检查组件注册和命名规范
  config      - 检查 config.toml 配置文件
  type        - 使用 mypy 进行类型检查
  style       - 使用 ruff 进行代码风格检查

示例:
  mpdt check                                    # 运行所有检查
  mpdt check --fix                             # 自动修复问题
  mpdt check --level error                     # 只显示错误
  mpdt check --report markdown -o report.md    # 生成报告
  mpdt check --no-type --no-style              # 跳过耗时检查
```

---

## 🏗️ 插件结构

MPDT 创建的插件遵循 MoFox-Bot 标准结构：

```
my_plugin/                   # 插件根目录
├── __init__.py              # ⭐ 插件元数据（必需）
│                            #    必须包含 __plugin_meta__ 变量
├── plugin.py                # ⭐ 插件主类（必需）
│                            #    继承自 BasePlugin
├── config/                  # ⭐ 配置目录（必需）
│   └── config.toml          # ⭐ 配置文件（必需）
├── components/              # 组件目录（可选但推荐）
│   ├── actions/             # Action 组件目录
│   │   └── send_message.py
│   ├── tools/               # Tool 组件目录
│   │   └── formatter.py
│   ├── events/              # Event Handler 目录
│   ├── adapters/            # Adapter 目录
│   ├── prompts/             # Prompt 目录
│   ├── plus_commands/       # PlusCommand 目录
│   ├── routers/             # Router 目录
│   └── chatters/            # Chatter 目录
├── utils/                   # 工具函数目录（可选）
│   └── helpers.py
├── tests/                   # 📋 测试目录（推荐）
│   ├── conftest.py
│   └── test_plugin.py
├── docs/                    # 📋 文档目录（推荐）
│   └── README.md
├── pyproject.toml           # 📋 项目配置（推荐）
├── requirements.txt         # 📋 依赖列表（推荐）
├── .gitignore              # Git 忽略文件
├── LICENSE                 # 开源许可证
└── README.md               # 📋 插件说明（推荐）
```


## 🎯 开发状态

### ✅ 已完成功能（v0.2.1）

#### 1. ✅ 插件初始化 (`mpdt init`)
- 支持 6 种模板类型
- 交互式问答模式
- Git 自动初始化和用户信息提取
- 多种开源协议支持
- 自动生成标准化项目结构

#### 2. ✅ 组件生成 (`mpdt generate`)
- 支持 8 种组件类型
- 所有方法自动生成为异步
- 自动更新插件主类注册代码
- 交互式和命令行两种模式
- 组件文件自动放置到正确目录

#### 3. ✅ 静态检查系统 (`mpdt check`)
- **结构验证器** - 目录和文件完整性检查
- **元数据验证器** - `__plugin_meta__` 验证
- **组件验证器** - 组件注册和规范检查
- **配置验证器** - `config.toml` 验证
- **类型检查器** - mypy 集成，严格类型检查
- **代码风格检查器** - ruff 集成，自动修复
- 支持生成 Markdown 格式报告
- 灵活的级别过滤（error/warning/info）

#### 4. ✅ 热重载开发模式 (`mpdt dev`)
- 基于 WebSocket 的实时通信
- 自动注入开发桥接插件
- 文件变化自动检测（使用 watchdog）
- 插件生命周期自动管理
- 实时状态显示和日志查看
- 支持主程序自动启动和停止

### 🚧 计划中功能

#### 测试框架 (`mpdt test`)
- 自动运行插件测试
- 覆盖率报告生成
- 并行测试执行
- 测试报告输出

#### 构建打包 (`mpdt build`)
- 插件打包为发布格式
- 版本号自动管理
- 依赖项打包
- 多种打包格式支持

#### 配置管理
- 项目级配置文件 `.mpdtrc.toml`
- 全局配置管理
- 配置验证和迁移

---

## 🤝 贡献指南

欢迎贡献代码和建议！

### 贡献方式
1. Fork 项目仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/MoFox-Studio/mofox-plugin-toolkit.git
cd mofox-plugin-toolkit

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
mypy mpdt
```

---

## 📄 许可证

本项目采用 GPL-3.0-or-later 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🔗 相关链接

- [MoFox-Bot 主仓库](https://github.com/MoFox-Studio/MoFox-Core)
- [插件开发文档](https://docs.mofox.studio/plugin-development)
- [问题反馈](https://github.com/MoFox-Studio/mofox-plugin-toolkit/issues)
- [更新日志](CHANGELOG.md)

---

## 📊 技术栈

### 核心框架
- **CLI 框架**: [Click](https://click.palletsprojects.com/) - 强大的命令行工具框架
- **交互式界面**: [Questionary](https://github.com/tmbo/questionary) - 美观的交互式问答
- **美化输出**: [Rich](https://github.com/Textualize/rich) - 富文本终端输出

### 开发工具
- **模板引擎**: [Jinja2](https://jinja.palletsprojects.com/) - 灵活的模板系统
- **配置管理**: [TOML](https://toml.io/), [Pydantic](https://docs.pydantic.dev/) - 配置解析和验证
- **代码检查**: 
  - [Mypy](https://mypy.readthedocs.io/) - 静态类型检查
  - [Ruff](https://docs.astral.sh/ruff/) - 快速的 Python 代码检查器和格式化工具

### 开发模式
- **文件监控**: [Watchdog](https://python-watchdog.readthedocs.io/) - 跨平台文件系统监控
- **WebSocket**: [websockets](https://websockets.readthedocs.io/) - 异步 WebSocket 库
- **HTTP 客户端**: [aiohttp](https://docs.aiohttp.org/) - 异步 HTTP 客户端/服务器

---

## 🛠️ 完整依赖清单

```toml
dependencies = [
    "click>=8.1.7",         # CLI 框架
    "rich>=13.7.0",         # 终端美化
    "questionary>=2.0.1",   # 交互式问答
    "jinja2>=3.1.2",        # 模板引擎
    "toml>=0.10.2",         # TOML 解析
    "tomli>=2.0.1",         # TOML 读取
    "tomli-w>=1.0.0",       # TOML 写入
    "pydantic>=2.5.0",      # 数据验证
    "watchdog>=3.0.0",      # 文件监控
    "websockets>=12.0",     # WebSocket
    "aiohttp>=3.9.0",       # 异步 HTTP
    "uvicorn>=0.24.0",      # ASGI 服务器
    "fastapi>=0.104.0",     # Web 框架
    "ruff>=0.1.6",          # 代码检查
    "mypy>=1.7.0"           # 类型检查
]
```

---

## 💡 常见问题

### Q: 如何配置开发模式？
A: 首次运行 `mpdt dev` 时会提示输入 MMC 主程序路径，配置会保存到 `~/.mpdt/config.toml`。

### Q: 检查器报错怎么办？
A: 首先尝试使用 `mpdt check --fix` 自动修复。如果仍有问题，查看具体错误信息和建议。

### Q: 如何跳过某些检查？
A: 使用 `--no-<checker>` 选项，例如 `mpdt check --no-type --no-style`。

### Q: 生成的组件在哪里？
A: 组件会自动放置到对应的目录，例如 Action 放在 `components/actions/`。

### Q: 如何更新工具？
A: 如果是从源码安装，执行 `git pull && pip install -e .`。

---

## 📝 更新日志

### v0.2.1 (2025-12-14)
- ✅ 实现完整的热重载开发模式 (`mpdt dev`)
- ✅ 添加 WebSocket 通信机制
- ✅ 实现开发桥接插件自动注入
- ✅ 改进文件监控和自动重载
- ✅ 优化用户交互体验

### v0.2.0
- ✅ 完成 6 个检查器实现
- ✅ 添加自动修复功能
- ✅ 支持 Markdown 报告生成
- ✅ 改进错误提示和建议

### v0.1.x
- ✅ 基础插件初始化功能
- ✅ 组件生成功能
- ✅ 交互式问答模式

---

## 🎉 致谢

感谢所有为 MoFox Plugin Dev Toolkit 贡献的开发者！

---

<div align="center">

**[⬆ 回到顶部](#mofox-plugin-dev-toolkit-mpdt)**

Made with ❤️ by MoFox-Studio

</div>

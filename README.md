# MoFox Plugin Dev Toolkit (MPDT)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.4-orange.svg)](https://github.com/MoFox-Studio/mofox-plugin-toolkit)

一个类似于 Vite 的 Python 开发工具，专门为 MoFox-Bot 插件系统设计，提供快速创建、开发和检查插件的完整工具链。

## ✨ 特性

- 🚀 **快速初始化** - 一键创建标准化的插件项目结构，支持多种模板（basic、action、tool、command、full、adapter）
- 🎨 **代码生成** - 快速生成 Action、Command、Tool、Event、Adapter、Prompt、PlusCommand、Router、Chatter 等组件（始终生成异步方法）
- 🔍 **静态检查** - 集成多层次验证系统：
  - ✅ 结构检查 - 验证插件目录结构和必需文件
  - ✅ 元数据检查 - 检查 `__plugin_meta__` 配置
  - ✅ 组件检查 - 验证组件注册和命名规范
  - ✅ 配置检查 - 检查 `config.toml` 配置文件
  - ✅ 类型检查 - 使用 mypy 进行类型检查
  - ✅ 代码风格检查 - 使用 ruff 检查代码规范
  - ✅ 自动修复 - 自动修复可修复的代码问题
- 📦 **依赖管理** - 自动管理插件依赖关系
- 🎯 **Git 集成** - 支持自动初始化 Git 仓库和提取 Git 用户信息
- 🎨 **丰富的交互** - 基于 questionary 的美观交互式命令行界面
- � **多种许可证** - 支持 GPL-v3.0、MIT、Apache-2.0、BSD-3-Clause

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
- `basic` - 基础插件模板
- `action` - 包含 Action 组件的模板
- `tool` - 包含 Tool 组件的模板
- `command` - 包含 Command 组件的模板
- `full` - 完整功能模板
- `adapter` - 适配器模板

### 2. 生成组件

```bash
cd my_awesome_plugin

# 交互式生成（推荐）
mpdt generate

# 生成 Action 组件
mpdt generate action SendMessage --description "发送消息"

# 生成 Tool 组件
mpdt generate tool MessageFormatter

# 生成 Command 组件
mpdt generate command Help

# 生成其他组件
mpdt generate event MessageReceived
mpdt generate adapter CustomAdapter
mpdt generate prompt SystemPrompt
mpdt generate plus-command CustomCommand
mpdt generate router MessageRouter
mpdt generate chatter ChatHandler
```

**注意**：所有生成的组件方法都是异步的（async）。

### 3. 检查插件

```bash
# 运行所有检查
mpdt check

# 自动修复问题
mpdt check --fix

# 只显示错误级别
mpdt check --level error

# 生成 Markdown 报告
mpdt check --report markdown --output check_report.md

# 跳过特定检查
mpdt check --no-type --no-style
```

检查项包括：
- 结构检查（structure）- 验证目录和文件结构
- 元数据检查（metadata）- 检查 `__plugin_meta__`
- 组件检查（component）- 验证组件注册
- 配置检查（config）- 检查配置文件
- 类型检查（type）- mypy 类型检查
- 代码风格检查（style）- ruff 代码规范检查

## 📖 命令参考

### `mpdt init` - 初始化插件

创建新的插件项目。

```bash
mpdt init [PLUGIN_NAME] [OPTIONS]

选项:
  -t, --template TEXT    模板类型: basic, action, tool, command, full, adapter
  -a, --author TEXT      作者名称
  -l, --license TEXT     开源协议: GPL-v3.0, MIT, Apache-2.0, BSD-3-Clause
  --with-examples        包含示例代码
  --with-docs           创建文档文件
  --init-git            初始化 Git 仓库
  --no-init-git         不初始化 Git 仓库
  -o, --output PATH     输出目录
```

### `mpdt generate` - 生成组件

生成插件组件代码（始终生成异步方法）。

```bash
mpdt generate [COMPONENT_TYPE] [COMPONENT_NAME] [OPTIONS]

组件类型:
  action          Action 组件
  tool            Tool 组件
  event           Event Handler 组件
  adapter         Adapter 组件
  prompt          Prompt 组件
  plus-command    PlusCommand 组件
  router          Router 路由组件
  chatter         Chatter 聊天组件

选项:
  -d, --description TEXT  组件描述
  -o, --output PATH      输出目录
  -f, --force            覆盖已存在的文件
```

**注意**：如果不提供参数，将进入交互式问答模式。

### `mpdt check` - 检查插件

对插件进行静态检查。

```bash
mpdt check [PATH] [OPTIONS]

选项:
  -l, --level TEXT       显示级别: error, warning, info
  --fix                  自动修复问题
  --report TEXT          报告格式: console, markdown
  -o, --output PATH      报告输出路径
  --no-structure         跳过结构检查
  --no-metadata          跳过元数据检查
  --no-component         跳过组件检查
  --no-type             跳过类型检查
  --no-style            跳过代码风格检查
  --no-security         跳过安全检查
```

### `mpdt test` - 运行测试 ⚠️ 未实现

运行插件测试（计划中）。

```bash
mpdt test [TEST_PATH] [OPTIONS]

选项:
  -c, --coverage         生成覆盖率报告
  --min-coverage INT     最低覆盖率要求
  -v, --verbose          详细输出
  -m, --markers TEXT     只运行特定标记的测试
  -k, --keyword TEXT     只运行匹配关键词的测试
  -n, --parallel INT     并行运行测试
```

### `mpdt dev` - 开发模式 ⚠️ 未实现

启动开发模式，监控文件变化（计划中）。

```bash
mpdt dev [OPTIONS]

选项:
  -p, --port INT         开发服务器端口
  --host TEXT           绑定的主机地址
  --no-reload           禁用自动重载
  --debug               启用调试模式
```

### `mpdt build` - 构建插件 ⚠️ 未实现

构建和打包插件（计划中）。

```bash
mpdt build [OPTIONS]

选项:
  -o, --output PATH      输出目录
  --with-docs           包含文档
  --format TEXT         构建格式: zip, tar.gz, wheel
  --bump TEXT           升级版本: major, minor, patch
```

## 🏗️ 插件结构

MPDT 创建的插件具有以下标准结构：

```
my_plugin/
├── __init__.py              # 插件元数据（包含 __plugin_meta__）
├── plugin.py                # 插件主类
├── config/
│   └── config.toml          # 配置文件
├── components/              # 组件目录（可选）
│   ├── actions/             # Action 组件
│   ├── tools/               # Tool 组件
│   ├── events/              # Event Handler 组件
│   ├── adapters/            # Adapter 组件
│   ├── prompts/             # Prompt 组件
│   ├── plus_commands/       # PlusCommand 组件
│   ├── routers/             # Router 组件
│   └── chatters/            # Chatter 组件
├── utils/                   # 工具函数（可选）
├── tests/                   # 测试目录（推荐）
│   ├── conftest.py
│   └── test_plugin.py
├── docs/                    # 文档目录（推荐）
│   └── README.md
├── pyproject.toml           # Python 项目配置（推荐）
├── requirements.txt         # 依赖列表（推荐）
└── README.md               # 插件说明（推荐）
```

### 必需文件
- `__init__.py` - 必须包含 `__plugin_meta__` 变量
- `plugin.py` - 插件主类，继承自 `BasePlugin`
- `config/config.toml` - 配置文件

### 推荐文件
- `README.md` - 插件使用说明
- `pyproject.toml` 或 `requirements.txt` - 依赖管理
- `tests/` - 测试目录
- `docs/` - 文档目录

## 🔧 配置

MPDT 支持项目级配置文件 `.mpdtrc.toml`（计划中）：

```toml
[mpdt]
project_name = "my_plugin"
version = "1.0.0"

[mpdt.check]
level = "warning"
auto_fix = false

[mpdt.test]
coverage_threshold = 80

[mpdt.templates]
author = "Your Name"
license = "GPL-v3.0"
```

## 🎯 开发状态

### ✅ 已实现功能

- ✅ **插件初始化** (`mpdt init`)
  - 支持 6 种模板类型
  - 交互式问答
  - Git 集成
  - 多种许可证支持
  
- ✅ **组件生成** (`mpdt generate`)
  - 支持 8 种组件类型
  - 自动异步方法生成
  - 自动更新插件注册
  - 交互式模式

- ✅ **静态检查** (`mpdt check`)
  - 结构验证器
  - 元数据验证器
  - 组件验证器
  - 配置验证器
  - 类型检查器 (mypy)
  - 代码风格检查器 (ruff)
  - 自动修复功能
  - Markdown 报告生成

### 🚧 计划中功能

- 🚧 **测试框架** (`mpdt test`)
- 🚧 **开发模式** (`mpdt dev`)
- 🚧 **构建打包** (`mpdt build`)

## 🤝 贡献

欢迎贡献代码和建议！

## 📄 许可证

GPL-3.0-or-later

## 🔗 相关链接

- [MoFox-Bot](https://github.com/MoFox-Studio/MoFox-Bot)
- [问题反馈](https://github.com/MoFox-Studio/mofox-plugin-toolkit/issues)

## 📊 技术栈

- **CLI 框架**: Click
- **交互式界面**: Questionary
- **美化输出**: Rich
- **模板引擎**: Jinja2
- **配置管理**: TOML, Pydantic
- **代码检查**: Mypy (类型检查), Ruff (代码风格)
- **文件监控**: Watchdog (计划中)

## 🛠️ 核心依赖

```toml
dependencies = [
    "click>=8.1.7",
    "rich>=13.7.0",
    "questionary>=2.0.1",
    "jinja2>=3.1.2",
    "toml>=0.10.2",
    "pydantic>=2.5.0",
    "watchdog>=3.0.0",
    "ruff>=0.1.6",
    "mypy>=1.7.0"
]
```

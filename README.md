# MoFox Plugin Dev Toolkit (MPDT)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.4.5-orange.svg)](https://github.com/MoFox-Studio/mofox-plugin-toolkit)
[![PyPI](https://img.shields.io/badge/PyPI-mofox--plugin--dev--toolkit-blue.svg)](https://pypi.org/project/mofox-plugin-dev-toolkit/)

一个类似于 Vite 的 Python 开发工具，专门为 Neo-MoFox 插件系统设计，提供快速创建、开发、构建、检查和热重载的完整工具链。

## ⚡ 快速开始

```bash
# 1. 安装 MPDT
pip install mofox-plugin-dev-toolkit

# 2. 创建插件
mpdt init my_awesome_plugin

# 3. 进入插件目录
cd my_awesome_plugin

# 4. 生成组件
mpdt generate action HelloWorld

# 5. 检查代码
mpdt check

# 6. 构建插件
mpdt build

# 7. 开发模式（需先配置 Neo-MoFox 路径）
mpdt dev
```

## ✨ 特性

### 核心功能

- 🚀 **快速初始化** - 一键创建标准化的插件项目结构，支持 6 种模板（basic、action、tool、plus_command、full、adapter）
- 🎨 **代码生成** - 快速生成 11 种组件类型（Action、Tool、Event、Adapter、Prompt、PlusCommand、Router、Chatter、Service、Config、Collection），始终生成异步方法
- 🔍 **完整的静态检查系统** - 集成 8 层验证体系：
  - ✅ **结构检查** - 验证插件目录结构、必需文件和推荐文件
  - ✅ **元数据检查** - 检查 `manifest.json` 配置的完整性和正确性
  - ✅ **组件检查** - 验证组件注册、命名规范和导入路径
  - ✅ **配置检查** - 检查配置文件的语法和必需配置
  - ✅ **类型检查** - 使用 mypy 进行严格的类型检查
  - ✅ **代码风格检查** - 使用 ruff 检查代码规范并自动修复
  - ✅ **自动修复** - 智能修复可自动处理的问题  
- 📦 **插件构建打包** - 将插件打包为标准 `.mfp` 格式（本质为 ZIP），支持版本号自动升级
- 🔥 **热重载开发模式** - 基于 DevBridge 插件的实时热重载系统：
  - 🔄 文件变化自动检测和重载
  - 📦 自动注入开发桥接插件
  - 🚦 自动管理插件生命周期
  - 📊 实时显示重载状态和日志
- 🎯 **Git 集成** - 支持自动初始化 Git 仓库和提取用户信息
- 🎨 **美观的交互界面** - 基于 Rich 和 Questionary 的现代化命令行体验
- 📜 **多种许可证** - 支持 GPL-v3.0、MIT、Apache-2.0、BSD-3-Clause
- 🛠️ **完整的配置管理** - 支持交互式配置向导、配置显示、配置验证和路径设置

## 📦 安装

### 使用 pip 安装（推荐）

```bash
# 从 PyPI 安装最新版本
pip install mofox-plugin-dev-toolkit

# 指定版本安装
pip install mofox-plugin-dev-toolkit==0.4.5

# 安装开发依赖
pip install "mofox-plugin-dev-toolkit[dev]"
```

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/MoFox-Studio/mofox-plugin-toolkit.git
cd mofox-plugin-toolkit

# 安装到本地
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"
```

### 验证安装

```bash
# 查看版本
mpdt --version

# 显示帮助
mpdt --help
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
mpdt generate service DataService --description "数据服务"
mpdt generate config PluginConfig --description "插件配置类"
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
- `service` - Service 组件（服务类）
- `config` - Config 组件（配置类）

**注意**：所有生成的组件方法都是异步的（async），符合 Neo-MoFox 的异步架构。

### 3. 开发模式（热重载）

```bash
# 启动开发模式（需要先配置 Neo-MoFox 主程序路径）
mpdt dev

# 指定主程序路径
mpdt dev --neo-mofox-path /path/to/neo-mofox

# 指定插件路径
mpdt dev --plugin-path /path/to/plugin

# 首次运行会提示配置
# 之后会自动：
# 1. 注入目标插件到主程序 plugins 目录
# 2. 注入 DevBridge 插件（包含文件监控和热重载逻辑）
# 3. 启动主程序
# 4. DevBridge 插件自动监控文件变化并热重载

# 开发模式功能：
# - 🔄 文件保存后自动重载插件
# - 📊 实时显示重载状态和耗时
# - 🚦 自动管理插件生命周期
# - 📝 实时查看主程序日志
# - ⚡ 无需手动重启主程序
# - 🧹 主程序退出时自动清理 DevBridge 插件
```

### 4. 检查插件

```bash
# 运行所有检查（包含 8 个检查器）
mpdt check

# 自动修复可修复的问题
mpdt check --fix

# 只显示错误级别的问题
mpdt check --level error

# 生成 Markdown 或 JSON 格式的检查报告
mpdt check --report markdown --output check_report.md
mpdt check --report json --output check_report.json

# 跳过特定检查
mpdt check --no-type        # 跳过类型检查
mpdt check --no-style       # 跳过代码风格检查
mpdt check --no-component   # 跳过组件检查
mpdt check --no-structure   # 跳过结构检查
mpdt check --no-metadata    # 跳过元数据检查

# 组合使用
mpdt check --fix --level warning --report markdown -o report.md
```

**检查项说明**：
- **结构检查** (structure) - 验证目录结构、必需文件（`__init__.py`、`plugin.py`、`manifest.json`）和推荐文件（`README.md`、`pyproject.toml`、`tests/`）
- **元数据检查** (metadata) - 检查 `manifest.json` 的存在性、格式和必需字段
- **组件检查** (component) - 验证组件注册、命名规范、导入路径和类型正确性
- **配置检查** (config) - 检查配置文件的语法、必需配置项和数据类型
- **类型检查** (type) - 使用 mypy 进行严格的类型检查，确保类型安全
- **代码风格检查** (style) - 使用 ruff 检查代码规范，支持自动修复格式问题
- **自动修复** (autofix) - 智能分析并自动修复可处理的问题

### 5. 构建插件

```bash
# 构建插件为 .mfp 文件（推荐格式）
mpdt build

# 指定输出目录
mpdt build --output dist

# 包含文档
mpdt build --with-docs

# 构建为 .zip 格式
mpdt build --format zip

# 自动升级版本号
mpdt build --bump patch   # 升级补丁版本 (0.0.1 -> 0.0.2)
mpdt build --bump minor   # 升级次版本 (0.1.0 -> 0.2.0)
mpdt build --bump major   # 升级主版本 (1.0.0 -> 2.0.0)

# 组合使用
mpdt build --with-docs --bump patch --output release
```

**说明**：`.mfp` 文件是 Neo-MoFox 的标准插件格式（本质为 ZIP 压缩包），可直接被 loader.py 加载。

### 6. 配置管理

```bash
# 交互式配置向导
mpdt config init

# 显示当前配置
mpdt config show

# 测试配置是否有效
mpdt config test

# 设置 Neo-MoFox 主程序路径
mpdt config set-mofox /path/to/neo-mofox
```

**配置项说明**：
  - **Neo-MoFox 路径** - Neo-MoFox 主程序的安装路径
  - **自动重载** - 是否启用自动重载功能（默认启用）
  - **重载延迟** - 文件变化后的重载延迟时间（默认 1 秒）
  - **Python 环境** - 自动检测和配置虚拟环境

## 📖 命令参考

### `mpdt` - 主命令

```bash
mpdt [OPTIONS] COMMAND [ARGS]...

选项:
  -v, --verbose    详细输出模式
  --no-color       禁用彩色输出
  --version        显示版本信息
  --help           显示帮助信息
```

### `mpdt init` - 初始化插件

创建新的插件项目，支持多种模板和自动化配置。

```bash
mpdt init [PLUGIN_NAME] [OPTIONS]

选项:
  -t, --template TEXT       模板类型: basic, action, tool, plus_command, full, adapter
  -a, --author TEXT         作者名称（可从 Git 配置自动获取）
  -l, --license TEXT        开源协议: GPL-v3.0, MIT, Apache-2.0, BSD-3-Clause
  --with-docs              创建文档目录和基础文档文件
  --init-git/--no-init-git 是否初始化 Git 仓库（默认初始化）
  -o, --output PATH        输出目录（默认为当前目录）

示例:
  mpdt init my_plugin                           # 交互式创建
  mpdt init my_plugin -t action -a "张三"       # 指定参数创建
  mpdt init my_plugin -t full --with-docs       # 创建完整模板
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
  service         Service 组件 - 服务类
  config          Config 组件 - 配置类

选项:
  -d, --description TEXT    组件描述信息
  -o, --output PATH        输出目录（默认自动选择对应组件目录）
  -f, --force              覆盖已存在的文件

示例:
  mpdt generate                                  # 交互式生成
  mpdt generate action SendMsg -d "发送消息"    # 命令行生成
  mpdt generate tool Formatter --force           # 强制覆盖
  mpdt generate service DataService              # 生成服务类
```

**注意**：不提供参数时将进入交互式问答模式，更易于使用。

### `mpdt check` - 检查插件

对插件进行全面的静态检查，包括 8 个检查器。

```bash
mpdt check [PATH] [OPTIONS]

选项:
  -l, --level TEXT         显示问题级别: error, warning, info（默认 warning）
  --fix                    自动修复可修复的问题（主要是代码风格）
  --report TEXT            报告格式: console（默认）, markdown, json
  -o, --output PATH        报告输出路径（仅用于 markdown 和 json 格式）
  --no-structure           跳过结构检查
  --no-metadata            跳过元数据检查
  --no-component           跳过组件检查
  --no-type                跳过类型检查
  --no-style               跳过代码风格检查

检查器说明:
  structure   - 检查目录结构、必需文件和推荐文件
  metadata    - 检查 manifest.json 的完整性
  component   - 检查组件注册和命名规范
  config      - 检查配置文件
  type        - 使用 mypy 进行类型检查
  style       - 使用 ruff 进行代码风格检查
  autofix     - 自动修复可处理的问题

示例:
  mpdt check                                    # 运行所有检查
  mpdt check --fix                             # 自动修复问题
  mpdt check --level error                     # 只显示错误
  mpdt check --report markdown -o report.md    # 生成 Markdown 报告
  mpdt check --report json -o report.json      # 生成 JSON 报告
  mpdt check --no-type --no-style              # 跳过耗时检查
```

### `mpdt build` - 构建插件

将插件打包为标准 `.mfp` 格式（本质为 ZIP 压缩包）。

```bash
mpdt build [PLUGIN_PATH] [OPTIONS]

选项:
  -o, --output PATH        输出目录（默认为 dist）
  --with-docs              包含文档文件
  --format TEXT            构建格式: mfp（推荐）, zip
  --bump TEXT              自动升级版本号: major, minor, patch

参数:
  PLUGIN_PATH              插件根目录（包含 manifest.json），默认当前目录

示例:
  mpdt build                                    # 构建到 dist 目录
  mpdt build --with-docs                        # 包含文档
  mpdt build --bump patch                       # 自动升级补丁版本
  mpdt build --format zip -o release            # 使用 zip 格式
```

**说明**：生成的 `.mfp` 文件可直接被 Neo-MoFox 的 loader.py 加载。

### `mpdt dev` - 开发模式

启动带热重载的开发模式，实时监控文件变化并自动重载插件。

```bash
mpdt dev [OPTIONS]

选项:
  --neo-mofox-path PATH    Neo-MoFox 主程序路径
  --plugin-path PATH       插件路径（默认当前目录）

功能特性:
  - 🔄 自动检测文件变化并热重载
  - 📦 自动注入 DevBridge 开发桥接插件
  - 🚦 自动管理插件生命周期
  - 📊 实时显示重载状态和耗时
  - 📝 显示主程序运行日志
  - 🧹 主程序退出时自动清理

首次运行:
  首次运行会提示配置 Neo-MoFox 主程序路径
  配置将保存到 ~/.mpdt/config.toml

工作流程:
  1. 自动将目标插件复制到主程序 plugins 目录
  2. 注入 DevBridge 插件（包含文件监控逻辑）
  3. 启动主程序
  4. DevBridge 插件监控文件变化
  5. 检测到变化时自动卸载旧版本并加载新版本

示例:
  mpdt dev                                      # 在插件目录中运行
  mpdt dev --neo-mofox-path /path/to/neo-mofox  # 指定主程序路径
```

### `mpdt config` - 配置管理

管理 MPDT 的配置信息。

```bash
# 子命令
mpdt config init         # 交互式配置向导
mpdt config show         # 显示当前配置
mpdt config test         # 测试配置是否有效
mpdt config set-mofox    # 设置 Neo-MoFox 主程序路径

示例:
  # 交互式配置
  mpdt config init

  # 设置 Neo-MoFox 路径
  mpdt config set-mofox /path/to/neo-mofox

  # 显示配置
  mpdt config show

  # 验证配置
  mpdt config test
```

**配置项说明**：
  - **Neo-MoFox 路径** - Neo-MoFox 主程序的安装路径
  - **自动重载** - 是否启用自动重载功能
  - **重载延迟** - 文件变化后的重载延迟时间（秒）
  - **Python 环境** - 自动检测虚拟环境和 Python 版本

---

## 🏗️ 插件结构

MPDT 创建的插件遵循 Neo-MoFox 标准结构：

```
my_plugin/                   # 插件根目录
├── __init__.py              # 包初始化文件
├── plugin.py                # ⭐ 插件主类（必需）
│                            #    继承自 BasePlugin
├── manifest.json            # ⭐ 插件元数据文件（必需）
│                            #    包含插件名称、版本、作者等信息
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
│   ├── chatters/            # Chatter 目录
│   ├── services/            # Service 目录
│   └── configs/             # Config 目录
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

### ✅ 已完成功能（v0.4.5）

#### 1. ✅ 插件初始化 (`mpdt init`)
- 支持 6 种模板类型（basic、action、tool、plus_command、full、adapter）
- 交互式问答模式
- Git 自动初始化和用户信息提取
- 多种开源协议支持（GPL-v3.0、MIT、Apache-2.0、BSD-3-Clause）
- 自动生成标准化项目结构
- 自动生成 manifest.json 元数据文件

#### 2. ✅ 组件生成 (`mpdt generate`)
- 支持 11 种组件类型（action、tool、event、adapter、prompt、plus-command、router、chatter、service、config、collection）
- 所有方法自动生成为异步
- 基于 libcst 的智能代码解析和注入
- 自动更新插件主类注册代码
- 交互式和命令行两种模式
- 组件文件自动放置到正确目录

#### 3. ✅ 静态检查系统 (`mpdt check`)
- **结构验证器** - 目录和文件完整性检查
- **元数据验证器** - `manifest.json` 验证
- **组件验证器** - 组件注册和规范检查
- **配置验证器** - 配置文件验证
- **类型检查器** - mypy 集成，严格类型检查
- **代码风格检查器** - ruff 集成，自动修复
- **自动修复验证器** - 智能问题修复
- 支持生成 Markdown 和 JSON 格式报告
- 灵活的级别过滤（error/warning/info）

#### 4. ✅ 插件构建打包 (`mpdt build`)
- 将插件打包为标准 `.mfp` 格式（本质为 ZIP）
- 支持版本号自动升级（major/minor/patch）
- 智能文件过滤（排除缓存、版本控制等）
- 支持 `.mfp` 或 `.zip` 格式输出
- 可选包含文档文件
- 自动验证 manifest.json

#### 5. ✅ 热重载开发模式 (`mpdt dev`)
- 基于 DevBridge 插件的热重载机制
- 自动注入目标插件和开发桥接插件
- 文件变化自动检测（使用 watchdog）
- 插件生命周期自动管理
- 实时状态显示和日志查看
- 主程序退出时自动清理

#### 6. ✅ 配置管理 (`mpdt config`)
- 交互式配置向导 (`mpdt config init`)
- 配置显示 (`mpdt config show`)
- 配置验证 (`mpdt config test`)
- Neo-MoFox 路径设置 (`mpdt config set-mofox`)
- 自动检测和配置虚拟环境
- 支持自定义重载延迟和自动重载开关

### 📦 PyPI 发布
- ✅ 已发布到 PyPI（包名：mofox-plugin-dev-toolkit）
- ✅ 支持 pip 直接安装
- ✅ 完整的依赖管理
- ✅ 支持可选依赖（dev、check、docs）

### 🚧 计划中功能

#### 测试框架增强
- 自动运行插件测试
- 覆盖率报告生成
- 并行测试执行
- 测试报告输出

#### 插件市场集成
- 插件上传和发布
- 版本管理
- 依赖解析

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

### 提交规范
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建/工具链相关

---

## 📄 许可证

本项目采用 GPL-3.0-or-later 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🔗 相关链接

- [Neo-MoFox 主仓库](https://github.com/MoFox-Studio/Neo-MoFox)
- [PyPI 项目页](https://pypi.org/project/mofox-plugin-dev-toolkit/)
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
- **代码解析**: [libcst](https://libcst.readthedocs.io/) - Python 具体语法树解析和修改
- **代码检查**: 
  - [Mypy](https://mypy.readthedocs.io/) - 静态类型检查
  - [Ruff](https://docs.astral.sh/ruff/) - 快速的 Python 代码检查器和格式化工具

### 开发模式
- **文件监控**: [Watchdog](https://python-watchdog.readthedocs.io/) - 跨平台文件系统监控
- **WebSocket**: [websockets](https://websockets.readthedocs.io/) - 异步 WebSocket 库
- **HTTP 客户端**: [aiohttp](https://docs.aiohttp.org/) - 异步 HTTP 客户端/服务器

## 🏗️ 项目结构

```
mofox-plugin-toolkit/
├── mpdt/                          # 主包
│   ├── __init__.py                # 版本信息
│   ├── __main__.py                # 入口点
│   ├── cli.py                     # CLI 主入口
│   ├── commands/                  # 命令实现
│   │   ├── init.py                # 插件初始化
│   │   ├── generate.py            # 组件生成
│   │   ├── check.py               # 静态检查
│   │   ├── build.py               # 插件构建
│   │   └── dev.py                 # 开发模式
│   ├── validators/                # 验证器
│   │   ├── base.py                # 基础验证器
│   │   ├── structure_validator.py # 结构验证
│   │   ├── metadata_validator.py  # 元数据验证
│   │   ├── component_validator.py # 组件验证
│   │   ├── config_validator.py    # 配置验证
│   │   ├── type_validator.py      # 类型检查
│   │   ├── style_validator.py     # 代码风格
│   │   └── auto_fix_validator.py  # 自动修复
│   ├── templates/                 # 组件模板
│   │   ├── action_template.py
│   │   ├── tool_template.py
│   │   ├── event_template.py
│   │   ├── adapter_template.py
│   │   ├── prompt_template.py
│   │   ├── plus_command_template.py
│   │   ├── router_template.py
│   │   ├── chatter_template.py
│   │   ├── service_template.py
│   │   ├── config_template.py
│   │   └── collection_template.py
│   ├── utils/                     # 工具函数
│   │   ├── code_parser.py         # 代码解析
│   │   ├── color_printer.py       # 彩色输出
│   │   ├── config_loader.py       # 配置加载
│   │   ├── config_manager.py      # 配置管理
│   │   ├── file_ops.py            # 文件操作
│   │   ├── license_generator.py   # 许可证生成
│   │   ├── plugin_parser.py       # 插件解析
│   │   └── template_engine.py     # 模板引擎
│   └── dev/                       # 开发模式相关
├── docs/                          # 文档
├── examples/                      # 示例
├── plugin_dev_toolkit_design/     # 设计文档
├── pyproject.toml                 # 项目配置
├── MANIFEST.in                    # 打包清单
├── README.md                      # 说明文档
└── LICENSE                        # 许可证
```

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
    "libcst>=1.8.6",        # Python CST 解析（代码智能注入）
    "aiohttp>=3.9.0",       # 异步 HTTP
    "uvicorn>=0.24.0",      # ASGI 服务器
    "fastapi>=0.104.0",     # Web 框架
    "ruff>=0.1.6",          # 代码检查
    "mypy>=1.7.0"           # 类型检查
]
```

---

## 💡 常见问题

### Q: 如何安装 MPDT？
A: 推荐使用 pip 安装：`pip install mofox-plugin-dev-toolkit`。也可以从源码安装：`git clone` 后执行 `pip install -e .`。

### Q: 如何配置开发模式？
A: 首次运行 `mpdt dev` 时会提示输入 Neo-MoFox 主程序路径，配置会保存到 `~/.mpdt/config.toml`。也可以使用 `mpdt config init` 进行交互式配置。

### Q: 检查器报错怎么办？
A: 首先尝试使用 `mpdt check --fix` 自动修复。如果仍有问题，查看具体错误信息和建议。

### Q: 如何跳过某些检查？
A: 使用 `--no-<checker>` 选项，例如 `mpdt check --no-type --no-style`。

### Q: 生成的组件在哪里？
A: 组件会自动放置到对应的目录，例如 Action 放在 `components/actions/`。

### Q: 如何更新工具？
A: 如果是 pip 安装，执行 `pip install --upgrade mofox-plugin-dev-toolkit`。如果是从源码安装，执行 `git pull && pip install -e .`。

### Q: .mfp 文件是什么？
A: `.mfp` 是 Neo-MoFox 的标准插件格式，本质为 ZIP 压缩包，可直接被 loader.py 加载，无需解压。

### Q: 开发模式如何工作？
A: MPDT 会将 DevBridge 插件注入到主程序，该插件负责监控文件变化并自动热重载目标插件。主程序退出时会自动清理 DevBridge。

### Q: 支持哪些组件类型？
A: 支持 11 种组件：action、tool、event、adapter、prompt、plus-command、router、chatter、service、config、collection。

### Q: manifest.json 和 __plugin_meta__ 的区别？
A: Neo-MoFox 使用 `manifest.json` 作为插件元数据文件，而不是旧版的 `__plugin_meta__` 变量。MPDT 生成的插件使用 manifest.json。

---

## 📝 更新日志

### v0.4.5 (2026-02-23)
- ✅ 发布到 PyPI，支持 pip 安装
- ✅ 添加 `mpdt build` 命令，支持打包为 .mfp 格式
- ✅ 支持版本号自动升级（--bump major/minor/patch）
- ✅ 完善配置管理功能
- ✅ 更新插件结构为 manifest.json 标准
- ✅ 新增 service 和 config 组件类型
- ✅ 优化代码结构和文档

### v0.4.x
- ✅ 实现插件构建和打包功能
- ✅ 添加 .mfp 格式支持
- ✅ 完善 CLI 参数和帮助信息
- ✅ 优化检查器性能

### v0.3.x
- ✅ 添加 libcst 代码解析支持
- ✅ 实现自动修复验证器 (AutoFixValidator)
- ✅ 支持 JSON 格式报告输出
- ✅ 改进组件代码注入机制

### v0.2.1 (2025-12-14)
- ✅ 实现完整的热重载开发模式 (`mpdt dev`)
- ✅ 添加 DevBridge 插件注入机制
- ✅ 实现开发桥接插件自动注入
- ✅ 改进文件监控和自动重载
- ✅ 优化用户交互体验

### v0.2.0
- ✅ 完成 8 个检查器实现
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

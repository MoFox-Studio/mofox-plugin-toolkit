# MoFox Plugin Dev Toolkit (MPDT)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](https://github.com/MoFox-Studio/mofox-plugin-toolkit)

一个类似于 Vite 的 Python 开发工具，专门为 MoFox-Bot 插件系统设计，提供快速创建、开发、测试和维护插件的完整工具链。

## ✨ 特性

- 🚀 **快速初始化** - 一键创建标准化的插件项目结构
- 🎨 **代码生成** - 快速生成 Action、Command、Tool 等组件
- 🔍 **静态检查** - 集成类型检查、代码风格和安全检查
- 🧪 **测试框架** - 完整的测试工具和 Mock 对象库
- 📦 **依赖管理** - 自动管理插件依赖关系
- 🛠️ **开发模式** - 文件监控和热重载
- 📚 **文档生成** - 自动生成插件文档

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

# 或直接指定插件名
mpdt init my_awesome_plugin --template action
```

### 2. 生成组件

```bash
cd my_awesome_plugin

# 生成 Action 组件
mpdt generate action SendMessage --description "发送消息"

# 生成 Tool 组件
mpdt generate tool MessageFormatter --async

# 生成 Command 组件
mpdt generate command Help --pattern "^/help"
```

### 3. 开发模式

```bash
# 启动开发模式（实时监控文件变化）
mpdt dev
```

### 4. 检查插件

```bash
# 运行所有检查
mpdt check

# 自动修复问题
mpdt check --fix
```

### 5. 运行测试

```bash
# 运行测试
mpdt test

# 带覆盖率报告
mpdt test --coverage
```

### 6. 构建插件

```bash
# 构建插件
mpdt build --with-docs
```

## 📖 命令参考

### `mpdt init` - 初始化插件

创建新的插件项目。

```bash
mpdt init [PLUGIN_NAME] [OPTIONS]

选项:
  -t, --template TEXT    模板类型: basic, action, tool, command, full
  -a, --author TEXT      作者名称
  -l, --license TEXT     开源协议
  --with-examples        包含示例代码
  --with-tests          创建测试文件
  --with-docs           创建文档文件
  -o, --output PATH     输出目录
```

### `mpdt generate` - 生成组件

生成插件组件代码。

```bash
mpdt generate <COMPONENT_TYPE> <COMPONENT_NAME> [OPTIONS]

组件类型:
  action          Action 组件
  command         Command 组件
  tool            Tool 组件
  event           Event Handler 组件
  adapter         Adapter 组件
  prompt          Prompt 组件
  plus-command    PlusCommand 组件

选项:
  -d, --description TEXT  组件描述
  --async                生成异步方法
  --with-test            同时生成测试文件
  -f, --force            覆盖已存在的文件
```

### `mpdt check` - 检查插件

对插件进行静态检查。

```bash
mpdt check [PATH] [OPTIONS]

选项:
  -l, --level TEXT       显示级别: error, warning, info
  --fix                  自动修复问题
  --report TEXT          报告格式: console, json, html
  -o, --output PATH      报告输出路径
  --no-structure         跳过结构检查
  --no-type             跳过类型检查
  --no-style            跳过代码风格检查
```

### `mpdt test` - 运行测试

运行插件测试。

```bash
mpdt test [TEST_PATH] [OPTIONS]

选项:
  -c, --coverage         生成覆盖率报告
  --min-coverage INT     最低覆盖率要求
  -v, --verbose          详细输出
  -m, --markers TEXT     只运行特定标记的测试
  -n, --parallel INT     并行运行测试
```

### `mpdt dev` - 开发模式

启动开发模式，监控文件变化。

```bash
mpdt dev [OPTIONS]

选项:
  -p, --port INT         开发服务器端口
  --host TEXT           绑定的主机地址
  --no-reload           禁用自动重载
  --debug               启用调试模式
```

### `mpdt build` - 构建插件

构建和打包插件。

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
├── __init__.py              # 插件元数据
├── plugin.py                # 插件主类
├── config/
│   └── config.toml          # 配置文件
├── components/              # 组件目录
│   ├── actions/             # Action 组件
│   ├── commands/            # Command 组件
│   ├── tools/               # Tool 组件
│   └── events/              # Event Handler 组件
├── utils/                   # 工具函数
├── tests/                   # 测试目录
│   ├── conftest.py
│   └── test_plugin.py
├── docs/                    # 文档目录
│   └── README.md
├── pyproject.toml           # Python 项目配置
└── requirements.txt         # 依赖列表
```

## 🔧 配置

MPDT 支持项目级配置文件 `.mpdtrc.toml`：

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

## 🤝 贡献

欢迎贡献代码和建议！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 许可证

GPL-3.0-or-later

## 🔗 相关链接

- [MoFox-Bot](https://github.com/MoFox-Studio/MoFox-Bot)
- [插件开发文档](https://docs.mofox.studio/plugin-development)
- [问题反馈](https://github.com/MoFox-Studio/mofox-plugin-toolkit/issues)

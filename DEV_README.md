# MoFox Plugin Dev Toolkit

## 安装

```bash
cd mofox-plugin-toolkit
pip install -e .
```

## 测试安装

```bash
# 查看帮助
mpdt --help

# 查看版本
mpdt --version

# 初始化新插件（交互式）
mpdt init

# 或直接指定参数
mpdt init test_plugin --template basic --author "Your Name"
```

## 当前状态

✅ **已完成:**
- CLI 基础框架
- 文件操作工具
- 彩色输出工具
- 模板引擎
- 配置加载器
- `mpdt init` 命令（完整实现）

⏳ **待实现:**
- `mpdt generate` 命令
- `mpdt check` 命令
- `mpdt test` 命令
- `mpdt build` 命令
- `mpdt dev` 命令

## 项目结构

```
mofox-plugin-toolkit/
├── mpdt/                      # 核心包
│   ├── __init__.py
│   ├── cli.py                 # CLI 入口 ✅
│   ├── commands/              # 命令模块
│   │   ├── init.py            # 初始化命令 ✅
│   │   ├── generate.py        # 生成命令 ⏳
│   │   └── check.py           # 检查命令 ⏳
│   └── utils/                 # 工具模块
│       ├── file_ops.py        # 文件操作 ✅
│       ├── color_printer.py   # 彩色输出 ✅
│       ├── template_engine.py # 模板引擎 ✅
│       └── config_loader.py   # 配置加载 ✅
├── pyproject.toml             # 项目配置 ✅
└── README.md                  # 说明文档 ✅
```

## 下一步开发

1. 实现 `mpdt generate` 命令的组件模板
2. 实现基本的静态检查功能
3. 添加测试用例
4. 完善文档

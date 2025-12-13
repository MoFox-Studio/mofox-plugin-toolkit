# 技术规范文档

## 1. CLI 命令详细规范

### 1.1 mpdt init

#### 完整命令格式
```bash
mpdt init [PLUGIN_NAME] [OPTIONS]
```

#### 参数说明

**位置参数:**
- `PLUGIN_NAME`: 插件名称（可选，不提供则进入交互模式）

**选项参数:**
- `--template, -t`: 使用的模板类型
  - 可选值: `basic`, `action`, `tool`, `command`, `full`, `adapter`
  - 默认: `basic`
  
- `--author, -a`: 作者名称
  - 默认: 从 git config 读取
  
- `--license, -l`: 开源协议
  - 可选值: `GPL-v3.0`, `MIT`, `Apache-2.0`, `BSD-3-Clause`
  - 默认: `GPL-v3.0`
  
- `--python-version`: Python 版本要求
  - 默认: `^3.11`
  
- `--with-examples`: 包含示例代码
  - 类型: bool flag
  
- `--with-tests`: 创建测试文件
  - 类型: bool flag
  
- `--with-docs`: 创建文档文件
  - 类型: bool flag
  
- `--output, -o`: 输出目录
  - 默认: 当前目录

#### 交互式问答流程

```python
questions = [
    {
        "type": "input",
        "name": "plugin_name",
        "message": "插件名称 (使用下划线命名):",
        "validate": lambda x: bool(re.match(r"^[a-z][a-z0-9_]*$", x)),
    },
    {
        "type": "input", 
        "name": "display_name",
        "message": "显示名称 (用户可见):",
    },
    {
        "type": "input",
        "name": "description",
        "message": "插件描述:",
    },
    {
        "type": "list",
        "name": "template",
        "message": "选择插件模板:",
        "choices": [
            {"name": "基础插件", "value": "basic"},
            {"name": "Action 插件", "value": "action"},
            {"name": "Tool 插件", "value": "tool"},
            {"name": "Command 插件", "value": "command"},
            {"name": "完整插件", "value": "full"},
            {"name": "Adapter 插件", "value": "adapter"},
        ],
    },
    {
        "type": "input",
        "name": "author",
        "message": "作者名称:",
        "default": get_git_user_name(),
    },
    {
        "type": "list",
        "name": "license",
        "message": "选择开源协议:",
        "choices": ["GPL-v3.0", "MIT", "Apache-2.0", "BSD-3-Clause"],
        "default": "GPL-v3.0",
    },
    {
        "type": "confirm",
        "name": "with_examples",
        "message": "包含示例代码?",
        "default": True,
    },
    {
        "type": "confirm",
        "name": "with_tests",
        "message": "创建测试文件?",
        "default": True,
    },
    {
        "type": "confirm",
        "name": "with_docs",
        "message": "创建文档文件?",
        "default": True,
    },
]
```

#### 输出结果

成功创建插件后，输出以下信息：

```
✅ 插件创建成功！

📁 项目结构:
my_plugin/
├── __init__.py
├── plugin.py
├── config/
│   └── config.toml
├── components/
├── tests/
└── docs/

📝 下一步:
1. cd my_plugin
2. mpdt generate action MyAction  # 创建 Action 组件
3. mpdt dev                        # 启动开发模式
4. mpdt check                      # 运行检查

📚 文档: https://docs.mofox.studio/mpdt/getting-started
```

### 1.2 mpdt generate

#### 完整命令格式
```bash
mpdt generate <COMPONENT_TYPE> <COMPONENT_NAME> [OPTIONS]
```

#### 参数说明

**位置参数:**
- `COMPONENT_TYPE`: 组件类型
  - 必选，可选值: `action`, `command`, `tool`, `event`, `adapter`, `prompt`, `plus-command`
  
- `COMPONENT_NAME`: 组件名称
  - 必选，使用 PascalCase 命名

**选项参数:**
- `--description, -d`: 组件描述
  
- `--async`: 生成异步方法
  - 类型: bool flag
  
- `--with-test`: 同时生成测试文件
  - 类型: bool flag
  
- `--output, -o`: 输出目录
  - 默认: `components/<component_type>s/`
  
- `--template`: 自定义模板路径
  
- `--force, -f`: 覆盖已存在的文件
  - 类型: bool flag

#### 组件类型详细说明

**Action 组件特有选项:**
```bash
--activation-type: Action 激活类型
  可选值: always, random, conditional, llm_judge
  默认: always

--chat-type: 允许的聊天类型
  可选值: private, group, all
  默认: all

--two-step: 是否为二步 Action
  类型: bool flag
```

**Command 组件特有选项:**
```bash
--pattern, -p: 命令匹配模式（正则表达式）
  默认: ^/<command_name>

--priority: 命令优先级
  类型: int
  默认: 0

--intercept: 是否拦截消息
  类型: bool flag
```

**Tool 组件特有选项:**
```bash
--params: 工具参数定义（JSON 格式）
  示例: '{"query": {"type": "string", "required": true}}'

--llm-available: 是否对 LLM 可用
  类型: bool flag
  默认: true
```

#### 批量生成

支持一次生成多个同类型组件：

```bash
mpdt generate action MessageAction ReplyAction ForwardAction
```

### 1.3 mpdt check

#### 完整命令格式
```bash
mpdt check [PATH] [OPTIONS]
```

#### 参数说明

**位置参数:**
- `PATH`: 要检查的插件路径
  - 可选，默认为当前目录

**选项参数:**
- `--level, -l`: 显示的最低级别
  - 可选值: `error`, `warning`, `info`
  - 默认: `warning`
  
- `--fix`: 自动修复可修复的问题
  - 类型: bool flag
  
- `--report`: 报告格式
  - 可选值: `console`, `json`, `html`, `markdown`
  - 默认: `console`
  
- `--output, -o`: 报告输出路径
  - 当 report 不为 console 时必需
  
- `--exclude`: 排除的文件模式
  - 示例: `--exclude "tests/*" --exclude "*.pyc"`
  
- `--include`: 只检查匹配的文件模式
  
- `--no-structure`: 跳过结构检查
- `--no-metadata`: 跳过元数据检查
- `--no-component`: 跳过组件检查
- `--no-type`: 跳过类型检查
- `--no-style`: 跳过代码风格检查
- `--no-security`: 跳过安全检查

#### 检查项详细说明

**1. 结构检查 (structure)**

检查内容:
- 必需文件存在性: `__init__.py`, `plugin.py`
- 必需目录存在性: `config/`
- 推荐目录存在性: `components/`, `tests/`, `docs/`
- 文件命名规范: 使用 snake_case
- 目录组织规范

错误级别:
- ERROR: 缺少必需文件/目录
- WARNING: 缺少推荐目录
- INFO: 命名不规范

**2. 元数据检查 (metadata)**

检查内容:
- `__plugin_meta__` 存在性
- 必需字段完整性: name, description, usage, version, author
- 版本号格式: 符合语义化版本规范
- 依赖声明格式
- 额外字段有效性

错误级别:
- ERROR: 缺少 `__plugin_meta__` 或必需字段
- WARNING: 版本号格式不规范
- INFO: 建议添加可选字段

**3. 组件检查 (component)**

检查内容:
- 组件类继承正确性
- 必需方法实现
- 方法签名正确性
- 类型注解完整性
- 组件信息定义正确性
- 组件注册正确性

错误级别:
- ERROR: 继承错误、缺少必需方法
- WARNING: 缺少类型注解
- INFO: 可优化的实现

**4. 配置检查 (config)**

检查内容:
- 配置文件格式 (TOML)
- 配置 Schema 定义
- 配置字段类型
- 默认值设置
- 配置文件与 Schema 一致性

错误级别:
- ERROR: 配置文件格式错误
- WARNING: Schema 定义不完整
- INFO: 建议的配置优化

**5. 依赖检查 (dependency)**

检查内容:
- Python 依赖可安装性
- 插件依赖存在性
- 循环依赖检测
- 版本冲突检测
- 依赖安全性

错误级别:
- ERROR: 循环依赖、版本冲突
- WARNING: 依赖不可用
- INFO: 依赖更新建议

**6. 类型检查 (type)**

使用 mypy 进行静态类型检查：
```bash
mypy --strict plugin_path
```

**7. 代码风格检查 (style)**

使用 ruff 进行代码风格检查：
```bash
ruff check plugin_path
```

**8. 安全检查 (security)**

使用 bandit 进行安全检查：
```bash
bandit -r plugin_path
```

#### 报告格式

**Console 格式:**
```
🔍 正在检查插件: my_plugin

📋 结构检查
  ✅ 必需文件完整
  ⚠️  缺少推荐目录: docs/
  
📝 元数据检查
  ✅ 元数据完整
  
🧩 组件检查
  ✅ Action 组件: SendMessage
  ❌ Action 组件: ReplyAction - 缺少 handle_action 方法
  
📦 依赖检查
  ✅ Python 依赖正常
  ⚠️  插件依赖 'core_plugin' 未找到
  
📊 检查摘要
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  总计: 10 个检查项
  ✅ 通过: 7
  ⚠️  警告: 2  
  ❌ 错误: 1
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**JSON 格式:**
```json
{
  "plugin_name": "my_plugin",
  "timestamp": "2025-12-13T10:30:00",
  "summary": {
    "total": 10,
    "passed": 7,
    "warnings": 2,
    "errors": 1
  },
  "checks": [
    {
      "category": "structure",
      "items": [
        {
          "level": "info",
          "message": "必需文件完整",
          "passed": true
        },
        {
          "level": "warning",
          "message": "缺少推荐目录: docs/",
          "passed": false,
          "fixable": false
        }
      ]
    },
    {
      "category": "component",
      "items": [
        {
          "level": "error",
          "message": "Action 组件: ReplyAction - 缺少 handle_action 方法",
          "file": "components/actions/reply_action.py",
          "line": 10,
          "passed": false,
          "fixable": false
        }
      ]
    }
  ]
}
```

### 1.4 mpdt test

#### 完整命令格式
```bash
mpdt test [TEST_PATH] [OPTIONS]
```

#### 参数说明

**位置参数:**
- `TEST_PATH`: 测试文件或目录路径
  - 可选，默认运行所有测试

**选项参数:**
- `--coverage, -c`: 生成覆盖率报告
  - 类型: bool flag
  
- `--cov-report`: 覆盖率报告格式
  - 可选值: `term`, `html`, `xml`, `json`
  - 默认: `term`
  
- `--min-coverage`: 最低覆盖率要求
  - 类型: int (0-100)
  - 默认: 80
  
- `--verbose, -v`: 详细输出
  - 类型: bool flag
  
- `--markers, -m`: 只运行特定标记的测试
  - 示例: `--markers "not slow"`
  
- `--keyword, -k`: 只运行匹配关键词的测试
  
- `--parallel, -n`: 并行运行测试
  - 类型: int (worker 数量)
  - 默认: 1
  
- `--watch`: 监控模式，文件变化时自动运行
  - 类型: bool flag

#### 测试组织

**测试文件命名:**
- 文件名: `test_*.py` 或 `*_test.py`
- 类名: `Test*`
- 方法名: `test_*`

**测试目录结构:**
```
tests/
├── __init__.py
├── conftest.py              # pytest 配置和 fixtures
├── test_plugin.py           # 插件整体测试
├── components/
│   ├── test_actions.py      # Action 组件测试
│   ├── test_commands.py     # Command 组件测试
│   └── test_tools.py        # Tool 组件测试
├── integration/             # 集成测试
│   └── test_workflow.py
└── performance/             # 性能测试
    └── test_performance.py
```

### 1.5 mpdt build

#### 完整命令格式
```bash
mpdt build [OPTIONS]
```

#### 参数说明

**选项参数:**
- `--output, -o`: 输出目录
  - 默认: `dist/`
  
- `--with-docs`: 包含文档
  - 类型: bool flag
  
- `--format`: 构建格式
  - 可选值: `zip`, `tar.gz`, `wheel`
  - 默认: `zip`
  
- `--include-deps`: 包含依赖
  - 类型: bool flag
  
- `--version`: 指定版本号
  - 如不指定，从元数据读取
  
- `--bump`: 自动升级版本号
  - 可选值: `major`, `minor`, `patch`

#### 构建流程

1. **验证**: 运行所有检查确保插件正常
2. **测试**: 运行所有测试
3. **文档**: 生成文档（如指定）
4. **打包**: 创建分发包
5. **签名**: 对包进行签名（可选）

### 1.6 mpdt dev

#### 完整命令格式
```bash
mpdt dev [OPTIONS]
```

#### 参数说明

**选项参数:**
- `--port, -p`: 开发服务器端口
  - 类型: int
  - 默认: 8080
  
- `--host`: 绑定的主机地址
  - 默认: `127.0.0.1`
  
- `--check-on-save`: 保存时自动检查
  - 类型: bool flag
  - 默认: true
  
- `--test-on-save`: 保存时自动测试
  - 类型: bool flag
  
- `--reload`: 代码变化时重载
  - 类型: bool flag
  - 默认: true
  
- `--debug`: 启用调试模式
  - 类型: bool flag

#### 开发模式功能

**文件监控:**
- 监控 `*.py`, `*.toml`, `*.yaml` 文件变化
- 排除 `__pycache__`, `.pytest_cache`, `*.pyc`

**自动任务:**
- 文件保存 → 代码格式化 (ruff format)
- 文件保存 → 类型检查 (mypy)
- 文件保存 → 运行测试 (可选)
- 文件保存 → 重新加载插件

**实时反馈:**
- 终端彩色输出
- 错误高亮显示
- 测试结果实时显示
- 性能统计

## 2. 配置文件规范

### 2.1 .mpdtrc.toml

项目根目录下的 MPDT 配置文件。

```toml
[mpdt]
# 项目基本信息
project_name = "my_plugin"
version = "1.0.0"

[mpdt.check]
# 检查配置
level = "warning"              # error, warning, info
auto_fix = false
ignore_patterns = [
    "tests/*",
    "*.pyc",
    "__pycache__/*",
]
# 禁用特定检查
disabled_checks = []

[mpdt.test]
# 测试配置
coverage_threshold = 80
pytest_args = ["-v", "--tb=short"]
parallel = false
watch_patterns = ["**/*.py"]

[mpdt.build]
# 构建配置
output_dir = "dist"
include_docs = true
include_tests = false
format = "zip"

[mpdt.dev]
# 开发模式配置
port = 8080
host = "127.0.0.1"
reload = true
check_on_save = true
test_on_save = false

[mpdt.templates]
# 模板默认配置
author = "Your Name"
license = "GPL-v3.0"
python_version = "^3.11"
```

### 2.2 pyproject.toml 集成

MPDT 也支持在 `pyproject.toml` 中配置：

```toml
[tool.mpdt]
project_name = "my_plugin"
version = "1.0.0"

[tool.mpdt.check]
level = "warning"
auto_fix = false

# ... 其他配置同 .mpdtrc.toml
```

## 3. 模板变量系统

### 3.1 全局变量

所有模板都可以使用的变量：

```python
{
    # 插件信息
    "plugin_name": str,              # 插件内部名称
    "plugin_display_name": str,      # 插件显示名称
    "plugin_description": str,       # 插件描述
    "plugin_usage": str,             # 使用说明
    "plugin_version": str,           # 版本号
    
    # 作者信息
    "author": str,                   # 作者名称
    "author_email": str,             # 作者邮箱
    "repository_url": str,           # 仓库地址
    
    # 许可证
    "license": str,                  # 开源协议
    "license_text": str,             # 协议全文
    
    # Python 信息
    "python_version": str,           # Python 版本要求
    
    # 时间戳
    "timestamp": str,                # 创建时间
    "year": str,                     # 当前年份
    
    # 组件信息
    "component_name": str,           # 组件名称
    "component_type": str,           # 组件类型
    "component_description": str,    # 组件描述
}
```

### 3.2 组件特定变量

**Action 组件:**
```python
{
    "activation_type": str,          # 激活类型
    "chat_type_allow": str,          # 允许的聊天类型
    "is_two_step": bool,             # 是否二步 Action
    "action_parameters": dict,       # 参数定义
}
```

**Command 组件:**
```python
{
    "command_pattern": str,          # 命令模式
    "priority": int,                 # 优先级
    "intercept_message": bool,       # 是否拦截
}
```

**Tool 组件:**
```python
{
    "tool_parameters": dict,         # 工具参数
    "llm_available": bool,           # LLM 可用性
}
```

## 4. 错误处理

### 4.1 错误代码

MPDT 使用统一的错误代码系统：

```python
class MPDTError(Exception):
    """MPDT 基础错误类"""
    code: str
    message: str

# 初始化错误 (INIT-xxx)
INIT_001 = "插件名称无效"
INIT_002 = "目标目录已存在"
INIT_003 = "模板不存在"

# 生成错误 (GEN-xxx)
GEN_001 = "组件类型无效"
GEN_002 = "组件名称无效"
GEN_003 = "输出文件已存在"

# 检查错误 (CHECK-xxx)
CHECK_001 = "插件结构不完整"
CHECK_002 = "元数据无效"
CHECK_003 = "组件定义错误"

# 测试错误 (TEST-xxx)
TEST_001 = "测试失败"
TEST_002 = "覆盖率不足"

# 构建错误 (BUILD-xxx)
BUILD_001 = "构建失败"
BUILD_002 = "依赖缺失"
```

### 4.2 错误输出格式

```
❌ 错误 [INIT-001]: 插件名称无效

详细信息:
  插件名称必须使用小写字母和下划线，以字母开头
  提供的名称: "123-plugin"
  建议: "my_plugin"

位置: __init__.py:10

建议修复:
  将插件名称改为符合规范的格式
  
文档: https://docs.mofox.studio/mpdt/errors/INIT-001
```

## 5. 性能要求

### 5.1 命令响应时间

- `mpdt init`: < 2s (不含依赖安装)
- `mpdt generate`: < 500ms
- `mpdt check`: < 5s (小型插件)
- `mpdt test`: 视测试数量而定
- `mpdt dev`: 启动 < 2s，文件变化响应 < 500ms

### 5.2 资源使用

- 内存占用: < 100MB (开发模式)
- CPU 使用: 检查时 < 50%
- 磁盘 I/O: 最小化

## 6. 安全考虑

### 6.1 代码执行

- **不执行**用户提供的代码
- 使用 AST 解析而非 eval/exec
- 沙箱化测试环境

### 6.2 依赖安全

- 检查依赖的安全漏洞
- 警告不安全的依赖版本
- 提供安全更新建议

### 6.3 文件操作

- 验证文件路径
- 防止路径遍历攻击
- 限制文件大小

## 7. 国际化 (I18n)

### 7.1 支持的语言

- 中文 (zh-CN) - 默认
- 英文 (en-US)

### 7.2 语言切换

```bash
# 使用环境变量
export MPDT_LANG=en-US
mpdt init

# 使用命令行选项
mpdt init --lang en-US
```

### 7.3 翻译文件

```
mpdt/
├── locales/
│   ├── zh-CN.json
│   └── en-US.json
```

## 8. 可访问性

### 8.1 终端兼容性

- 支持标准 ANSI 终端
- 支持 Windows 终端
- 支持 WSL
- 禁用彩色输出选项: `--no-color`

### 8.2 输出格式

- 提供纯文本输出模式
- 支持重定向到文件
- 机器可读的格式 (JSON, XML)

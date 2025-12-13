# MoFox Plugin Dev Toolkit (MPDT) 设计文档

## 📋 概述

MoFox Plugin Dev Toolkit (MPDT) 是一个类似于 Node.js 的 Vite 的 Python 开发工具，专门为 MoFox-Bot 插件系统设计。它提供了一套完整的命令行工具，帮助开发者快速创建、开发、测试和维护插件。

## 🎯 设计目标

1. **快速初始化**: 一键创建标准化的插件项目结构
2. **开发辅助**: 提供代码生成、模板管理等开发工具
3. **质量保证**: 集成静态检查、类型检查、代码规范检查
4. **测试支持**: 提供插件测试框架和工具
5. **依赖管理**: 自动管理插件依赖关系
6. **文档生成**: 自动生成插件文档和使用说明

## 🏗️ 架构设计

```
mofox-plugin-toolkit/
├── mpdt/                           # 核心包
│   ├── __init__.py
│   ├── cli.py                      # CLI 入口点
│   ├── commands/                   # 命令模块
│   │   ├── __init__.py
│   │   ├── init.py                 # 初始化命令
│   │   ├── generate.py             # 代码生成命令
│   │   ├── check.py                # 静态检查命令
│   │   ├── test.py                 # 测试命令
│   │   ├── build.py                # 构建命令
│   │   └── dev.py                  # 开发模式命令
│   ├── templates/                  # 模板系统
│   │   ├── __init__.py
│   │   ├── plugin_base.py          # 基础插件模板
│   │   ├── action_template.py      # Action 组件模板
│   │   ├── command_template.py     # Command 组件模板
│   │   ├── tool_template.py        # Tool 组件模板
│   │   ├── event_handler_template.py  # Event Handler 模板
│   │   ├── adapter_template.py     # Adapter 模板
│   │   └── prompt_template.py      # Prompt 模板
│   ├── validators/                 # 验证器
│   │   ├── __init__.py
│   │   ├── structure_validator.py  # 结构验证
│   │   ├── metadata_validator.py   # 元数据验证
│   │   ├── type_validator.py       # 类型检查
│   │   └── dependency_validator.py # 依赖验证
│   ├── analyzers/                  # 分析器
│   │   ├── __init__.py
│   │   ├── component_analyzer.py   # 组件分析
│   │   ├── dependency_analyzer.py  # 依赖分析
│   │   └── code_analyzer.py        # 代码质量分析
│   ├── generators/                 # 生成器
│   │   ├── __init__.py
│   │   ├── doc_generator.py        # 文档生成器
│   │   ├── config_generator.py     # 配置生成器
│   │   └── test_generator.py       # 测试生成器
│   ├── utils/                      # 工具函数
│   │   ├── __init__.py
│   │   ├── file_ops.py             # 文件操作
│   │   ├── template_engine.py      # 模板引擎
│   │   ├── color_printer.py        # 彩色输出
│   │   └── config_loader.py        # 配置加载
│   └── testing/                    # 测试框架
│       ├── __init__.py
│       ├── plugin_test_base.py     # 测试基类
│       ├── mock_chat_stream.py     # Mock 对象
│       └── fixtures.py             # 测试固件
├── templates/                      # 外部模板文件
│   ├── plugin_structure/           # 插件目录结构模板
│   ├── config_files/               # 配置文件模板
│   └── docs/                       # 文档模板
├── tests/                          # 工具包测试
├── setup.py                        # 安装配置
├── pyproject.toml                  # 项目配置
└── README.md                       # 使用文档
```

## 🚀 核心功能

### 1. 初始化命令 (`mpdt init`)

创建新的插件项目，提供交互式问答来配置插件。

#### 命令格式
```bash
mpdt init [plugin_name] [options]
```

#### 功能特性
- **交互式创建**: 通过问答式界面收集插件信息
- **模板选择**: 提供多种插件模板（基础插件、Action插件、Tool插件等）
- **自动生成**: 自动创建标准化的目录结构和文件
- **依赖配置**: 自动配置 Python 依赖和插件依赖

#### 生成的目录结构
```
my_awesome_plugin/
├── __init__.py                     # 插件元数据
├── plugin.py                       # 插件主类
├── config/
│   └── config.toml                 # 配置文件
├── components/                     # 组件目录
│   ├── __init__.py
│   ├── actions/                    # Action 组件
│   │   └── __init__.py
│   ├── commands/                   # Command 组件
│   │   └── __init__.py
│   ├── tools/                      # Tool 组件
│   │   └── __init__.py
│   └── events/                     # Event Handler 组件
│       └── __init__.py
├── utils/                          # 工具函数
│   └── __init__.py
├── tests/                          # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   └── test_plugin.py
├── docs/                           # 文档目录
│   ├── README.md
│   └── API.md
├── pyproject.toml                  # Python 项目配置
├── requirements.txt                # 依赖列表
└── README.md                       # 插件说明
```

#### 示例
```bash
# 交互式创建
mpdt init

# 直接指定插件名
mpdt init my_plugin --template action --author "Your Name"

# 使用完整模板
mpdt init my_plugin --template full --with-examples
```

### 2. 代码生成命令 (`mpdt generate`)

快速生成各种插件组件的代码模板。

#### 命令格式
```bash
mpdt generate <component_type> <component_name> [options]
```

#### 支持的组件类型
- `action`: Action 组件
- `command`: Command 组件  
- `tool`: Tool 组件
- `event`: Event Handler 组件
- `adapter`: Adapter 组件
- `prompt`: Prompt 组件
- `plus-command`: PlusCommand 组件

#### 功能特性
- **智能模板**: 根据组件类型生成适配的代码模板
- **类型提示**: 自动添加完整的类型注解
- **文档字符串**: 生成标准的 docstring
- **示例代码**: 包含常用功能的示例实现
- **自动注册**: 自动更新插件主类的组件注册代码

#### 示例
```bash
# 生成 Action 组件
mpdt generate action SendMessage --description "发送消息的动作"

# 生成 Tool 组件
mpdt generate tool DatabaseQuery --async --with-test

# 生成 Command 组件
mpdt generate command Help --pattern "^/help" --priority 100

# 批量生成
mpdt generate action MessageAction ReplyAction ForwardAction
```

### 3. 静态检查命令 (`mpdt check`)

对插件进行全面的静态检查，确保代码质量和规范性。

#### 命令格式
```bash
mpdt check [path] [options]
```

#### 检查项目
1. **结构检查**
   - 目录结构完整性
   - 必需文件存在性
   - 文件命名规范

2. **元数据检查**
   - `__plugin_meta__` 完整性
   - 版本号格式
   - 依赖声明正确性

3. **组件检查**
   - 组件类继承正确性
   - 必需方法实现
   - 类型注解完整性
   - 方法签名正确性

4. **配置检查**
   - 配置文件格式
   - 配置 Schema 定义
   - 配置字段类型

5. **依赖检查**
   - Python 依赖可用性
   - 插件依赖存在性
   - 循环依赖检测

6. **代码质量检查**
   - 代码风格 (使用 ruff)
   - 类型检查 (使用 mypy)
   - 安全性检查 (使用 bandit)

#### 功能特性
- **多级别检查**: 支持 error、warning、info 三个级别
- **自动修复**: 对于简单问题提供自动修复选项
- **详细报告**: 生成详细的检查报告
- **持续集成**: 可集成到 CI/CD 流程

#### 示例
```bash
# 检查当前目录
mpdt check

# 检查指定插件
mpdt check path/to/plugin

# 只显示错误
mpdt check --level error

# 自动修复问题
mpdt check --fix

# 生成报告
mpdt check --report json --output report.json
```

### 4. 测试命令 (`mpdt test`)

运行插件测试，确保功能正常。

#### 命令格式
```bash
mpdt test [options]
```

#### 功能特性
- **单元测试**: 运行所有单元测试
- **集成测试**: 测试组件间交互
- **覆盖率报告**: 生成代码覆盖率报告
- **Mock 支持**: 提供常用 Mock 对象
- **性能测试**: 测试组件性能

#### 示例
```bash
# 运行所有测试
mpdt test

# 运行特定测试
mpdt test tests/test_actions.py

# 显示覆盖率
mpdt test --coverage

# 详细输出
mpdt test -v
```

### 5. 构建命令 (`mpdt build`)

构建和打包插件。

#### 命令格式
```bash
mpdt build [options]
```

#### 功能特性
- **依赖打包**: 打包所有依赖
- **版本管理**: 自动版本号管理
- **文档生成**: 自动生成文档
- **分发准备**: 生成分发包

#### 示例
```bash
# 构建插件
mpdt build

# 构建并生成文档
mpdt build --with-docs

# 指定输出目录
mpdt build --output dist/
```

### 6. 开发模式命令 (`mpdt dev`)

启动开发模式，实时监控文件变化。

#### 命令格式
```bash
mpdt dev [options]
```

#### 功能特性
- **热重载**: 文件变化自动重载
- **实时检查**: 保存时自动运行检查
- **日志监控**: 实时显示插件日志
- **调试支持**: 集成调试工具

#### 示例
```bash
# 启动开发模式
mpdt dev

# 指定端口
mpdt dev --port 8080

# 开启调试模式
mpdt dev --debug
```

## 📝 模板系统

### 模板引擎

使用 Jinja2 作为模板引擎，支持变量替换、条件判断、循环等功能。

### 模板变量

所有模板支持以下通用变量：

```python
{
    "plugin_name": "插件名称",
    "plugin_description": "插件描述",
    "author": "作者名称",
    "version": "版本号",
    "license": "开源协议",
    "python_version": "Python 版本要求",
    "timestamp": "创建时间",
    "component_name": "组件名称",
    "component_description": "组件描述",
}
```

### 组件模板示例

#### Action 组件模板

```python
"""
{{ component_description }}
"""

from typing import Any

from src.plugin_system import BaseAction, ActionInfo, ActionActivationType
from src.common.logger import get_logger

logger = get_logger("{{ plugin_name }}.{{ component_name }}")


class {{ component_name }}(BaseAction):
    """{{ component_description }}"""

    # Action 基本信息
    action_name = "{{ component_name.lower() }}"
    action_description = "{{ component_description }}"
    
    # Action 激活类型
    activation_type = ActionActivationType.ALWAYS  # 可选: ALWAYS, RANDOM, CONDITIONAL, LLM_JUDGE
    
    # Action 使用场景描述
    action_require = [
        "使用场景描述 1",
        "使用场景描述 2",
    ]
    
    # Action 参数定义
    action_parameters = {
        "param1": "参数1描述",
        "param2": "参数2描述",
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_prefix = f"[{{ component_name }}]"
    
    async def handle_action(self) -> tuple[bool, str]:
        """
        执行 Action 的主要逻辑
        
        Returns:
            tuple[bool, str]: (是否成功, 返回消息)
        """
        try:
            logger.info(f"{self.log_prefix} 开始执行动作")
            
            # TODO: 实现你的 Action 逻辑
            
            # 示例: 发送文本消息
            # await self.send_text("Hello, World!")
            
            # 示例: 调用其他 Action
            # success, message = await self.call_action("other_action", {"param": "value"})
            
            return True, "执行成功"
            
        except Exception as e:
            logger.error(f"{self.log_prefix} 执行失败: {e}", exc_info=True)
            return False, f"执行失败: {str(e)}"
    
    @classmethod
    def get_action_info(cls) -> ActionInfo:
        """获取 Action 信息"""
        return ActionInfo(
            name=cls.action_name,
            description=cls.action_description,
            activation_type=cls.activation_type,
            action_require=cls.action_require,
            action_parameters=cls.action_parameters,
        )
```

#### Tool 组件模板

```python
"""
{{ component_description }}
"""

from typing import Any

from src.plugin_system import BaseTool, ToolInfo, ToolParamType
from src.common.logger import get_logger

logger = get_logger("{{ plugin_name }}.{{ component_name }}")


class {{ component_name }}(BaseTool):
    """{{ component_description }}"""

    # Tool 基本信息
    tool_name = "{{ component_name.lower() }}"
    tool_description = "{{ component_description }}"
    
    # Tool 参数定义
    tool_parameters = {
        "param1": {
            "type": ToolParamType.STRING,
            "description": "参数1描述",
            "required": True,
        },
        "param2": {
            "type": ToolParamType.NUMBER,
            "description": "参数2描述",
            "required": False,
            "default": 0,
        },
    }
    
    def __init__(self, plugin_config: dict[str, Any] | None = None, chat_stream: Any = None):
        super().__init__(plugin_config, chat_stream)
        self.log_prefix = f"[{{ component_name }}]"
    
    async def execute(self, **kwargs) -> dict[str, Any]:
        """
        执行 Tool 的主要逻辑
        
        Args:
            **kwargs: Tool 参数
            
        Returns:
            dict[str, Any]: 执行结果
        """
        try:
            logger.info(f"{self.log_prefix} 开始执行工具")
            
            # 获取参数
            param1 = kwargs.get("param1")
            param2 = kwargs.get("param2", 0)
            
            # TODO: 实现你的 Tool 逻辑
            result = f"处理 {param1} 和 {param2}"
            
            return {
                "success": True,
                "result": result,
            }
            
        except Exception as e:
            logger.error(f"{self.log_prefix} 执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    @classmethod
    def get_tool_info(cls) -> ToolInfo:
        """获取 Tool 信息"""
        return ToolInfo(
            name=cls.tool_name,
            description=cls.tool_description,
            parameters=cls.tool_parameters,
        )
```

#### Command 组件模板

```python
"""
{{ component_description }}
"""

from src.plugin_system import BaseCommand, CommandInfo, ChatType
from src.database.models import DatabaseMessages
from src.common.logger import get_logger

logger = get_logger("{{ plugin_name }}.{{ component_name }}")


class {{ component_name }}(BaseCommand):
    """{{ component_description }}"""

    # Command 基本信息
    command_name = "{{ component_name.lower() }}"
    command_description = "{{ component_description }}"
    command_pattern = r"^/{{ component_name.lower() }}(\s+.*)?$"
    
    # 允许的聊天类型
    chat_type_allow = ChatType.ALL  # 可选: PRIVATE, GROUP, ALL
    
    # 优先级（数字越大优先级越高）
    priority = 0
    
    # 是否拦截消息（执行后不再传递给其他组件）
    intercept_message = False
    
    def __init__(self, message: DatabaseMessages, plugin_config: dict | None = None):
        super().__init__(message, plugin_config)
        self.log_prefix = f"[{{ component_name }}]"
    
    async def execute(self) -> tuple[bool, str | None, bool]:
        """
        执行 Command
        
        Returns:
            tuple[bool, str | None, bool]: 
                - bool: 是否执行成功
                - str | None: 回复消息
                - bool: 是否继续处理（False 表示拦截）
        """
        try:
            logger.info(f"{self.log_prefix} 开始执行命令")
            
            # 获取命令参数
            args = self.parse_args()
            
            # TODO: 实现你的 Command 逻辑
            response = f"命令执行成功，参数: {args}"
            
            return True, response, not self.intercept_message
            
        except Exception as e:
            logger.error(f"{self.log_prefix} 执行失败: {e}", exc_info=True)
            return False, f"命令执行失败: {str(e)}", True
    
    def parse_args(self) -> dict[str, Any]:
        """解析命令参数"""
        # TODO: 根据 command_pattern 解析参数
        return {}
    
    @classmethod
    def get_command_info(cls) -> CommandInfo:
        """获取 Command 信息"""
        return CommandInfo(
            name=cls.command_name,
            description=cls.command_description,
            pattern=cls.command_pattern,
            chat_type_allow=cls.chat_type_allow,
            priority=cls.priority,
        )
```

## 🔍 验证器设计

### 结构验证器

检查插件目录结构的完整性和规范性。

```python
class StructureValidator:
    """插件结构验证器"""
    
    REQUIRED_FILES = [
        "__init__.py",
        "plugin.py",
    ]
    
    REQUIRED_DIRS = [
        "config",
    ]
    
    RECOMMENDED_DIRS = [
        "components",
        "utils",
        "tests",
        "docs",
    ]
    
    def validate(self, plugin_path: Path) -> ValidationResult:
        """验证插件结构"""
        pass
```

### 元数据验证器

验证插件元数据的完整性和正确性。

```python
class MetadataValidator:
    """元数据验证器"""
    
    REQUIRED_FIELDS = [
        "name",
        "description",
        "usage",
        "version",
        "author",
    ]
    
    def validate(self, metadata: PluginMetadata) -> ValidationResult:
        """验证元数据"""
        pass
```

### 类型验证器

使用 mypy 进行静态类型检查。

```python
class TypeValidator:
    """类型验证器"""
    
    def validate(self, plugin_path: Path) -> ValidationResult:
        """运行 mypy 类型检查"""
        pass
```

### 依赖验证器

检查插件依赖的正确性和可用性。

```python
class DependencyValidator:
    """依赖验证器"""
    
    def validate_python_deps(self, dependencies: list) -> ValidationResult:
        """验证 Python 依赖"""
        pass
    
    def validate_plugin_deps(self, dependencies: list) -> ValidationResult:
        """验证插件依赖"""
        pass
    
    def detect_circular_deps(self) -> ValidationResult:
        """检测循环依赖"""
        pass
```

## 📊 分析器设计

### 组件分析器

分析插件中的组件信息。

```python
class ComponentAnalyzer:
    """组件分析器"""
    
    def analyze_plugin(self, plugin_path: Path) -> PluginAnalysisResult:
        """分析插件"""
        return {
            "actions": self.find_actions(plugin_path),
            "commands": self.find_commands(plugin_path),
            "tools": self.find_tools(plugin_path),
            "events": self.find_event_handlers(plugin_path),
        }
    
    def find_actions(self, plugin_path: Path) -> list[ActionInfo]:
        """查找所有 Action 组件"""
        pass
```

### 依赖分析器

分析插件依赖关系。

```python
class DependencyAnalyzer:
    """依赖分析器"""
    
    def analyze_dependencies(self, plugin_path: Path) -> DependencyGraph:
        """分析依赖关系"""
        pass
    
    def build_dependency_graph(self) -> nx.DiGraph:
        """构建依赖图"""
        pass
```

### 代码分析器

分析代码质量和复杂度。

```python
class CodeAnalyzer:
    """代码质量分析器"""
    
    def analyze_complexity(self, file_path: Path) -> ComplexityReport:
        """分析代码复杂度"""
        pass
    
    def analyze_coverage(self, plugin_path: Path) -> CoverageReport:
        """分析测试覆盖率"""
        pass
```

## 🧪 测试框架

### 测试基类

提供插件测试的基础设施。

```python
class PluginTestBase:
    """插件测试基类"""
    
    @pytest.fixture
    def mock_chat_stream(self):
        """Mock ChatStream 对象"""
        pass
    
    @pytest.fixture
    def mock_plugin_config(self):
        """Mock 插件配置"""
        pass
    
    @pytest.fixture
    def mock_database(self):
        """Mock 数据库"""
        pass
```

### Mock 对象

提供常用的 Mock 对象。

```python
class MockChatStream:
    """Mock ChatStream 对象"""
    pass

class MockDatabaseMessages:
    """Mock 消息对象"""
    pass

class MockLLMRequest:
    """Mock LLM 请求对象"""
    pass
```

## 🎨 CLI 界面设计

使用 `rich` 库提供美观的命令行界面。

### 彩色输出

```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

# 成功消息
console.print("✅ 插件初始化成功", style="bold green")

# 错误消息
console.print("❌ 验证失败", style="bold red")

# 警告消息
console.print("⚠️ 发现潜在问题", style="bold yellow")

# 表格输出
table = Table(title="检查结果")
table.add_column("项目", style="cyan")
table.add_column("状态", style="magenta")
table.add_column("描述", style="green")
console.print(table)
```

### 进度条

```python
with Progress() as progress:
    task = progress.add_task("[cyan]检查中...", total=100)
    # 更新进度
    progress.update(task, advance=10)
```

### 交互式问答

```python
from rich.prompt import Prompt, Confirm

# 文本输入
plugin_name = Prompt.ask("请输入插件名称")

# 确认
if Confirm.ask("是否创建测试文件?"):
    create_tests()
```

## 📦 依赖管理

### Python 依赖

```toml
[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1.0"
rich = "^13.0.0"
jinja2 = "^3.1.0"
pydantic = "^2.0.0"
toml = "^0.10.2"
ruff = "^0.1.0"
mypy = "^1.7.0"
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.0"
networkx = "^3.2"  # 依赖图分析
```

## 🚀 使用示例

### 完整工作流

```bash
# 1. 创建新插件
mpdt init my_awesome_plugin --template full

# 2. 进入插件目录
cd my_awesome_plugin

# 3. 生成组件
mpdt generate action SendMessage --description "发送消息"
mpdt generate tool MessageFormatter --async
mpdt generate command Help --pattern "^/help"

# 4. 开发模式（实时监控）
mpdt dev

# 5. 运行检查
mpdt check --fix

# 6. 运行测试
mpdt test --coverage

# 7. 构建插件
mpdt build --with-docs

# 8. 查看文档
mpdt docs serve
```

## 🔧 配置文件

工具支持 `.mpdtrc.toml` 配置文件：

```toml
[mpdt]
# 项目信息
project_name = "my_plugin"
version = "1.0.0"

[mpdt.check]
# 检查配置
level = "warning"
auto_fix = false
ignore_patterns = ["tests/*", "*.pyc"]

[mpdt.test]
# 测试配置
coverage_threshold = 80
pytest_args = ["-v", "--tb=short"]

[mpdt.build]
# 构建配置
output_dir = "dist"
include_docs = true

[mpdt.templates]
# 模板配置
author = "Your Name"
license = "GPL-v3.0"
python_version = "^3.11"
```

## 📚 扩展性

### 自定义模板

用户可以创建自定义模板：

```bash
# 添加自定义模板
mpdt template add my_template path/to/template.py

# 使用自定义模板
mpdt generate --template my_template MyComponent
```

### 插件系统

工具本身支持插件扩展：

```python
from mpdt import MPDTPlugin

class MyCustomChecker(MPDTPlugin):
    """自定义检查器插件"""
    
    def check(self, plugin_path: Path) -> ValidationResult:
        # 自定义检查逻辑
        pass
```

## 🎯 开发路线图

### Phase 1: 核心功能 (v0.1.0)
- [x] 项目架构设计
- [ ] CLI 框架搭建
- [ ] 初始化命令实现
- [ ] 基础模板系统
- [ ] 结构验证器

### Phase 2: 代码生成 (v0.2.0)
- [ ] 组件模板完善
- [ ] 代码生成命令
- [ ] 模板变量系统
- [ ] 自定义模板支持

### Phase 3: 静态检查 (v0.3.0)
- [ ] 完整的验证器系统
- [ ] 类型检查集成
- [ ] 代码风格检查
- [ ] 自动修复功能

### Phase 4: 测试框架 (v0.4.0)
- [ ] 测试基类实现
- [ ] Mock 对象库
- [ ] 测试生成器
- [ ] 覆盖率报告

### Phase 5: 高级功能 (v0.5.0)
- [ ] 开发模式
- [ ] 文档生成
- [ ] 依赖分析
- [ ] 性能分析

### Phase 6: 生态完善 (v1.0.0)
- [ ] 插件市场集成
- [ ] CI/CD 集成
- [ ] 云端模板库
- [ ] 完整文档

## 📖 参考资料

- [MoFox-Bot 插件系统文档](../plugin_system_docs.md)
- [Vite 官方文档](https://vitejs.dev/)
- [Click 文档](https://click.palletsprojects.com/)
- [Rich 文档](https://rich.readthedocs.io/)

## 📄 许可证

GPL-v3.0-or-later

## 👥 贡献

欢迎贡献代码和建议！请参考 [CONTRIBUTING.md](CONTRIBUTING.md)。

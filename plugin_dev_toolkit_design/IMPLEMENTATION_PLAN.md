# 实现计划

## Phase 1: 基础框架 (Week 1-2)

### 目标
建立项目基础结构，实现基本的 CLI 框架和核心工具函数。

### 任务清单

#### 1.1 项目初始化
- [ ] 创建项目目录结构
- [ ] 设置 pyproject.toml
- [ ] 配置开发环境
- [ ] 设置 git 仓库
- [ ] 创建 README.md

#### 1.2 CLI 框架
- [ ] 安装并配置 Click
- [ ] 创建主命令组
- [ ] 实现基本的命令路由
- [ ] 添加全局选项 (--help, --version, --verbose)
- [ ] 配置日志系统

```python
# mpdt/cli.py
import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option(version="0.1.0")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def cli(verbose):
    """MoFox Plugin Dev Toolkit - 插件开发工具"""
    if verbose:
        console.print("[bold green]MPDT v0.1.0[/bold green]")

@cli.command()
def init():
    """初始化新插件"""
    console.print("🚀 初始化插件...")

if __name__ == "__main__":
    cli()
```

#### 1.3 工具函数库
- [ ] 文件操作工具 (file_ops.py)
  - [ ] 安全的文件读写
  - [ ] 目录创建和遍历
  - [ ] 文件复制和移动
  
- [ ] 模板引擎 (template_engine.py)
  - [ ] 集成 Jinja2
  - [ ] 模板加载和渲染
  - [ ] 变量系统
  
- [ ] 彩色输出 (color_printer.py)
  - [ ] 使用 rich 库
  - [ ] 统一的输出样式
  - [ ] 进度条和表格
  
- [ ] 配置加载器 (config_loader.py)
  - [ ] TOML 文件解析
  - [ ] 配置合并和验证
  - [ ] 默认配置

#### 1.4 测试框架
- [ ] 设置 pytest
- [ ] 创建测试工具类
- [ ] 添加 CI/CD 配置

### 可交付成果
- 可运行的 CLI 程序
- 基础工具函数库
- 单元测试覆盖率 > 80%

---

## Phase 2: 初始化命令 (Week 3-4)

### 目标
实现完整的 `mpdt init` 命令，支持交互式和非交互式插件创建。

### 任务清单

#### 2.1 交互式界面
- [ ] 使用 questionary 库实现问答
- [ ] 设计问题流程
- [ ] 添加输入验证
- [ ] 实现默认值读取 (git config)

```python
# mpdt/commands/init.py
import questionary
from rich.console import Console

console = Console()

def interactive_init():
    """交互式初始化"""
    answers = questionary.form(
        plugin_name=questionary.text(
            "插件名称:",
            validate=lambda x: bool(re.match(r"^[a-z][a-z0-9_]*$", x))
        ),
        description=questionary.text("插件描述:"),
        template=questionary.select(
            "选择模板:",
            choices=["basic", "action", "tool", "command", "full"]
        ),
    ).ask()
    
    return answers
```

#### 2.2 模板系统
- [ ] 创建基础插件模板
- [ ] 创建 Action 插件模板
- [ ] 创建 Tool 插件模板
- [ ] 创建 Command 插件模板
- [ ] 创建完整插件模板
- [ ] 模板变量系统

**模板文件结构:**
```
templates/
├── basic/
│   ├── {{plugin_name}}/
│   │   ├── __init__.py.jinja
│   │   ├── plugin.py.jinja
│   │   └── config/
│   │       └── config.toml.jinja
├── action/
├── tool/
├── command/
└── full/
```

#### 2.3 文件生成
- [ ] 目录结构创建
- [ ] 文件从模板生成
- [ ] 权限设置
- [ ] Git 初始化 (可选)

#### 2.4 依赖处理
- [ ] 生成 requirements.txt
- [ ] 生成 pyproject.toml
- [ ] 依赖安装提示

#### 2.5 后处理
- [ ] 成功消息输出
- [ ] 下一步指引
- [ ] 生成项目报告

### 可交付成果
- 完整的 `mpdt init` 命令
- 5 套插件模板
- 详细的用户文档

---

## Phase 3: 代码生成命令 (Week 5-6)

### 目标
实现 `mpdt generate` 命令，支持生成各种组件。

### 任务清单

#### 3.1 组件模板
- [ ] Action 组件模板
- [ ] Command 组件模板
- [ ] Tool 组件模板
- [ ] Event Handler 模板
- [ ] Adapter 模板
- [ ] Prompt 模板
- [ ] PlusCommand 模板

每个模板包含:
- 完整的类定义
- 类型注解
- 文档字符串
- 示例实现
- 对应的测试文件模板

#### 3.2 代码生成逻辑
- [ ] 解析命令参数
- [ ] 验证组件名称
- [ ] 确定输出路径
- [ ] 渲染模板
- [ ] 写入文件
- [ ] 更新插件主类

```python
# mpdt/commands/generate.py
def generate_component(
    component_type: str,
    component_name: str,
    options: dict
) -> bool:
    """生成组件"""
    # 1. 加载模板
    template = load_template(component_type)
    
    # 2. 准备变量
    context = prepare_context(component_name, options)
    
    # 3. 渲染模板
    code = template.render(context)
    
    # 4. 写入文件
    output_path = determine_output_path(component_type, component_name)
    write_file(output_path, code)
    
    # 5. 更新插件注册
    update_plugin_registration(component_type, component_name)
    
    return True
```

#### 3.3 插件注册自动更新
- [ ] AST 解析 plugin.py
- [ ] 添加组件导入
- [ ] 更新 get_plugin_components 方法
- [ ] 保持代码格式

#### 3.4 测试文件生成
- [ ] 组件测试模板
- [ ] Mock 对象配置
- [ ] 测试用例示例

### 可交付成果
- 完整的 `mpdt generate` 命令
- 7 种组件模板
- 自动注册功能

---

## Phase 4: 静态检查命令 (Week 7-9)

### 目标
实现全面的 `mpdt check` 命令，确保插件质量。

### 任务清单

#### 4.1 验证器实现

**结构验证器:**
```python
class StructureValidator:
    def validate(self, plugin_path: Path) -> ValidationResult:
        result = ValidationResult()
        
        # 检查必需文件
        for file in REQUIRED_FILES:
            if not (plugin_path / file).exists():
                result.add_error(f"缺少必需文件: {file}")
        
        # 检查目录结构
        for dir in REQUIRED_DIRS:
            if not (plugin_path / dir).is_dir():
                result.add_error(f"缺少必需目录: {dir}")
        
        return result
```

- [ ] 结构验证器
- [ ] 元数据验证器
- [ ] 组件验证器
- [ ] 配置验证器
- [ ] 依赖验证器

#### 4.2 类型检查集成
- [ ] 配置 mypy
- [ ] 解析 mypy 输出
- [ ] 格式化错误信息

```python
def run_mypy_check(plugin_path: Path) -> list[CheckResult]:
    """运行 mypy 类型检查"""
    result = subprocess.run(
        ["mypy", "--strict", str(plugin_path)],
        capture_output=True,
        text=True
    )
    
    return parse_mypy_output(result.stdout)
```

#### 4.3 代码风格检查
- [ ] 配置 ruff
- [ ] 解析 ruff 输出
- [ ] 自动修复功能

```python
def run_ruff_check(plugin_path: Path, fix: bool = False) -> list[CheckResult]:
    """运行 ruff 代码风格检查"""
    cmd = ["ruff", "check", str(plugin_path)]
    if fix:
        cmd.append("--fix")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return parse_ruff_output(result.stdout)
```

#### 4.4 安全检查
- [ ] 集成 bandit
- [ ] 常见安全问题检测
- [ ] 依赖安全扫描

#### 4.5 报告生成
- [ ] Console 格式
- [ ] JSON 格式
- [ ] HTML 格式
- [ ] Markdown 格式

```python
class CheckReporter:
    def generate_console_report(self, results: CheckResults):
        """生成终端报告"""
        table = Table(title="检查结果")
        table.add_column("类别")
        table.add_column("状态")
        table.add_column("描述")
        
        for result in results:
            table.add_row(
                result.category,
                "✅" if result.passed else "❌",
                result.message
            )
        
        console.print(table)
```

### 可交付成果
- 完整的检查系统
- 多种报告格式
- 自动修复功能

---

## Phase 5: 测试命令 (Week 10-11)

### 目标
实现 `mpdt test` 命令和测试框架。

### 任务清单

#### 5.1 测试基类
```python
class PluginTestBase:
    """插件测试基类"""
    
    @pytest.fixture
    def mock_chat_stream(self):
        """Mock ChatStream"""
        stream = MagicMock()
        stream.stream_id = "test_stream"
        stream.context = MagicMock()
        return stream
    
    @pytest.fixture
    def mock_plugin_config(self):
        """Mock 插件配置"""
        return {"enabled": True}
```

- [ ] 实现测试基类
- [ ] 创建 Mock 对象库
- [ ] 提供测试工具函数

#### 5.2 测试运行器
- [ ] pytest 集成
- [ ] 并行测试支持
- [ ] 测试过滤和选择

```python
def run_tests(
    test_path: str,
    coverage: bool = False,
    parallel: int = 1,
    markers: str = None
) -> TestResult:
    """运行测试"""
    args = ["pytest", test_path]
    
    if coverage:
        args.extend(["--cov", "--cov-report", "term"])
    
    if parallel > 1:
        args.extend(["-n", str(parallel)])
    
    if markers:
        args.extend(["-m", markers])
    
    result = subprocess.run(args, capture_output=True)
    return parse_pytest_output(result)
```

#### 5.3 覆盖率报告
- [ ] 集成 pytest-cov
- [ ] 多种报告格式
- [ ] 覆盖率门槛检查

#### 5.4 性能测试
- [ ] 集成 pytest-benchmark
- [ ] 性能回归检测

### 可交付成果
- 完整的测试框架
- Mock 对象库
- 测试工具集

---

## Phase 6: 构建和开发命令 (Week 12-13)

### 目标
实现 `mpdt build` 和 `mpdt dev` 命令。

### 任务清单

#### 6.1 构建命令
- [ ] 插件打包
- [ ] 依赖打包
- [ ] 版本管理
- [ ] 文档生成

```python
def build_plugin(
    plugin_path: Path,
    output_dir: Path,
    format: str = "zip"
) -> Path:
    """构建插件"""
    # 1. 验证插件
    check_result = run_checks(plugin_path)
    if not check_result.passed:
        raise BuildError("检查未通过")
    
    # 2. 运行测试
    test_result = run_tests(plugin_path)
    if not test_result.passed:
        raise BuildError("测试未通过")
    
    # 3. 生成文档
    generate_docs(plugin_path)
    
    # 4. 打包
    package_path = create_package(plugin_path, output_dir, format)
    
    return package_path
```

#### 6.2 开发模式
- [ ] 文件监控 (watchdog)
- [ ] 自动重载
- [ ] 实时检查
- [ ] 日志显示

```python
class DevServer:
    """开发服务器"""
    
    def __init__(self, plugin_path: Path):
        self.plugin_path = plugin_path
        self.observer = Observer()
    
    def start(self):
        """启动开发模式"""
        handler = PluginChangeHandler(self)
        self.observer.schedule(
            handler,
            str(self.plugin_path),
            recursive=True
        )
        self.observer.start()
        
        console.print("🚀 开发模式已启动")
        console.print(f"📁 监控目录: {self.plugin_path}")
        
    def on_file_change(self, event):
        """文件变化处理"""
        console.print(f"📝 文件变化: {event.src_path}")
        
        # 自动格式化
        run_formatter(event.src_path)
        
        # 运行检查
        run_quick_check(event.src_path)
```

### 可交付成果
- 构建系统
- 开发模式
- 热重载功能

---

## Phase 7: 文档和生态 (Week 14-15)

### 目标
完善文档，建立生态系统。

### 任务清单

#### 7.1 文档生成
- [ ] 自动生成 API 文档
- [ ] 从代码提取文档
- [ ] 生成使用示例

```python
class DocGenerator:
    """文档生成器"""
    
    def generate_api_docs(self, plugin_path: Path) -> str:
        """生成 API 文档"""
        # 解析所有组件
        components = analyze_components(plugin_path)
        
        # 生成 Markdown
        doc = "# API 文档\n\n"
        
        for component in components:
            doc += f"## {component.name}\n\n"
            doc += f"{component.description}\n\n"
            doc += self.generate_component_doc(component)
        
        return doc
```

#### 7.2 使用文档
- [ ] 快速开始指南
- [ ] 完整使用手册
- [ ] API 参考
- [ ] 最佳实践
- [ ] 常见问题

#### 7.3 示例插件
- [ ] 创建示例插件集
- [ ] 不同类型的示例
- [ ] 详细注释

#### 7.4 VS Code 扩展（可选）
- [ ] 语法高亮
- [ ] 代码补全
- [ ] 插件管理面板

### 可交付成果
- 完整文档网站
- 示例插件集
- VS Code 扩展

---

## Phase 8: 优化和发布 (Week 16)

### 目标
性能优化，准备发布。

### 任务清单

#### 8.1 性能优化
- [ ] 命令响应时间优化
- [ ] 内存使用优化
- [ ] 缓存机制
- [ ] 并发处理

#### 8.2 错误处理
- [ ] 完善错误信息
- [ ] 添加错误代码
- [ ] 错误恢复机制

#### 8.3 国际化
- [ ] 提取可翻译文本
- [ ] 添加英文翻译
- [ ] 语言切换机制

#### 8.4 发布准备
- [ ] 版本号确定
- [ ] 更新日志
- [ ] 发布说明
- [ ] PyPI 打包
- [ ] 发布到 PyPI

### 可交付成果
- 稳定的 v1.0.0 版本
- 完整的发布包
- 发布公告

---

## 开发工具和依赖

### 核心依赖
```toml
[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1.7"           # CLI 框架
rich = "^13.7.0"            # 终端美化
questionary = "^2.0.1"      # 交互式问答
jinja2 = "^3.1.2"           # 模板引擎
toml = "^0.10.2"            # TOML 解析
pydantic = "^2.5.0"         # 数据验证
watchdog = "^3.0.0"         # 文件监控
```

### 检查工具
```toml
[tool.poetry.group.check.dependencies]
mypy = "^1.7.0"             # 类型检查
ruff = "^0.1.6"             # 代码检查和格式化
bandit = "^1.7.5"           # 安全检查
```

### 测试工具
```toml
[tool.poetry.group.test.dependencies]
pytest = "^7.4.3"           # 测试框架
pytest-cov = "^4.1.0"       # 覆盖率
pytest-asyncio = "^0.21.1"  # 异步测试
pytest-mock = "^3.12.0"     # Mock
pytest-xdist = "^3.5.0"     # 并行测试
```

### 文档工具
```toml
[tool.poetry.group.docs.dependencies]
mkdocs = "^1.5.3"           # 文档生成
mkdocs-material = "^9.4.0"  # Material 主题
```

---

## 风险和缓解措施

### 风险 1: 插件系统 API 变化
**缓解**: 
- 密切关注插件系统更新
- 维护兼容性层
- 版本化模板

### 风险 2: 依赖冲突
**缓解**:
- 使用虚拟环境隔离
- 固定关键依赖版本
- 提供依赖解决工具

### 风险 3: 性能问题
**缓解**:
- 早期性能测试
- 增量检查
- 缓存优化

### 风险 4: 用户体验不佳
**缓解**:
- 早期用户测试
- 收集反馈
- 持续改进

---

## 里程碑

- **M1 (Week 2)**: 基础框架完成
- **M2 (Week 4)**: 初始化命令可用
- **M3 (Week 6)**: 代码生成功能完成
- **M4 (Week 9)**: 检查系统完成
- **M5 (Week 11)**: 测试框架完成
- **M6 (Week 13)**: 构建和开发模式完成
- **M7 (Week 15)**: 文档完成
- **M8 (Week 16)**: v1.0.0 发布

---

## 资源需求

### 人力
- 1 名全职开发者
- 预计 16 周（4 个月）

### 测试
- 至少 3 名测试用户
- 持续反馈收集

### 基础设施
- GitHub 仓库
- CI/CD (GitHub Actions)
- 文档托管 (Read the Docs)
- PyPI 账号

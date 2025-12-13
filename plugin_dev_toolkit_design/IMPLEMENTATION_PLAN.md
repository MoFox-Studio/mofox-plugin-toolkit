# 实现计划

> **更新日期**: 2025年12月13日
> 
> **当前状态**: Phase 1 和 Phase 2 基本完成，Phase 3 开始实施

---

## Phase 1: 基础框架 ✅ **已完成**

### 目标
建立项目基础结构，实现基本的 CLI 框架和核心工具函数。

### 任务清单

#### 1.1 项目初始化 ✅
- [x] 创建项目目录结构
- [x] 设置 pyproject.toml
- [x] 配置开发环境
- [x] 设置 git 仓库
- [x] 创建 README.md

#### 1.2 CLI 框架 ✅
- [x] 安装并配置 Click
- [x] 创建主命令组
- [x] 实现基本的命令路由
- [x] 添加全局选项 (--help, --version, --verbose)
- [x] 配置日志系统（使用 rich.console）


**已实现的 CLI 命令:**
```python
# mpdt/cli.py
@click.group()
@click.version_option(version=__version__, prog_name="MPDT")
@click.option("--verbose", "-v", is_flag=True, help="详细输出模式")
@click.option("--no-color", is_flag=True, help="禁用彩色输出")
def cli(ctx: click.Context, verbose: bool, no_color: bool) -> None:
    """MoFox Plugin Dev Toolkit - MoFox-Bot 插件开发工具"""
    ...

# 已实现的命令：init, generate, check, test, build, dev
```

#### 1.3 工具函数库 ✅
- [x] 文件操作工具 (file_ops.py)
  - [x] 安全的文件读写 (`safe_write_file`)
  - [x] 目录创建和遍历 (`ensure_dir`, `list_python_files`)
  - [x] 文件复制和移动 (`copy_directory`)
  - [x] 名称验证 (`validate_plugin_name`, `validate_component_name`)
  - [x] Git 用户信息获取 (`get_git_user_info`)
  
- [x] 模板引擎 (template_engine.py)
  - [x] 集成 Jinja2
  - [x] 模板加载和渲染 (`TemplateEngine` 类)
  - [x] 字符串模板渲染 (`render_string`)
  - [x] 文件模板渲染 (`render_file`, `render_to_file`)
  - [x] 通用上下文准备 (`prepare_common_context`)
  
- [x] 彩色输出 (color_printer.py)
  - [x] 使用 rich 库
  - [x] 统一的输出样式 (`print_success`, `print_error`, `print_warning`, `print_info`)
  - [x] 进度条和表格 (`create_progress`, `print_table`)
  - [x] 树形显示 (`print_tree`)
  - [x] 面板和分隔线 (`print_panel`, `print_divider`)
  
- [x] 配置加载器 (config_loader.py)
  - [x] TOML 文件解析 (`ConfigLoader` 类)
  - [x] 配置合并和验证 (`load`, `get`, `set`)
  - [x] 默认配置 (`get_default_config`)
  - [x] 配置保存 (`save`)
  - [x] 项目配置加载 (`load_mpdt_config`)

#### 1.4 测试框架 ⚠️ **部分完成**
- [x] 设置 pytest 配置（在 pyproject.toml 中）
- [ ] 创建测试工具类
- [ ] 添加单元测试
- [ ] 添加 CI/CD 配置

### 可交付成果 ✅
- ✅ 可运行的 CLI 程序
- ✅ 基础工具函数库
- ⚠️ 单元测试覆盖率 > 80% (待实施)

---

## Phase 2: 初始化命令 ✅ **已完成**

### 目标
实现完整的 `mpdt init` 命令，支持交互式和非交互式插件创建。

### 任务清单

#### 2.1 交互式界面 ✅
- [x] 使用 questionary 库实现问答 (`_interactive_init`)
- [x] 设计问题流程（插件名、描述、模板、作者、协议等）
- [x] 添加输入验证
- [x] 实现默认值读取（从 git config 获取用户信息）

**已实现的交互流程:**
```python
def _interactive_init() -> dict[str, Any]:
    """交互式初始化"""
    answers = {
        'plugin_name': questionary.text(...).ask(),
        'description': questionary.text(...).ask(),
        'template': questionary.select(...).ask(),
        'author': questionary.text(...).ask(),
        'license': questionary.select(...).ask(),
        'with_examples': questionary.confirm(...).ask(),
        'with_tests': questionary.confirm(...).ask(),
        'with_docs': questionary.confirm(...).ask(),
    }
    return answers
```

#### 2.2 模板系统 ✅
- [x] 创建基础插件模板（内联代码生成）
- [x] 创建 Action 插件模板
- [x] 创建 Tool 插件模板
- [x] 创建 Command 插件模板
- [x] 创建完整插件模板
- [x] 创建 Adapter 插件模板
- [x] 模板变量系统

**实现方式:** 使用代码生成函数而非文件模板
- `_generate_init_file()`
- `_generate_plugin_file()`
- `_generate_config_file()`
- `_generate_test_file()`
- `_generate_readme_file()`
- `_generate_pyproject_file()`

#### 2.3 文件生成 ✅
- [x] 目录结构创建 (`_create_plugin_structure`)
- [x] 文件从模板生成
- [x] 权限设置
- [x] Git 初始化(可选,通过 `--with-git` 选项)
- [x] 许可证文件生成 (支持 GPL-v3.0, MIT, Apache-2.0, BSD-3-Clause)

**生成的目录结构:**
```
<plugin_name>/
├── <plugin_name>/
│   ├── __init__.py
│   ├── plugin.py
│   └── config/
│       └── config.toml
├── tests/
│   ├── conftest.py
│   └── test_<plugin_name>.py
├── docs/
│   └── README.md
├── pyproject.toml
├── requirements.txt
├── README.md
└── LICENSE  # 🆕 自动生成的许可证文件
```

#### 2.4 依赖处理 ✅
- [x] 生成 pyproject.toml（包含依赖）
- [x] 依赖说明和安装提示

#### 2.5 后处理 ✅
- [x] 成功消息输出（带颜色和格式）
- [x] 下一步指引
- [x] 项目信息面板显示

### 可交付成果 ✅
- ✅ 完整的 `mpdt init` 命令
- ✅ 6 套插件模板(basic, action, tool, command, adapter, full)
- ✅ 自动许可证文件生成 (支持 4 种常见开源协议)
- ✅ 详细的用户文档(README.md)

---

## Phase 3: 代码生成命令 🔄 **进行中**

> **更新**: 2025年12月13日 - 开始实施 Phase 3
> **详细任务清单**: 见 [PHASE3_TODO.md](./PHASE3_TODO.md)

### 目标
实现 `mpdt generate` 命令,支持生成各种组件。

### 任务清单

#### 3.1 组件模板 ✅ **已完成**
- [x] Action 组件模板
- [x] Command 组件模板
- [x] Tool 组件模板
- [x] Event Handler 模板
- [ ] Adapter 模板 (待实现)
- [ ] Prompt 模板 (待实现)
- [ ] PlusCommand 模板 (待实现)

每个模板需要包含:
- 完整的类定义
- 类型注解
- 文档字符串
- 示例实现
- 对应的测试文件模板

#### 3.2 代码生成逻辑 ✅ **已完成**
- [x] 解析命令参数
- [x] 验证组件名称
- [x] 确定输出路径
- [x] 渲染模板
- [x] 写入文件
- [x] 更新插件主类

**计划实现示例:**
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

**当前状态:** 基础功能已实现,支持 Action、Command、Tool、Event 四种组件类型

#### 3.3 插件注册自动更新 ✅ **已完成**
- [x] 添加组件导入 (文本处理方式)
- [x] 在 get_plugin_components 方法中添加 TODO 注释
- [ ] AST 解析 plugin.py (可选,用于更复杂的场景)
- [ ] 完全自动化注册 (需要 ComponentInfo 配置)

#### 3.4 测试文件生成 📝 **待实现**
- [ ] 组件测试模板
- [ ] Mock 对象配置
- [ ] 测试用例示例

### 可交付成果
- 完整的 `mpdt generate` 命令
- 7 种组件模板
- 自动注册功能

---

## Phase 4: 静态检查命令 📝 **待开始**

### 目标
实现全面的 `mpdt check` 命令，确保插件质量。

### 任务清单

#### 4.1 验证器实现 📝 **待实现**

- [ ] 结构验证器
- [ ] 元数据验证器
- [ ] 组件验证器
- [ ] 配置验证器
- [ ] 依赖验证器

**计划实现示例:**
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

**当前状态:** 命令框架已创建（`mpdt/commands/check.py`），但功能未实现

#### 4.2 类型检查集成 📝 **待实现**
- [ ] 配置 mypy
- [ ] 解析 mypy 输出
- [ ] 格式化错误信息

#### 4.3 代码风格检查 📝 **待实现**
- [ ] 配置 ruff
- [ ] 解析 ruff 输出
- [ ] 自动修复功能

#### 4.4 安全检查 📝 **待实现**
- [ ] 集成 bandit
- [ ] 常见安全问题检测
- [ ] 依赖安全扫描

#### 4.5 报告生成 📝 **待实现**
- [ ] Console 格式
- [ ] JSON 格式
- [ ] HTML 格式
- [ ] Markdown 格式

### 可交付成果
- 完整的检查系统
- 多种报告格式
- 自动修复功能

---

## Phase 5: 测试命令 📝 **待开始**

### 目标
实现 `mpdt test` 命令和测试框架。

### 任务清单

#### 5.1 测试基类 📝 **待实现**
- [ ] 实现测试基类
- [ ] 创建 Mock 对象库
- [ ] 提供测试工具函数

**计划实现示例:**
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

#### 5.2 测试运行器 📝 **待实现**
- [ ] pytest 集成
- [ ] 并行测试支持
- [ ] 测试过滤和选择

**当前状态:** 命令框架已创建，pytest 已配置在 pyproject.toml 中

#### 5.3 覆盖率报告 📝 **待实现**
- [ ] 集成 pytest-cov
- [ ] 多种报告格式
- [ ] 覆盖率门槛检查

#### 5.4 性能测试 📝 **待实现**
- [ ] 集成 pytest-benchmark
- [ ] 性能回归检测

### 可交付成果
- 完整的测试框架
- Mock 对象库
- 测试工具集

---

## Phase 6: 构建和开发命令 📝 **待开始**

### 目标
实现 `mpdt build` 和 `mpdt dev` 命令。

### 任务清单

#### 6.1 构建命令 📝 **待实现**
- [ ] 插件打包
- [ ] 依赖打包
- [ ] 版本管理
- [ ] 文档生成

**当前状态:** 命令框架已创建（`mpdt build`），但功能未实现

#### 6.2 开发模式 📝 **待实现**
- [ ] 文件监控（使用 watchdog，已在依赖中）
- [ ] 自动重载
- [ ] 实时检查
- [ ] 日志显示

**当前状态:** 命令框架已创建（`mpdt dev`），但功能未实现
```python
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

## Phase 7: 文档和生态 📝 **待开始**

### 目标
完善文档，建立生态系统。

### 任务清单

#### 7.1 文档生成 📝 **待实现**
- [ ] 自动生成 API 文档
- [ ] 从代码提取文档
- [ ] 生成使用示例

#### 7.2 使用文档 ⚠️ **部分完成**
- [x] 快速开始指南（README.md 已创建）
- [ ] 完整使用手册
- [ ] API 参考
- [ ] 最佳实践
- [ ] 常见问题

#### 7.3 示例插件 📝 **待实现**
- [ ] 创建示例插件集
- [ ] 不同类型的示例
- [ ] 详细注释

#### 7.4 VS Code 扩展（可选）📝 **待实现**
- [ ] 语法高亮
- [ ] 代码补全
- [ ] 插件管理面板

### 可交付成果
- 完整文档网站
- 示例插件集
- VS Code 扩展（可选）

---

## Phase 8: 优化和发布 📝 **待开始**

### 目标
性能优化，准备发布。

### 任务清单

#### 8.1 性能优化 📝 **待实现**
- [ ] 命令响应时间优化
- [ ] 内存使用优化
- [ ] 缓存机制
- [ ] 并发处理

#### 8.2 错误处理 ⚠️ **部分完成**
- [x] 基础错误信息（已在工具函数中实现）
- [ ] 完善错误信息
- [ ] 添加错误代码
- [ ] 错误恢复机制

#### 8.3 国际化 📝 **待实现**
- [ ] 提取可翻译文本
- [ ] 添加英文翻译
- [ ] 语言切换机制

#### 8.4 发布准备 📝 **待实现**
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

## 开发工具和依赖 ✅ **已配置**

### 核心依赖 ✅
```toml
# pyproject.toml 中已配置
dependencies = [
    "click>=8.1.7",        # CLI 框架 ✅
    "rich>=13.7.0",        # 终端美化 ✅
    "questionary>=2.0.1",  # 交互式问答 ✅
    "jinja2>=3.1.2",       # 模板引擎 ✅
    "toml>=0.10.2",        # TOML 解析 ✅
    "pydantic>=2.5.0",     # 数据验证 ✅
    "watchdog>=3.0.0",     # 文件监控 ✅
]
```

### 开发和检查工具 ✅
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",          # 测试框架 ✅
    "pytest-cov>=4.1.0",      # 覆盖率 ✅
    "pytest-asyncio>=0.21.1", # 异步测试 ✅
    "pytest-mock>=3.12.0",    # Mock ✅
    "mypy>=1.7.0",            # 类型检查 ✅
    "ruff>=0.1.6",            # 代码检查 ✅
]

check = [
    "mypy>=1.7.0",    # 类型检查 ✅
    "ruff>=0.1.6",    # 代码检查 ✅
    "bandit>=1.7.5",  # 安全检查 ✅
]

docs = [
    "mkdocs>=1.5.3",           # 文档生成 ✅
    "mkdocs-material>=9.4.0",  # Material 主题 ✅
]
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

## 里程碑（修订版）

- **M1 ✅ (已完成)**: 基础框架完成
  - CLI 框架搭建完成
  - 工具函数库实现完成
  - 项目结构建立完成
  
- **M2 ✅ (已完成)**: 初始化命令可用
  - `mpdt init` 命令完全实现
  - 交互式界面实现
  - 6 套模板可用
  
- **M3 🔄 (进行中)**: 代码生成功能完成
  - 目标：实现 `mpdt generate` 命令
  - 当前状态：命令框架已创建，待实现具体功能
  
- **M4 📝 (待开始)**: 检查系统完成
  - 目标：实现 `mpdt check` 命令
  - 预计时间：2-3 周
  
- **M5 📝 (待开始)**: 测试框架完成
  - 目标：实现 `mpdt test` 命令
  - 预计时间：2 周
  
- **M6 📝 (待开始)**: 构建和开发模式完成
  - 目标：实现 `mpdt build` 和 `mpdt dev` 命令
  - 预计时间：2 周
  
- **M7 📝 (待开始)**: 文档完成
  - 目标：完善文档，创建示例插件
  - 预计时间：2 周
  
- **M8 📝 (待开始)**: v1.0.0 发布
  - 目标：性能优化，正式发布
  - 预计时间：1 周

---

## 当前项目状态总结

### ✅ 已完成的工作
1. **项目结构** - 完整的项目目录结构
2. **CLI 框架** - 基于 Click 的完整命令行界面
3. **工具函数库** - 4 个核心工具模块（file_ops, template_engine, color_printer, config_loader）
4. **init 命令** - 完整的插件初始化功能
5. **依赖配置** - pyproject.toml 完整配置
6. **文档** - README.md 和 DEV_README.md

### 🔄 进行中的工作
1. **generate 命令** - 命令框架已创建，待实现功能
2. **check 命令** - 命令框架已创建，待实现功能

### 📝 待实现的工作
1. **test 命令** - 测试运行和覆盖率报告
2. **build 命令** - 插件打包和发布
3. **dev 命令** - 开发模式和热重载
4. **单元测试** - 为现有代码添加测试
5. **CI/CD** - GitHub Actions 配置
6. **示例插件** - 创建参考示例
7. **完整文档** - API 参考和最佳实践

### 🎯 下一步行动
1. **优先级 1**: 实现 `mpdt generate` 命令的核心功能
2. **优先级 2**: 实现 `mpdt check` 命令的基础验证
3. **优先级 3**: 添加单元测试，提高代码质量
4. **优先级 4**: 实现 `mpdt test` 命令

---

## 资源需求

### 人力
- 1 名开发者
- 当前进度：约 40% 完成
- 预计剩余时间：6-8 周

### 测试
- 至少 3 名测试用户
- 持续反馈收集

### 基础设施
- [x] GitHub 仓库（已创建）
- [ ] CI/CD (GitHub Actions)
- [ ] 文档托管 (Read the Docs)
- [ ] PyPI 账号

---

## 更新历史

- **2025-12-13**: 根据实际项目结构更新计划，标记已完成项目
  - Phase 1 和 Phase 2 标记为已完成
  - 更新里程碑状态
  - 添加当前项目状态总结
  - 添加下一步行动计划

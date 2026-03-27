---
name: mpdt-plugin-development
description: "使用 MPDT (MoFox Plugin Dev Toolkit) 创建、开发和构建 Neo-MoFox 插件的完整工作流。适用场景：初始化新插件、生成组件、检查插件质量、构建打包、启动开发模式。关键词：mpdt、Neo-MoFox 插件、插件开发、组件生成、插件检查、插件构建、热重载开发。"
---

# MPDT 插件开发工作流

这个 Skill 提供使用 MPDT 工具进行 Neo-MoFox 插件开发的标准化流程。

## 何时使用此 Skill

当用户提到以下需求时，应使用此 Skill：

- "创建一个 Neo-MoFox 插件"
- "用 mpdt 初始化插件"
- "生成一个 action/tool/chatter 组件"
- "检查插件是否符合规范"
- "构建/打包插件"
- "启动插件开发模式"
- "给我的插件添加新组件"

## 前置条件检查

在开始之前，确认：

1. **MPDT 已安装**：在终端运行 `mpdt --version` 验证
2. **Python 环境**：Python >= 3.11
3. **工作目录**：确认当前目录位置
4. **配置状态**：运行 `mpdt config show` 查看配置（如有需要）

## 标准工作流

### 工作流 1：创建新插件（完整流程）

```
初始化 → 生成组件 → 检查质量 → 构建打包
```

#### 步骤 1：初始化插件

```bash
mpdt init [插件名称] \
  --template [模板类型] \
  --author "作者名" \
  --email "邮箱" \
  --license GPL-v3.0 \
  --output [输出目录]
```

**模板类型选择**：
- `basic` - 最小插件（仅 manifest + plugin.py）
- `action` - 包含 Action 组件示例
- `tool` - 包含 Tool 组件示例
- `chatter` - 包含 Chatter 组件（对话逻辑核心）
- `adapter` - 包含 Adapter 组件（平台适配器）
- `collection` - 包含 Collection 组件（工具集合）
- `router` - 包含 Router 组件（HTTP 路由）
- `event_handler` - 包含 EventHandler 组件
- `plus_command` - 包含增强命令组件
- `full` - 包含所有组件类型示例

**交互式模式**：
```bash
mpdt init  # 不带参数进入问答模式
```

#### 步骤 2：生成额外组件（可选）

如果需要添加更多组件：

```bash
cd [插件目录]
mpdt generate [组件类型] [组件名称] \
  --description "组件描述" \
  --root  # 如果要在根目录而非 components/ 下生成
```

**组件类型**：
- `action` - LLM 工具调用的主动操作（如发送消息、禁言）
- `tool` - LLM 可查询的工具（如计算器、翻译）
- `chatter` - 对话智能核心
- `adapter` - 平台通信适配器
- `collection` - 嵌套的 Action/Tool 集合
- `event` - 事件订阅处理器
- `plus-command` - 命令处理器（支持参数解析）
- `router` - FastAPI HTTP 路由
- `service` - 跨插件服务接口
- `config` - 配置定义

**交互式生成**：
```bash
mpdt generate  # 不带参数进入问答模式
```

#### 步骤 3：质量检查

在提交或构建前，必须运行检查：

```bash
mpdt check [插件路径] \
  --level warning \
  --report console \
  --fix  # 自动修复可修复的问题
```

**检查级别**：
- `error` - 仅显示错误
- `warning` - 显示警告和错误（推荐）
- `info` - 显示所有信息

**报告格式**：
- `console` - 终端彩色输出
- `markdown` - Markdown 报告文件
- `json` - JSON 格式（便于集成）

**跳过特定检查**（仅在必要时）：
```bash
mpdt check --no-type --no-style  # 跳过类型和风格检查
```

#### 步骤 4：构建打包

开发完成后构建为分发包：

```bash
mpdt build [插件路径] \
  --output dist \
  --format mfp \
  --bump patch \
  --with-docs
```

**格式选择**：
- `mfp` - MoFox Plugin 格式（推荐，官方标准）
- `zip` - 标准 ZIP 压缩包

**版本升级**：
- `major` - 主版本（1.0.0 -> 2.0.0）
- `minor` - 次版本（1.0.0 -> 1.1.0）
- `patch` - 补丁版本（1.0.0 -> 1.0.1）

### 工作流 2：开发调试（热重载）

适合快速迭代开发：

```bash
mpdt dev \
  --neo-mofox-path [Neo-MoFox主程序路径] \
  --plugin-path [插件路径]
```

**开发模式特性**：
- 文件修改自动检测
- 自动重载插件
- 实时日志输出
- 无需手动重启 Neo-MoFox

**首次使用配置**：
```bash
mpdt config init  # 配置 Neo-MoFox 路径和开发选项
```

## 参数化输入模式

当用户提供参数时，直接使用；否则进入交互式问答。

### 示例对话 1：用户提供完整参数


**执行**：
```bash
mpdt init my_translator --template tool --license GPL-v3.0
```

### 示例对话 2：参数不完整

**用户**："帮我生成一个 action 组件"

**AI 询问**：
- 插件在哪个目录？
- 组件叫什么名字？
- 组件的功能描述是什么？

然后执行：
```bash
cd [插件目录]
mpdt generate action [组件名] --description "[描述]"
```

### 示例对话 3：完全交互式

**用户**："我想创建一个新插件"

**AI 行动**：
```bash
mpdt init  # 进入交互式向导
```

## 错误处理策略

### 场景 1：检查失败

如果 `mpdt check` 报错：

1. **查看错误详情**：
   ```bash
   mpdt check --level info --report markdown --output check_report.md
   ```

2. **尝试自动修复**：
   ```bash
   mpdt check --fix
   ```

3. **如果仍有错误**：
   - 结构错误：检查 manifest.json 和目录结构
   - 类型错误：补充类型注解
   - 风格错误：运行 `ruff format .`

### 场景 2：构建失败

如果 `mpdt build` 失败：

1. 先运行检查：`mpdt check --fix`
2. 确认 manifest.json 格式正确
3. 确认所有必需文件都存在
4. 查看构建日志确定具体错误

### 场景 3：开发模式启动失败

如果 `mpdt dev` 失败：

1. 检查配置：`mpdt config show`
2. 测试配置：`mpdt config test`
3. 确认 Neo-MoFox 路径正确
4. 确认插件路径正确

## 最佳实践

### 1. 使用类型注解

生成的组件已包含类型注解，保持这个习惯：

```python
async def execute(self, param: str) -> dict[str, Any]:
    """示例方法"""
    return {"result": param}
```

### 2. 编写文档字符串

所有函数、类、方法必须有文档字符串：

```python
def process_data(data: list[str]) -> str:
    """
    处理数据列表。
    
    Args:
        data: 输入数据列表
        
    Returns:
        处理后的字符串结果
    """
    return " ".join(data)
```

### 3. 先检查再构建

养成习惯在构建前运行检查：

```bash
mpdt check --fix && mpdt build
```

### 4. 利用开发模式

开发阶段使用 dev 模式提高效率：

```bash
mpdt dev  # 自动热重载
```

### 5. 版本管理

使用语义化版本号：
- 破坏性变更 → `--bump major`
- 新功能 → `--bump minor`
- Bug 修复 → `--bump patch`

## 常见问题排查

### Q: 找不到 mpdt 命令

**诊断**：
```bash
which mpdt  # Linux/macOS
where mpdt  # Windows
```

**解决**：
```bash
pip install -e .  # 在 mofox-plugin-toolkit 目录下
```

### Q: 生成的组件在哪？

**默认位置**：`[插件目录]/components/[组件类型]/[组件名].py`

**使用 --root 标志**：`[插件目录]/[组件名].py`

### Q: 如何修改已生成的组件？

直接编辑生成的 Python 文件，然后运行 `mpdt check` 验证。

### Q: 配置文件在哪？

**位置**：
- Linux/macOS: `~/.config/mpdt/config.json`
- Windows: `%APPDATA%\mpdt\config.json`

**查看配置**：`mpdt config show`

## 工作流执行顺序

### 新插件开发（标准流程）

```
1. mpdt config init           ← 首次配置（可选）
2. mpdt init [名称]            ← 创建插件骨架
3. mpdt generate [组件]        ← 添加组件（重复多次）
4. mpdt check --fix           ← 质量检查
5. mpdt dev                   ← 开发调试（迭代阶段）
6. mpdt check                 ← 最终检查
7. mpdt build --bump patch    ← 构建打包
```

### 快速原型开发

```
1. mpdt init [名称] --template full  ← 使用完整模板
2. mpdt dev                         ← 直接进入开发模式
3. 边改边测试
4. mpdt check --fix                 ← 修复问题
5. mpdt build                       ← 打包
```

### 添加组件到现有插件

```
1. cd [插件目录]
2. mpdt generate [组件类型] [组件名]
3. mpdt check --fix
4. mpdt build --bump minor
```

## 输出确认

每次执行命令后，确认：

1. **成功标志**：查看 ✓ 或 "成功" 字样
2. **输出位置**：记录生成的文件路径
3. **下一步提示**：MPDT 通常会提示下一步操作

示例输出：
```
✓ 插件初始化成功: ./my_plugin
  ├── manifest.json
  ├── plugin.py
  └── components/

📝 下一步:
  1. cd my_plugin
  2. mpdt generate [组件类型]
  3. mpdt dev
```

## 安全注意事项

1. **路径校验**：仅在安全目录内执行操作
2. **覆盖确认**：使用 `--force` 前确认无误
3. **配置敏感信息**：不要在配置中存储密钥
4. **许可证合规**：遵守 GPL-3.0 要求（本仓库规范）

## 扩展阅读

- Neo-MoFox 插件开发文档
- MPDT GitHub 仓库：mofox-plugin-toolkit
- 组件架构说明：Neo-MoFox/docs/
- GPL-3.0 许可证：https://www.gnu.org/licenses/gpl-3.0.html

---

**记住**：始终先运行 `mpdt check` 再构建或提交代码。

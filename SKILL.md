---
name: mpdt-plugin-development
description: "使用 MPDT (MoFox Plugin Dev Toolkit) 创建、开发和构建 Neo-MoFox 插件。支持插件初始化、组件生成、质量检查、版本管理、构建打包、开发调试、市场发布、配置管理。关键词：mpdt、Neo-MoFox 插件、插件开发、组件生成、插件检查、插件构建、热重载开发、插件市场。"
---

# MPDT 插件开发工具命令手册

这个 Skill 提供 MPDT 工具的所有命令详细说明。

## 何时使用此 Skill

当用户提到以下需求时，应使用此 Skill：

- "创建/初始化 Neo-MoFox 插件"
- "生成组件（action/tool/chatter/adapter/router/service/config等）"
- "检查插件规范"
- "升级插件版本"
- "构建/打包插件"
- "启动开发模式/热重载"
- "发布插件到市场"
- "搜索/查看市场插件"
- "配置 MPDT 工具"

## 前置条件

- **MPDT 已安装**：运行 `mpdt --version` 验证
- **Python 环境**：Python >= 3.11
- **工作目录**：确认当前目录位置

---

# 命令分组

## 一、Plugin 插件开发命令组

### 1. `mpdt plugin init` - 初始化新插件

初始化一个新的插件项目，支持多种模板类型。

**命令格式**：
```bash
mpdt plugin init [PLUGIN_NAME] [选项]
```

**位置参数**：
- `PLUGIN_NAME`（可选）：插件名称，不提供则进入交互式模式

**选项**：
- `--template, -t <TYPE>`：模板类型（默认：basic）
  - `basic` - 最小插件（仅 manifest + plugin.py）
  - `action` - 包含 Action 组件示例
  - `tool` - 包含 Tool 组件示例
  - `chatter` - 包含 Chatter 组件
  - `adapter` - 包含 Adapter 组件
  - `collection` - 包含 Collection 组件
  - `router` - 包含 Router 组件（HTTP 路由）
  - `plus_command` - 包含增强命令组件
  - `event_handler` - 包含 EventHandler 组件
  - `full` - 包含所有组件类型示例
- `--author, -a <NAME>`：作者名称
- `--email, -e <EMAIL>`：作者电子邮箱
- `--license, -l <TYPE>`：开源协议（默认：GPL-v3.0）
  - `GPL-v3.0`
  - `MIT`
  - `Apache-2.0`
  - `BSD-3-Clause`
- `--with-docs`：创建文档文件
- `--init-git/--no-init-git`：是否初始化 Git 仓库
- `--output, -o <PATH>`：输出目录

**示例**：
```bash
# 交互式模式
mpdt plugin init

# 指定参数
mpdt plugin init my_plugin --template tool --author "张三" --email "zhangsan@example.com"

# 完整参数
mpdt plugin init weather_plugin \
  --template action \
  --author "李四" \
  --email "lisi@example.com" \
  --license MIT \
  --with-docs \
  --init-git \
  --output ./plugins
```

---

### 2. `mpdt plugin generate` - 生成插件组件

在现有插件中生成新组件，始终生成异步方法。

**命令格式**：
```bash
mpdt plugin generate [COMPONENT_TYPE] [COMPONENT_NAME] [PATH] [选项]
```

**位置参数**：
- `COMPONENT_TYPE`（可选）：组件类型
  - `action` - LLM 工具调用的主动操作
  - `tool` - LLM 可查询的工具
  - `chatter` - 对话智能核心
  - `adapter` - 平台通信适配器
  - `collection` - Action/Tool 集合
  - `event` - 事件订阅处理器
  - `plus-command` - 命令处理器
  - `router` - FastAPI HTTP 路由
  - `service` - 跨插件服务接口
  - `config` - 配置定义
- `COMPONENT_NAME`（可选）：组件名称
- `PATH`（可选）：插件根目录路径（默认为当前目录）

**选项**：
- `--description, -d <TEXT>`：组件描述
- `--force, -f`：覆盖已存在的文件
- `--root`：在插件根目录生成组件文件，而不是 components/ 文件夹

**示例**：
```bash
# 交互式模式
mpdt plugin generate

# 在 components/ 文件夹下生成
mpdt plugin generate action send_message --description "发送消息到群聊"

# 在根目录生成
mpdt plugin generate chatter my_chatter --root --description "主对话逻辑"

# 指定插件路径
mpdt plugin generate tool calculator ./my_plugin --description "计算器工具"
```

---

### 3. `mpdt plugin check` - 插件静态检查

对插件进行全面的静态代码检查，支持自动修复。

**命令格式**：
```bash
mpdt plugin check [PATH] [选项]
```

**位置参数**：
- `PATH`（可选）：插件路径（默认：当前目录）

**选项**：
- `--level, -l <LEVEL>`：显示的最低级别（默认：warning）
  - `error` - 仅显示错误
  - `warning` - 显示警告和错误
  - `info` - 显示所有信息
- `--fix`：自动修复可修复的问题
- `--report <FORMAT>`：输出报告格式（默认：console）
  - `console` - 终端彩色输出
  - `markdown` - Markdown 报告文件
  - `json` - JSON 格式
- `--output, -o <PATH>`：报告输出路径
- `--no-structure`：跳过结构检查
- `--no-metadata`：跳过元数据检查
- `--no-component`：跳过组件检查
- `--no-type`：跳过类型检查
- `--no-style`：跳过代码风格检查

**示例**：
```bash
# 基本检查
mpdt plugin check

# 检查并自动修复
mpdt plugin check --fix

# 仅显示错误级别
mpdt plugin check --level error

# 生成 Markdown 报告
mpdt plugin check --report markdown --output ./report.md

# 跳过类型和风格检查
mpdt plugin check --no-type --no-style

# 检查指定路径
mpdt plugin check ./my_plugin --level warning --fix
```

---

### 4. `mpdt plugin bump` - 提升插件版本号

提升插件的版本号（基于语义化版本控制）。

**命令格式**：
```bash
mpdt plugin bump [PATH] [选项]
```

**位置参数**：
- `PATH`（可选）：插件根目录（默认：当前目录）

**选项**：
- `--type, -t <TYPE>`：版本升级类型（默认：patch）
  - `major` - 主版本号 (1.0.0 -> 2.0.0)
  - `minor` - 次版本号 (1.0.0 -> 1.1.0)
  - `patch` - 修订号 (1.0.0 -> 1.0.1)

**示例**：
```bash
# 升级 patch 版本
mpdt plugin bump

# 升级 minor 版本
mpdt plugin bump --type minor

# 升级 major 版本
mpdt plugin bump ./my_plugin --type major
```

---

### 5. `mpdt plugin build` - 构建并打包插件

将插件构建为 .mfp 或 .zip 分发包。

**命令格式**：
```bash
mpdt plugin build [PATH] [选项]
```

**位置参数**：
- `PATH`（可选）：插件根目录（默认：当前目录）

**选项**：
- `--output, -o <PATH>`：输出目录（默认：dist）
- `--with-docs`：包含文档
- `--format <FORMAT>`：构建格式（默认：mfp）
  - `mfp` - MoFox Plugin 格式（推荐）
  - `zip` - 标准 ZIP 压缩包

**示例**：
```bash
# 基本构建
mpdt plugin build

# 包含文档
mpdt plugin build --with-docs

# 指定输出目录和格式
mpdt plugin build --output ./release --format mfp

# 构建指定插件
mpdt plugin build ./my_plugin --with-docs --output ./dist
```

---

### 6. `mpdt plugin dev` - 启动开发模式

启动开发模式，支持文件修改自动重载插件。

**命令格式**：
```bash
mpdt plugin dev [PATH] [选项]
```

**位置参数**：
- `PATH`（可选）：插件路径（默认：当前目录）

**选项**：
- `--neo-mofox-path <PATH>`：Neo-MoFox 主程序路径

**开发模式特性**：
- 文件修改自动检测
- 自动重载插件
- 实时日志输出
- 无需手动重启 Neo-MoFox

**示例**：
```bash
# 使用配置文件中的 Neo-MoFox 路径
mpdt plugin dev

# 指定路径
mpdt plugin dev ./my_plugin --neo-mofox-path /path/to/Neo-MoFox
```

---

## 二、Market 插件市场命令组

### 7. `mpdt market publish` - 一键发布插件到市场

完整流程：构建 -> GitHub 仓库 -> Release -> 市场注册。

**命令格式**：
```bash
mpdt market publish [PLUGIN_PATH] [选项]
```

**位置参数**：
- `PLUGIN_PATH`（可选）：插件路径（默认：当前目录）

**选项**：
- `--token <TOKEN>`：市场访问令牌
- `--github-token <TOKEN>`：GitHub Personal Access Token
- `--owner <NAME>`：GitHub 用户或组织名
- `--repo <NAME>`：GitHub 仓库名（默认使用插件 ID）
- `--private`：创建私有仓库
- `--output <PATH>`：输出目录（默认：dist）
- `--with-docs`：包含文档
- `--release-notes <TEXT>`：Release 说明
- `--skip-push`：跳过 Git 推送
- `--save-github-token/--no-save-github-token`：是否保存 GitHub Token

**示例**：
```bash
# 基本发布（使用配置文件中的 token）
mpdt market publish

# 指定所有参数
mpdt market publish \
  --github-token ghp_xxx \
  --owner myusername \
  --repo my-plugin \
  --with-docs \
  --release-notes "首次发布" \
  --save-github-token

# 发布到私有仓库
mpdt market publish --private --owner myorg
```

---

### 8. `mpdt market search` - 搜索公开插件

在插件市场中搜索公开插件。

**命令格式**：
```bash
mpdt market search [QUERY] [选项]
```

**位置参数**：
- `QUERY`（可选）：搜索关键词

**选项**：
- `--category <NAME>`：分类过滤
- `--tag <NAME>`：标签过滤
- `--limit <NUM>`：返回数量（默认：20）

**示例**：
```bash
# 搜索所有插件
mpdt market search

# 按关键词搜索
mpdt market search "weather"

# 按分类和标签过滤
mpdt market search --category "工具" --tag "API"

# 限制返回数量
mpdt market search "翻译" --limit 10
```

---

### 9. `mpdt market info` - 查看公开插件详情

查看指定插件的详细信息。

**命令格式**：
```bash
mpdt market info <PLUGIN_ID>
```

**位置参数**：
- `PLUGIN_ID`（必需）：插件 ID

**示例**：
```bash
mpdt market info my_awesome_plugin
```

---

### 10. `mpdt market package-update` - 打包并发布插件新版本

为已在市场注册的插件打包并发布新版本。

**命令格式**：
```bash
mpdt market package-update [PLUGIN_PATH] [选项]
```

**位置参数**：
- `PLUGIN_PATH`（可选）：插件路径（默认：当前目录）

**选项**：
- `--token <TOKEN>`：市场访问令牌
- `--github-token <TOKEN>`：GitHub Personal Access Token
- `--owner <NAME>`：GitHub 用户或组织名
- `--repo <NAME>`：GitHub 仓库名（默认使用插件 ID）
- `--with-docs`：包含文档
- `--release-notes <TEXT>`：Release 说明
- `--skip-push`：跳过 Git 推送
- `--save-github-token/--no-save-github-token`：是否保存 GitHub Token

**前置检查**：
- 插件是否已在市场注册
- 仓库是否存在且有权限
- 版本是否已存在

**示例**：
```bash
# 基本更新
mpdt market package-update

# 指定参数
mpdt market package-update \
  --github-token ghp_xxx \
  --owner myusername \
  --with-docs \
  --release-notes "修复了若干 bug"
```

---

## 三、Config 配置管理命令组

### 11. `mpdt config init` - 交互式配置向导

通过交互式问答配置 MPDT 工具。

**命令格式**：
```bash
mpdt config init
```

**配置项**：
- Neo-MoFox 主程序路径
- 市场地址
- GitHub Token
- 自动重载选项
- 重载延迟时间

**示例**：
```bash
mpdt config init
```

---

### 12. `mpdt config show` - 显示当前配置

以表格形式显示当前的 MPDT 配置。

**命令格式**：
```bash
mpdt config show
```

**示例**：
```bash
mpdt config show
```

---

### 13. `mpdt config open` - 打开配置文件

使用系统默认编辑器打开配置文件。

**命令格式**：
```bash
mpdt config open
```

**示例**：
```bash
mpdt config open
```
---

### 18. `mpdt config edit` - 编辑配置项

类似 git config 的方式编辑配置项。

**命令格式**：
```bash
mpdt config edit [KEY] [VALUE] [选项]
```

**位置参数**：
- `KEY`（可选）：配置键
- `VALUE`（可选）：配置值

**选项**：
- `--unset`：删除配置项

**支持的配置键**：
- `mofox.path` - Neo-MoFox 主程序路径
- `github.token` - GitHub Personal Access Token
- `market.url` - 插件市场地址
- `pypi.index_url` - PyPI 镜像源地址
- `editor.command` - 编辑器命令（code/pycharm/subl/vim 等）
- `dev.auto_reload` - 自动重载（true/false）
- `dev.reload_delay` - 重载延迟（秒）

**示例**：
```bash
# 设置配置
mpdt config edit mofox.path /path/to/mofox
mpdt config edit github.token ghp_xxxxx
mpdt config edit editor.command code

# 查看配置
mpdt config edit github.token

# 删除配置
mpdt config edit --unset github.token
```

---

## 四、Depend 依赖管理命令组

### 19. `mpdt depend add` - 添加依赖

添加插件或 Python 包依赖到插件。

**命令格式**：
```bash
mpdt depend add <DEPENDENCY> [选项]
```

**位置参数**：
- `DEPENDENCY`（必需）：依赖包名称和版本约束

**选项**：
- `--path <PATH>`：插件根目录（默认：当前目录）
- `--type <TYPE>`：依赖类型（默认：auto）
  - `auto` - 自动判断
  - `plugin` - Neo-MoFox 插件
  - `python` - Python 包

**示例**：
```bash
# 添加 Python 包
mpdt depend add 'requests>=2.28.0'
mpdt depend add 'aiohttp~=3.8'

# 添加插件依赖
mpdt depend add 'some-plugin>=1.0.0' --type plugin

# 指定插件路径
mpdt depend add 'httpx>=0.24.0' --path ./my_plugin
```

---

### 20. `mpdt depend search` - 搜索依赖

在插件市场或 PyPI 中搜索可用的依赖包。

**命令格式**：
```bash
mpdt depend search <QUERY> [选项]
```

**位置参数**：
- `QUERY`（必需）：搜索关键词

**选项**：
- `--type <TYPE>`：搜索类型（默认：all）
  - `all` - 全部
  - `plugin` - 仅插件
  - `python` - 仅 Python 包
- `--limit <NUM>`：返回结果数量（默认：20）

**示例**：
```bash
# 搜索所有相关包
mpdt depend search requests

# 仅搜索插件
mpdt depend search utility --type plugin

# 限制结果数量
mpdt depend search http --limit 10
```

---

### 21. `mpdt depend info` - 查看依赖信息

查看依赖包的详细信息和可用版本。

**命令格式**：
```bash
mpdt depend info <DEPENDENCY> [选项]
```

**位置参数**：
- `DEPENDENCY`（必需）：依赖包名称

**选项**：
- `--type <TYPE>`：依赖类型（默认：auto）
  - `auto` - 自动判断
  - `plugin` - Neo-MoFox 插件
  - `python` - Python 包

**示例**：
```bash
# 查看 Python 包信息
mpdt depend info requests

# 查看插件信息
mpdt depend info some-plugin --type plugin
```

---

### 22. `mpdt depend remove` - 移除依赖

从插件中移除依赖。

**命令格式**：
```bash
mpdt depend remove <DEPENDENCY> [PATH] [选项]
```

**位置参数**：
- `DEPENDENCY`（必需）：依赖包名称
- `PATH`（可选）：插件根目录（默认：当前目录）

**选项**：
- `--type <TYPE>`：依赖类型（默认：auto）
  - `auto` - 自动判断
  - `plugin` - Neo-MoFox 插件
  - `python` - Python 包

**示例**：
```bash
# 移除 Python 包
mpdt depend remove requests

# 移除插件依赖
mpdt depend remove some-plugin . --type plugin

# 指定插件路径
mpdt depend remove httpx ./my_plugin
```

---

### 23. `mpdt depend list` - 列出所有依赖

列出插件的所有依赖。

**命令格式**：
```bash
mpdt depend list [PATH] [选项]
```

**位置参数**：
- `PATH`（可选）：插件根目录（默认：当前目录）

**选项**：
- `--type <TYPE>`：依赖类型（默认：all）
  - `all` - 全部
  - `plugin` - 仅插件
  - `python` - 仅 Python 包

**示例**：
```bash
# 列出所有依赖
mpdt depend list

# 仅列出 Python 包
mpdt depend list . --type python

# 列出指定插件的依赖
mpdt depend list ./my_plugin
```

---

## 使用建议

### 参数化输入模式

当用户提供参数时，直接使用；否则进入交互式问答或提示用户提供必要参数。

**示例 1：用户提供完整参数**

**用户**："创建一个名为 my_translator 的插件，使用 tool 模板"

**AI 执行**：
```bash
mpdt plugin init my_translator --template tool
```

**示例 2：参数不完整**

**用户**："帮我生成一个 action 组件"

**AI 询问**：
- 插件在哪个目录？
- 组件叫什么名字？
- 组件的功能描述是什么？

然后执行：
```bash
cd [插件目录]
mpdt plugin generate action [组件名] --description "[描述]"
```

**示例 3：完全交互式**

**用户**："我想创建一个新插件"

**AI 执行**：
```bash
mpdt plugin init  # 进入交互式向导
```

---

## 常用命令组合参考

以下是常见的命令组合，仅供参考：

1. **新插件开发**：`init` → `generate` → `check` → `build`
2. **版本更新发布**：`bump` → `build` → `market package-update`
3. **快速开发调试**：`init` → `dev`
4. **首次发布**：`check` → `build` → `market publish`

---

## 错误处理

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

---

**记住**：始终先运行 `mpdt check` 再构建或提交代码。

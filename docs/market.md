# Market 插件市场模块

插件市场命令模块，提供完整的插件发布、管理和查询功能。

## 架构

```
mpdt/market/
├── client.py          # 市场 API 客户端
├── config.py          # 配置管理（URL、Token）
├── git.py             # Git 操作封装
├── github.py          # GitHub API 客户端
└── manifest.py        # Manifest 处理和 Payload 构建

mpdt/commands/
└── market.py          # CLI 命令实现
```

## 核心功能

### 1. 市场诊断

#### `mpdt market doctor`

检查与市场后端的连接状态。

**参数:**
- `--market-url`: 自定义市场服务器地址（可选）
- `--token`: API 认证令牌（可选）

**示例:**
```bash
mpdt market doctor
mpdt market doctor --market-url https://market.example.com
```

**输出信息:**
- 服务器可达性
- 服务状态
- 服务名称

---

### 2. 插件管理

#### `mpdt market register`

在市场中注册新插件。

**参数:**
- `--plugin-path`: 插件目录路径（默认：`.`）
- `--market-url`: 市场服务器地址（可选）
- `--token`: 作者认证令牌（可选）
- `--repository-url`: GitHub 仓库地址（可选）

**示例:**
```bash
mpdt market register
mpdt market register --plugin-path ./my-plugin
mpdt market register --repository-url https://github.com/user/repo
```

**功能:**
- 从 `manifest.toml` 读取插件元数据
- 提交插件注册请求到市场
- 返回 `plugin_id` 和状态

---

#### `mpdt market update`

更新插件的元数据信息。

**参数:**
- `--plugin-path`: 插件目录路径（默认：`.`）
- `--market-url`: 市场服务器地址（可选）
- `--token`: 作者认证令牌（可选）
- `--repository-url`: GitHub 仓库地址（可选）

**示例:**
```bash
mpdt market update
mpdt market update --repository-url https://github.com/user/new-repo
```

**功能:**
- 更新插件描述、类别、标签等信息
- 不影响已发布的版本

---

### 3. 版本管理

#### `mpdt market package`

构建插件包并显示市场元数据。

**参数:**
- `--plugin-path`: 插件目录路径（默认：`.`）
- `--output-dir`: 输出目录（默认：`dist`）
- `--with-docs`: 是否包含文档（默认：`False`）

**示例:**
```bash
mpdt market package
mpdt market package --output-dir ./release --with-docs
```

**输出信息:**
- asset_name: 包文件名
- file_size: 文件大小（字节）
- sha256: 校验和
- path: 完整路径

---

#### `mpdt market submit-version`

构建并提交新版本到市场。

**参数:**
- `--plugin-path`: 插件目录路径（默认：`.`）
- `--market-url`: 市场服务器地址（可选）
- `--token`: 作者认证令牌（可选）
- `--asset-url`: 资源下载地址（可选）
- `--release-url`: 发布页面地址（可选）
- `--output-dir`: 输出目录（默认：`dist`）
- `--with-docs`: 是否包含文档（默认：`False`）

**示例:**
```bash
mpdt market submit-version
mpdt market submit-version --asset-url https://cdn.example.com/plugin-1.0.0.mfp
```

**功能:**
- 自动构建 `.mfp` 包
- 计算 SHA256 校验和
- 提交版本元数据到市场

---

#### `mpdt market sync`

重新构建并同步版本元数据。

**参数:**
与 `submit-version` 相同

**示例:**
```bash
mpdt market sync
```

**使用场景:**
- 修复已提交版本的元数据错误
- 更新下载链接或校验和
- 重新构建包以确保一致性

---

#### `mpdt market yank`

撤回（yank）某个版本，标记为不推荐安装。

**参数:**
- `--plugin-path`: 插件目录路径（默认：`.`）
- `--version`: 要撤回的版本号（可选，默认使用当前版本）
- `--market-url`: 市场服务器地址（可选）
- `--token`: 作者认证令牌（可选）
- `--reason`: 撤回原因（可选）

**示例:**
```bash
mpdt market yank --version 1.0.0 --reason "Critical security bug"
mpdt market yank  # 撤回当前版本
```

**说明:**
- 被 yank 的版本不会出现在推荐安装列表中
- 已安装的用户不受影响
- 可以用于紧急撤回有问题的版本

---

### 4. 完整发布流程

#### `mpdt market publish`

🚀 **一键发布命令** - 自动化完整发布流程。

**参数:**
- `--plugin-path`: 插件目录路径（默认：`.`）
- `--market-url`: 市场服务器地址（可选）
- `--token`: 作者认证令牌（可选）
- `--github-token`: GitHub Personal Access Token（可选）
- `--owner`: GitHub 用户名/组织名（可选）
- `--repo`: GitHub 仓库名（可选）
- `--private`: 创建私有仓库（默认：`False`）
- `--output-dir`: 输出目录（默认：`dist`）
- `--with-docs`: 是否包含文档（默认：`False`）
- `--release-notes`: 发布说明（可选）
- `--skip-push`: 跳过 Git 推送（默认：`False`）
- `--save-token`: 保存 GitHub Token（可选）

**示例:**
```bash
# 最简单的用法（需提前配置 token）
mpdt market publish

# 指定 GitHub Token
mpdt market publish --github-token ghp_xxxxxxxxxxxx --save-token

# 自定义仓库
mpdt market publish --owner myorg --repo my-plugin --private

# 完整参数
mpdt market publish \
  --plugin-path ./my-plugin \
  --github-token ghp_xxxxxxxxxxxx \
  --owner myorg \
  --repo my-awesome-plugin \
  --release-notes "修复了关键 bug，新增 XYZ 功能" \
  --with-docs
```

**完整流程:**
1. **构建包** - 调用 `build_package()` 生成 `.mfp` 文件
2. **保存 Token** - 可选择保存 GitHub Token 到 `~/.mpdt/config.toml`
3. **GitHub 仓库** - 自动创建或确认仓库存在
4. **Git 操作**
   - 初始化 Git 仓库（如果需要）
   - 设置 remote 指向 GitHub
   - 提交更改（commit message: `Release {version}`）
   - 创建版本标签（格式: `v{version}`）
   - 推送分支和标签到 GitHub
5. **GitHub Release**
   - 创建或更新 Release
   - 上传 `.mfp` 包作为 Release Asset
   - 自动检测是否为预发布版本（版本号包含 `-`）
6. **市场注册**
   - 首次发布：注册插件到市场
   - 已存在：更新插件元数据
7. **版本提交**
   - 首次提交：创建新版本记录
   - 已存在：同步版本元数据

**自动推断规则:**
- `owner`: manifest 中的 `github_owner` → GitHub 当前用户
- `repo`: manifest 中的 `github_repo` → `plugin_id`
- `release_title`: `{plugin_id} {version}`
- `release_body`: manifest 中的 `release_notes` → `Release {version}`
- `is_prerelease`: 版本号中包含 `-` 则为 true

**错误处理:**
- 如果插件/版本已存在，自动切换到更新模式
- 网络失败会显示清晰的错误信息
- Git 操作失败时会提示具体原因

---

### 5. 查询功能

#### `mpdt market status`

查看插件在市场中的状态。

**参数:**
- `--plugin-path`: 插件目录路径（默认：`.`）
- `--market-url`: 市场服务器地址（可选）
- `--token`: 认证令牌（可选）
- `--plugin-id`: 插件 ID（可选，默认从 manifest 读取）

**示例:**
```bash
mpdt market status
mpdt market status --plugin-id my-plugin
```

**输出表格:**
| Version | Status | Sync | Yanked |
|---------|--------|------|--------|
| 1.0.0   | active | ok   | False  |
| 0.9.0   | active | ok   | True   |

---

#### `mpdt market search`

搜索公开的市场插件。

**参数:**
- `--query`: 搜索关键词（可选）
- `--category`: 分类过滤（可选）
- `--tag`: 标签过滤（可选）
- `--limit`: 结果数量限制（默认：`20`）
- `--market-url`: 市场服务器地址（可选）

**示例:**
```bash
mpdt market search --query music
mpdt market search --category entertainment --limit 50
mpdt market search --tag audio
```

**输出表格:**
| Plugin | Name | Status | Summary |
|--------|------|--------|---------|
| music-player | 音乐播放器 | active | 播放本地音乐 |

---

#### `mpdt market info`

显示插件的详细信息和版本列表。

**参数:**
- `plugin_id`: 插件 ID（必需）
- `--market-url`: 市场服务器地址（可选）

**示例:**
```bash
mpdt market info my-plugin
```

**输出信息:**
- 插件基本信息（ID、名称、状态、仓库）
- 风险提示（如果有）
- 所有版本的详细列表（版本号、状态、平台、校验和）

---

#### `mpdt market install-info`

获取推荐安装版本的详细信息。

**参数:**
- `plugin_id`: 插件 ID（必需）
- `--market-url`: 市场服务器地址（可选）
- `--host-version`: Neo-MoFox 版本（可选）
- `--plugin-api-version`: Plugin API 版本（可选）
- `--platform`: 平台名称（可选）
- `--include-prerelease`: 包含预发布版本（默认：`False`）

**示例:**
```bash
mpdt market install-info my-plugin
mpdt market install-info my-plugin --host-version 2.0.0 --platform linux
mpdt market install-info my-plugin --include-prerelease
```

**输出信息:**
- 推荐版本号
- Plugin API 版本
- Host 版本范围
- 支持的平台
- 是否为预发布版本
- 下载地址、SHA256、文件大小

---

## 配置管理

### Token 配置

**配置文件位置:** `~/.mpdt/config.toml`

**配置格式:**
```toml
[market]
url = "https://market.example.com"
token = "your-market-author-token"

[github]
token = "ghp_your_github_personal_access_token"
```

**环境变量:**
- `MPDT_MARKET_URL`: 覆盖市场服务器地址
- `MPDT_MARKET_TOKEN`: 覆盖市场认证令牌
- `GITHUB_TOKEN` / `GH_TOKEN`: 覆盖 GitHub Token

**优先级:** 命令行参数 > 环境变量 > 配置文件

---

### GitHub Token 权限要求

创建 GitHub Personal Access Token 时需要以下权限：

- `repo` - 完整的仓库访问权限
  - `repo:status` - 读取提交状态
  - `repo_deployment` - 读取部署状态
  - `public_repo` - 访问公开仓库
- `write:packages` - 上传 Release Assets（如需要）

**创建 Token:**
1. 访问 https://github.com/settings/tokens/new
2. 选择 `repo` 权限
3. 生成 Token
4. 使用 `--save-token` 参数保存到配置文件

---

## 工作流程示例

### 首次发布插件

```bash
# 1. 开发插件，确保 manifest.toml 正确配置
cd my-plugin/

# 2. 本地测试
mpdt check

# 3. 一键发布（首次需要 GitHub Token）
mpdt market publish --github-token ghp_xxxxxxxxxxxx --save-token

# 4. 检查发布状态
mpdt market status
```

---

### 发布新版本

```bash
# 1. 更新版本号（在 manifest.toml 中）
# 2. 更新 CHANGELOG
# 3. 提交代码
git add .
git commit -m "Bump version to 1.1.0"

# 4. 发布（Token 已保存）
mpdt market publish --release-notes "新增功能 XYZ，修复 bug ABC"

# 5. 验证
mpdt market info my-plugin
```

---

### 紧急撤回版本

```bash
# 发现 1.0.0 版本有严重 bug
mpdt market yank --version 1.0.0 --reason "Critical security vulnerability CVE-2026-xxxx"

# 快速发布修复版本
# 修改代码，更新版本号为 1.0.1
mpdt market publish --release-notes "Security fix for CVE-2026-xxxx"
```

---

### 仅更新元数据

```bash
# 修改 manifest.toml 中的描述、类别等
mpdt market update

# 或重新同步当前版本的元数据
mpdt market sync
```

---

## API 集成说明

### MarketClient

**主要方法:**
- `health()` - 健康检查
- `register_plugin(payload)` - 注册插件
- `update_plugin(plugin_id, payload)` - 更新插件
- `submit_version(plugin_id, payload)` - 提交版本
- `sync_version(plugin_id, payload)` - 同步版本
- `yank_version(plugin_id, version, reason)` - 撤回版本
- `status(plugin_id)` - 查询状态
- `search_plugins(query, category, tag, limit)` - 搜索插件
- `plugin_detail(plugin_id)` - 插件详情
- `plugin_versions(plugin_id)` - 版本列表
- `install_info(plugin_id, ...)` - 安装信息

---

### GitHubClient

**主要方法:**
- `current_user()` - 获取当前用户
- `ensure_repo(owner, repo, description, private)` - 确保仓库存在
- `ensure_release(owner, repo, tag, title, body, prerelease)` - 确保 Release 存在
- `upload_asset(release, file_path)` - 上传 Release Asset

---

### Git 操作

**主要函数:**
- `ensure_git_repo(path)` - 初始化 Git 仓库
- `set_remote(path, url)` - 设置 remote
- `ensure_commit(path, message)` - 确保有 commit
- `ensure_tag(path, tag)` - 创建标签
- `push_branch_and_tag(path, branch, tag, remote_url)` - 推送
- `current_branch(path)` - 获取当前分支
- `github_push_url(owner, repo, token)` - 构建推送 URL

---

## 错误处理

### 常见错误

**PLUGIN_ALREADY_EXISTS**
```
已注册的插件尝试再次注册
→ 自动切换到 update 模式
```

**VERSION_ALREADY_EXISTS**
```
已提交的版本尝试再次提交
→ 自动切换到 sync 模式
```

**UNAUTHORIZED**
```
Token 无效或过期
→ 检查 ~/.mpdt/config.toml 或环境变量
```

**REPO_PERMISSION_DENIED**
```
GitHub Token 权限不足
→ 确保 Token 包含 repo 权限
```

**GIT_NOT_CLEAN**
```
工作区有未提交的更改
→ git commit 或 git stash
```

---

## 最佳实践

### 1. 版本号规范

遵循 [SemVer](https://semver.org/) 语义化版本：
- `MAJOR.MINOR.PATCH` - 正式版本
- `MAJOR.MINOR.PATCH-alpha.N` - Alpha 预发布
- `MAJOR.MINOR.PATCH-beta.N` - Beta 预发布
- `MAJOR.MINOR.PATCH-rc.N` - Release Candidate

---

### 2. Manifest 配置

```toml
[project]
name = "my-plugin"
version = "1.0.0"
summary = "简短描述（50 字以内）"
description = "详细描述"
category = "entertainment"  # 分类
tags = ["music", "audio"]   # 标签

[project.github]
owner = "myusername"         # GitHub 用户名
repo = "my-plugin"           # 仓库名
release_notes = "发布说明"   # 每次发布时更新
```

---

### 3. CI/CD 集成

GitHub Actions 示例：

```yaml
name: Publish Plugin
on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install mpdt
        run: pip install mofox-plugin-toolkit
      - name: Publish to market
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          MPDT_MARKET_TOKEN: ${{ secrets.MARKET_TOKEN }}
        run: mpdt market publish --skip-push
```

---

### 4. 测试流程

发布前检查清单：
- [ ] 代码通过 `mpdt check`
- [ ] 版本号已更新
- [ ] CHANGELOG 已更新
- [ ] Release notes 已准备
- [ ] 本地测试通过
- [ ] Git 工作区干净

---

## 相关资源

- **市场后端 API 文档**: `/plugin_market/README.md`
- **Manifest 规范**: `manifest-spec.md`
- **插件开发指南**: `/Neo-MoFox/docs/plugin-development.md`
- **GitHub API 文档**: https://docs.github.com/rest

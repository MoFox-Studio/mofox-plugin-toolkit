# 构建命令实现设计文档

## 1. 概述

本文档详细说明 `mpdt build` 命令的实现方案，该命令用于将 MoFox-Bot 插件打包成可分发的格式。

## 2. MoFox-Bot 插件加载机制分析

### 2.1 插件目录结构

根据现有插件的分析，标准的 MoFox-Bot 插件结构如下：

```
plugin_name/
├── __init__.py              # 插件元数据声明（使用 __plugin_meta__）
├── plugin.py                # 插件主类
├── pyproject.toml          # Python 项目配置
├── requirements.txt        # 依赖声明（可选）
├── config/                 # 配置文件目录
│   └── config.toml
├── components/             # 组件目录
│   ├── actions/
│   ├── tools/
│   ├── events/
│   └── ...
├── utils/                  # 工具模块
├── docs/                   # 文档
├── tests/                  # 测试文件
└── README.md
```

### 2.2 插件加载流程

根据 `mmc/src/plugin_system/core/plugin_manager.py` 的分析：

1. **扫描插件目录** (`_load_plugin_modules_from_directory`)
   - 扫描 `src/plugins/built_in` 和 `plugins` 目录
   - 查找包含 `plugin.py` 的子目录

2. **加载插件模块** (`_load_plugin_module_file`)
   - 首先加载 `__init__.py` 获取 `__plugin_meta__`
   - 检查 Python 依赖（`python_dependencies`）
   - 检查插件依赖（`dependencies`）
   - 加载 `plugin.py` 主模块

3. **实例化插件** (`load_registered_plugin_classes`)
   - 从 `__plugin_meta__` 获取元数据
   - 使用 `PluginMetadata` 创建插件实例
   - 检查 `enable_plugin` 配置
   - 调用 `register_plugin()` 注册组件

4. **组件注册**
   - 注册 Action、Tool、Event、Adapter 等组件
   - 注册权限节点
   - 调用 `on_plugin_loaded()` 钩子

### 2.3 插件元数据

**插件元数据在 `__init__.py` 中使用 `__plugin_meta__` 定义：**

```python
from src.plugin_system.base.plugin_metadata import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="plugin_name",
    description="插件描述",
    usage="使用说明",
    version="1.0.0",
    author="作者名",
    license="GPL-v3.0",
    repository_url="https://github.com/...",
    python_dependencies=["requests>=2.28.0"],  # Python 依赖
    dependencies=["other_plugin"],             # 插件依赖
    keywords=["tag1", "tag2"],
    categories=["category1"],
    extra={"is_built_in": False},
)
```

> **注意**: `_manifest.json` 已被废弃，不再使用。所有元数据都应在 `__init__.py` 的 `__plugin_meta__` 中定义。

## 3. 构建命令设计

### 3.1 命令接口

```bash
mpdt build [OPTIONS]
```

### 3.2 命令选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--output, -o` | Path | `dist` | 输出目录 |
| `--format, -f` | Choice | `zip` | 打包格式：`zip`, `tar.gz`, `wheel` |
| `--with-docs` | Flag | False | 包含文档文件 |
| `--with-tests` | Flag | False | 包含测试文件 |
| `--bump` | Choice | None | 自动升级版本号：`major`, `minor`, `patch` |
| `--clean` | Flag | False | 构建前清理输出目录 |
| `--verify` | Flag | True | 构建后验证插件结构 |

### 3.3 构建流程

```
┌─────────────────┐
│  1. 验证项目    │
│  - 检查结构     │
│  - 验证元数据   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. 版本管理    │
│  - bump版本(可选)│
│  - 同步版本号   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. 准备构建    │
│  - 清理临时文件 │
│  - 复制源文件   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. 验证元数据  │
│  - __plugin_meta__│
│  - pyproject.toml│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. 打包        │
│  - zip/tar.gz   │
│  - wheel (可选) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  6. 验证打包    │
│  - 完整性检查   │
│  - 结构验证     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  7. 生成报告    │
│  - 构建清单     │
│  - 文件大小     │
└─────────────────┘
```

## 4. 详细实现方案

### 4.1 文件结构

```
mpdt/
└── commands/
    ├── build.py           # 构建命令主模块
    └── build_utils/
        ├── __init__.py
        ├── validator.py   # 项目验证
        ├── version.py     # 版本管理
        ├── packer.py      # 打包处理
        └── verifier.py    # 打包验证
```

### 4.2 核心模块

#### 4.2.1 build.py - 主入口

```python
"""
插件构建命令实现
"""
import os
from pathlib import Path
from typing import Literal

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mpdt.commands.build_utils.validator import ProjectValidator
from mpdt.commands.build_utils.version import VersionManager
from mpdt.commands.build_utils.packer import PluginPacker
from mpdt.commands.build_utils.verifier import PackageVerifier

console = Console()

def build_plugin(
    output_dir: str = "dist",
    format: Literal["zip", "tar.gz", "wheel"] = "zip",
    with_docs: bool = False,
    with_tests: bool = False,
    bump: Literal["major", "minor", "patch"] | None = None,
    clean: bool = False,
    verify: bool = True,
    verbose: bool = False,
) -> None:
    """
    构建和打包插件
    
    Args:
        output_dir: 输出目录
        format: 打包格式
        with_docs: 是否包含文档
        with_tests: 是否包含测试
        bump: 版本号升级类型
        clean: 是否清理输出目录
        verify: 是否验证打包结果
        verbose: 详细输出
    """
    try:
        current_dir = Path.cwd()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # 1. 验证项目结构
            task = progress.add_task("验证项目结构...", total=None)
            validator = ProjectValidator(current_dir, verbose)
            if not validator.validate_structure():
                console.print("[red]❌ 项目结构验证失败[/red]")
                return
            progress.update(task, completed=True)
            
            # 2. 版本管理
            if bump:
                task = progress.add_task(f"升级版本号 ({bump})...", total=None)
                version_manager = VersionManager(current_dir, verbose)
                new_version = version_manager.bump_version(bump)
                console.print(f"[green]✓[/green] 版本已升级到 {new_version}")
                progress.update(task, completed=True)
            
            # 3. 准备输出目录
            task = progress.add_task("准备输出目录...", total=None)
            output_path = Path(output_dir)
            if clean and output_path.exists():
                import shutil
                shutil.rmtree(output_path)
            output_path.mkdir(parents=True, exist_ok=True)
            progress.update(task, completed=True)
            
            # 4. 打包
            task = progress.add_task(f"打包插件 ({format})...", total=None)
            packer = PluginPacker(
                current_dir,
                output_path,
                with_docs=with_docs,
                with_tests=with_tests,
                verbose=verbose,
            )
            package_path = packer.pack(format)
            progress.update(task, completed=True)
            
            # 5. 验证打包
            if verify:
                task = progress.add_task("验证打包结果...", total=None)
                verifier = PackageVerifier(package_path, verbose)
                if not verifier.verify():
                    console.print("[yellow]⚠️  打包验证发现问题[/yellow]")
                progress.update(task, completed=True)
        
        # 显示构建结果
        console.print("\n[bold green]✓ 构建完成！[/bold green]")
        console.print(f"输出文件: [cyan]{package_path}[/cyan]")
        
        # 显示文件大小
        size = package_path.stat().st_size
        size_str = _format_size(size)
        console.print(f"文件大小: [cyan]{size_str}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]❌ 构建失败: {e}[/red]")
        if verbose:
            console.print_exception()
        raise click.Abort()


def _format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"
```

#### 4.2.2 validator.py - 项目验证

```python
"""
项目结构验证
"""
from pathlib import Path
from typing import Any

import toml
from rich.console import Console

console = Console()


class ProjectValidator:
    """项目验证器"""
    
    def __init__(self, project_dir: Path, verbose: bool = False):
        self.project_dir = project_dir
        self.verbose = verbose
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def validate_structure(self) -> bool:
        """验证项目结构"""
        checks = [
            self._check_required_files,
            self._check_pyproject_toml,
            self._check_init_file,
            self._check_plugin_file,
        ]
        
        for check in checks:
            if not check():
                return False
        
        if self.warnings and self.verbose:
            for warning in self.warnings:
                console.print(f"[yellow]⚠️  {warning}[/yellow]")
        
        return True
    
    def _check_required_files(self) -> bool:
        """检查必需文件"""
        required = ["__init__.py", "plugin.py", "pyproject.toml"]
        for filename in required:
            if not (self.project_dir / filename).exists():
                self.errors.append(f"缺少必需文件: {filename}")
                console.print(f"[red]✗[/red] 缺少必需文件: {filename}")
                return False
        return True
    
    def _check_pyproject_toml(self) -> bool:
        """检查 pyproject.toml"""
        pyproject_path = self.project_dir / "pyproject.toml"
        
        try:
            data = toml.load(pyproject_path)
        except Exception as e:
            self.errors.append(f"无法解析 pyproject.toml: {e}")
            console.print(f"[red]✗[/red] 无法解析 pyproject.toml: {e}")
            return False
        
        # 检查必需字段
        if "project" not in data:
            self.errors.append("pyproject.toml 中缺少 [project] 部分")
            console.print("[red]✗[/red] pyproject.toml 中缺少 [project] 部分")
            return False
        
        project = data["project"]
        required_fields = ["name", "version", "description"]
        
        for field in required_fields:
            if field not in project:
                self.errors.append(f"pyproject.toml 中缺少字段: {field}")
                console.print(f"[red]✗[/red] pyproject.toml 中缺少字段: {field}")
                return False
        
        return True
    
    def _check_init_file(self) -> bool:
        """检查 __init__.py"""
        init_path = self.project_dir / "__init__.py"
        
        content = init_path.read_text(encoding="utf-8")
        
        if "__plugin_meta__" not in content:
            self.errors.append("__init__.py 中缺少 __plugin_meta__ 声明")
            console.print("[red]✗[/red] __init__.py 中缺少 __plugin_meta__ 声明")
            return False
        
        if "PluginMetadata" not in content:
            self.warnings.append("__init__.py 中可能缺少 PluginMetadata 导入")
        
        return True
    
    def _check_plugin_file(self) -> bool:
        """检查 plugin.py"""
        plugin_path = self.project_dir / "plugin.py"
        
        content = plugin_path.read_text(encoding="utf-8")
        
        if "BasePlugin" not in content:
            self.warnings.append("plugin.py 中可能缺少 BasePlugin 导入")
        
        if "@register_plugin" not in content and "register_plugin" not in content:
            self.warnings.append("plugin.py 中可能缺少 @register_plugin 装饰器")
        
        return True
```

#### 4.2.3 version.py - 版本管理

```python
"""
版本管理
"""
from pathlib import Path
from typing import Literal

import toml
from packaging.version import Version


class VersionManager:
    """版本管理器"""
    
    def __init__(self, project_dir: Path, verbose: bool = False):
        self.project_dir = project_dir
        self.verbose = verbose
        self.pyproject_path = project_dir / "pyproject.toml"
        self.init_path = project_dir / "__init__.py"
    
    def get_current_version(self) -> str:
        """获取当前版本号"""
        data = toml.load(self.pyproject_path)
        return data["project"]["version"]
    
    def bump_version(self, bump_type: Literal["major", "minor", "patch"]) -> str:
        """升级版本号"""
        current = Version(self.get_current_version())
        
        if bump_type == "major":
            new = Version(f"{current.major + 1}.0.0")
        elif bump_type == "minor":
            new = Version(f"{current.major}.{current.minor + 1}.0")
        else:  # patch
            new = Version(f"{current.major}.{current.minor}.{current.micro + 1}")
        
        new_version = str(new)
        
        # 更新 pyproject.toml
        self._update_pyproject_version(new_version)
        
        # 更新 __init__.py
        self._update_init_version(new_version)
        
        return new_version
    
    def _update_pyproject_version(self, version: str) -> None:
        """更新 pyproject.toml 中的版本"""
        data = toml.load(self.pyproject_path)
        data["project"]["version"] = version
        
        with open(self.pyproject_path, "w", encoding="utf-8") as f:
            toml.dump(data, f)
    
    def _update_init_version(self, version: str) -> None:
        """更新 __init__.py 中的版本"""
        content = self.init_path.read_text(encoding="utf-8")
        
        # 替换 PluginMetadata 中的 version 参数
        import re
        pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
        new_content = re.sub(pattern, rf'\g<1>{version}\g<3>', content)
        
        self.init_path.write_text(new_content, encoding="utf-8")
```

#### 4.2.4 packer.py - 打包处理

```python
"""
插件打包
"""
import json
import shutil
import tempfile
from pathlib import Path
from typing import Literal

import toml


class PluginPacker:
    """插件打包器"""
    
    def __init__(
        self,
        project_dir: Path,
        output_dir: Path,
        with_docs: bool = False,
        with_tests: bool = False,
        verbose: bool = False,
    ):
        self.project_dir = project_dir
        self.output_dir = output_dir
        self.with_docs = with_docs
        self.with_tests = with_tests
        self.verbose = verbose
    
    def pack(self, format: Literal["zip", "tar.gz", "wheel"]) -> Path:
        """打包插件"""
        if format == "wheel":
            return self._pack_wheel()
        elif format == "tar.gz":
            return self._pack_tarball()
        else:  # zip
            return self._pack_zip()
    
    def _pack_zip(self) -> Path:
        """打包为 ZIP 格式"""
        plugin_name = self._get_plugin_name()
        version = self._get_version()
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plugin_path = temp_path / plugin_name
            
            # 复制文件
            self._copy_files(plugin_path)
            
            # 打包
            output_file = self.output_dir / f"{plugin_name}-{version}.zip"
            shutil.make_archive(
                str(output_file.with_suffix("")),
                "zip",
                temp_path,
                plugin_name,
            )
        
        return output_file
    
    def _pack_tarball(self) -> Path:
        """打包为 tar.gz 格式"""
        plugin_name = self._get_plugin_name()
        version = self._get_version()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            plugin_path = temp_path / plugin_name
            
            self._copy_files(plugin_path)
            
            output_file = self.output_dir / f"{plugin_name}-{version}.tar.gz"
            shutil.make_archive(
                str(output_file.with_suffix("").with_suffix("")),
                "gztar",
                temp_path,
                plugin_name,
            )
        
        return output_file
    
    def _pack_wheel(self) -> Path:
        """打包为 Wheel 格式"""
        import subprocess
        
        # 使用 setuptools 构建 wheel
        result = subprocess.run(
            ["python", "-m", "build", "--wheel", "--outdir", str(self.output_dir)],
            cwd=self.project_dir,
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"构建 wheel 失败: {result.stderr}")
        
        # 查找生成的 wheel 文件
        wheels = list(self.output_dir.glob("*.whl"))
        if not wheels:
            raise RuntimeError("未找到生成的 wheel 文件")
        
        return wheels[0]
    
    def _copy_files(self, dest: Path) -> None:
        """复制文件到目标目录"""
        dest.mkdir(parents=True, exist_ok=True)
        
        # 要复制的文件和目录
        include = [
            "__init__.py",
            "plugin.py",
            "pyproject.toml",
            "README.md",
            "LICENSE",
            "requirements.txt",
            "config/",
            "components/",
            "utils/",
        ]
        
        if self.with_docs:
            include.append("docs/")
        
        if self.with_tests:
            include.append("tests/")
        
        # 排除的文件模式
        exclude = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "*.log",
            ".git",
            ".gitignore",
        ]
        
        for item in include:
            src = self.project_dir / item
            if not src.exists():
                continue
            
            if src.is_file():
                shutil.copy2(src, dest / item)
            else:
                shutil.copytree(
                    src,
                    dest / item,
                    ignore=shutil.ignore_patterns(*exclude),
                )
    
    def _get_plugin_name(self) -> str:
        """获取插件名称"""
        data = toml.load(self.project_dir / "pyproject.toml")
        return data["project"]["name"]
    
    def _get_version(self) -> str:
        """获取版本号"""
        data = toml.load(self.project_dir / "pyproject.toml")
        return data["project"]["version"]
```

#### 4.2.5 verifier.py - 打包验证

```python
"""
打包验证
"""
import zipfile
import tarfile
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


class PackageVerifier:
    """打包验证器"""
    
    def __init__(self, package_path: Path, verbose: bool = False):
        self.package_path = package_path
        self.verbose = verbose
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def verify(self) -> bool:
        """验证打包结果"""
        suffix = self.package_path.suffix
        
        if suffix == ".zip":
            return self._verify_zip()
        elif suffix == ".gz":
            return self._verify_tarball()
        elif suffix == ".whl":
            return self._verify_wheel()
        
        return False
    
    def _verify_zip(self) -> bool:
        """验证 ZIP 包"""
        try:
            with zipfile.ZipFile(self.package_path, "r") as zf:
                # 检查必需文件
                files = zf.namelist()
                
                required = [
                    "__init__.py",
                    "plugin.py",
                ]
                
                for req in required:
                    if not any(req in f for f in files):
                        self.errors.append(f"打包缺少必需文件: {req}")
                        console.print(f"[red]✗[/red] 打包缺少必需文件: {req}")
                        return False
                
                if self.verbose:
                    console.print(f"[green]✓[/green] ZIP 包含 {len(files)} 个文件")
                
                return True
        except Exception as e:
            self.errors.append(f"验证失败: {e}")
            console.print(f"[red]✗[/red] 验证失败: {e}")
            return False
    
    def _verify_tarball(self) -> bool:
        """验证 tar.gz 包"""
        try:
            with tarfile.open(self.package_path, "r:gz") as tf:
                files = tf.getnames()
                
                required = [
                    "__init__.py",
                    "plugin.py",
                ]
                
                for req in required:
                    if not any(req in f for f in files):
                        self.errors.append(f"打包缺少必需文件: {req}")
                        console.print(f"[red]✗[/red] 打包缺少必需文件: {req}")
                        return False
                
                if self.verbose:
                    console.print(f"[green]✓[/green] tar.gz 包含 {len(files)} 个文件")
                
                return True
        except Exception as e:
            self.errors.append(f"验证失败: {e}")
            console.print(f"[red]✗[/red] 验证失败: {e}")
            return False
    
    def _verify_wheel(self) -> bool:
        """验证 Wheel 包"""
        # Wheel 是 ZIP 格式
        return self._verify_zip()
```

### 4.3 CLI 集成

在 `mpdt/cli.py` 中更新 build 命令：

```python
@cli.command()
@click.option("--output", "-o", type=click.Path(), default="dist", help="输出目录")
@click.option("--format", "-f", type=click.Choice(["zip", "tar.gz", "wheel"]), 
              default="zip", help="打包格式")
@click.option("--with-docs", is_flag=True, help="包含文档")
@click.option("--with-tests", is_flag=True, help="包含测试")
@click.option("--bump", type=click.Choice(["major", "minor", "patch"]), help="自动升级版本号")
@click.option("--clean", is_flag=True, help="构建前清理输出目录")
@click.option("--verify/--no-verify", default=True, help="验证打包结果")
@click.pass_context
def build(ctx: click.Context, output: str, format: str, with_docs: bool, 
          with_tests: bool, bump: str | None, clean: bool, verify: bool) -> None:
    """构建和打包插件"""
    from mpdt.commands.build import build_plugin
    
    try:
        build_plugin(
            output_dir=output,
            format=format,
            with_docs=with_docs,
            with_tests=with_tests,
            bump=bump,
            clean=clean,
            verify=verify,
            verbose=ctx.obj["verbose"],
        )
    except Exception as e:
        console.print(f"[bold red]❌ 构建失败: {e}[/bold red]")
        raise click.Abort()
```

## 5. 依赖管理

### 5.1 新增依赖

在 `pyproject.toml` 中添加：

```toml
dependencies = [
    # ... 现有依赖 ...
    "packaging>=23.0",  # 版本管理
    "build>=1.0.0",     # 构建 wheel
]
```

## 6. 使用示例

### 6.1 基本使用

```bash
# 构建为 ZIP 格式
mpdt build

# 构建为 tar.gz 格式
mpdt build --format tar.gz

# 构建为 wheel 格式
mpdt build --format wheel
```

### 6.2 版本管理

```bash
# 升级补丁版本 (1.0.0 -> 1.0.1)
mpdt build --bump patch

# 升级次版本 (1.0.0 -> 1.1.0)
mpdt build --bump minor

# 升级主版本 (1.0.0 -> 2.0.0)
mpdt build --bump major
```

### 6.3 包含额外文件

```bash
# 包含文档
mpdt build --with-docs

# 包含测试
mpdt build --with-tests

# 都包含
mpdt build --with-docs --with-tests
```

### 6.4 自定义输出

```bash
# 指定输出目录
mpdt build -o release

# 清理后构建
mpdt build --clean
```

## 7. 构建输出

### 7.1 输出结构

```
dist/
└── plugin_name-1.0.0.zip
    └── plugin_name/
        ├── __init__.py          # 包含 __plugin_meta__
        ├── plugin.py
        ├── pyproject.toml
        ├── README.md
        ├── LICENSE
        ├── requirements.txt     # 如果存在
        ├── config/
        ├── components/
        └── utils/
```

### 7.2 构建报告

```
✓ 验证项目结构...
✓ 打包插件 (zip)...
✓ 验证打包结果...

✓ 构建完成！
输出文件: dist/my_plugin-1.0.0.zip
文件大小: 25.43 KB
```

## 8. 错误处理

### 8.1 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| 缺少必需文件 | 项目结构不完整 | 检查 `__init__.py`, `plugin.py` |
| 无法解析 pyproject.toml | TOML 语法错误 | 验证 TOML 格式 |
| 缺少 __plugin_meta__ | 元数据未定义 | 在 `__init__.py` 中添加 |
| 版本号格式错误 | 不符合 PEP 440 | 使用 `major.minor.patch` 格式 |

### 8.2 调试模式

```bash
# 启用详细输出
mpdt build -v

# 跳过验证（不推荐）
mpdt build --no-verify
```

## 9. 安装和使用打包后的插件

### 9.1 手动安装

```bash
# 1. 解压插件包
unzip plugin_name-1.0.0.zip

# 2. 复制到插件目录
cp -r plugin_name /path/to/mmc/plugins/

# 3. 安装依赖（如果有）
pip install -r plugin_name/requirements.txt

# 4. 重启 MoFox-Bot
```

### 9.2 自动安装（未来功能）

```bash
# 使用 mpdt 安装插件
mpdt install plugin_name-1.0.0.zip

# 或从远程仓库安装
mpdt install plugin_name --from https://repo.example.com
```

## 10. 未来扩展

### 10.1 插件签名

```bash
# 生成密钥对
mpdt key generate

# 签名插件
mpdt build --sign

# 验证签名
mpdt verify plugin_name-1.0.0.zip
```

### 10.2 发布到仓库

```bash
# 发布到官方仓库
mpdt publish dist/plugin_name-1.0.0.zip

# 发布到自定义仓库
mpdt publish dist/plugin_name-1.0.0.zip --repo https://custom.repo
```

### 10.3 CI/CD 集成

```yaml
# .github/workflows/build.yml
name: Build Plugin

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install MPDT
        run: pip install mofox-plugin-toolkit
      - name: Build Plugin
        run: mpdt build --format zip --verify
      - name: Upload Artifact
        uses: actions/upload-artifact@v2
        with:
          name: plugin-package
          path: dist/*.zip
```

## 11. 总结

本文档详细说明了 `mpdt build` 命令的实现方案，包括：

1. **插件加载机制分析** - 了解 MoFox-Bot 如何加载插件
2. **构建流程设计** - 7 步构建流程
3. **核心模块实现** - 5 个核心模块的详细代码
4. **CLI 集成** - 命令行接口设计
5. **使用示例** - 各种使用场景
6. **错误处理** - 常见问题和解决方案
7. **未来扩展** - 插件签名、发布等功能

该实现方案完全兼容 MoFox-Bot 的插件系统，支持多种打包格式，并提供了完善的验证机制。

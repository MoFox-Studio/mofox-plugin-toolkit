"""
构建命令实现

将插件目录打包为 .mfp 文件（本质为 ZIP 压缩包）。
loader.py 支持从 .mfp 直接加载插件，与文件夹加载行为一致。

流程：
1. 验证插件目录及 manifest.json
2. 可选地自动升级版本号（major / minor / patch）
3. 收集需打包的文件（排除缓存、版本控制等）
4. 写入 .mfp（ZIP）或 .zip 文件
5. 打印构建摘要
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from mpdt.utils.color_printer import (
    console,
    print_error,
    print_step,
    print_success,
    print_warning,
)
from mpdt.utils.manifest_metadata import ensure_manifest_metadata_interactive, metadata_errors

# 构建时默认排除的文件/目录名称（精确匹配）
_EXCLUDE_NAMES: set[str] = {
    "__pycache__",
    ".git",
    ".gitignore",
    ".gitattributes",
    ".github",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".venv",
    "venv",
    ".env",
    "node_modules",
    "dist",
    ".DS_Store",
    "Thumbs.db",
}

# 排除的文件扩展名
_EXCLUDE_EXTS: set[str] = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".egg-info",
}

# 文档相关目录/文件名
_DOC_NAMES: set[str] = {
    "docs",
    "doc",
    "README.md",
    "README.rst",
    "CHANGELOG.md",
    "CHANGELOG.rst",
}


@dataclass(frozen=True)
class PackageResult:
    """插件打包结果。"""

    plugin_name: str
    plugin_version: str
    author: str
    entry_point: str
    file_count: int
    source_size: int
    package_size: int
    package_path: Path
    sha256: str


def _is_excluded(path: Path, with_docs: bool) -> bool:
    """判断路径是否应被排除。"""
    name = path.name
    if name in _EXCLUDE_NAMES:
        return True
    if path.suffix in _EXCLUDE_EXTS:
        return True
    # 以 . 开头的隐藏文件/目录
    if name.startswith("."):
        return True
    # 文档文件（若不包含文档）
    if not with_docs and name in _DOC_NAMES:
        return True
    return False


def _collect_files(plugin_dir: Path, with_docs: bool) -> list[Path]:
    """递归收集插件目录中需要打包的文件列表（相对路径）。"""
    files: list[Path] = []

    for item in sorted(plugin_dir.rglob("*")):
        # 检查路径上的每个部分是否被排除
        relative = item.relative_to(plugin_dir)
        parts = relative.parts

        excluded = False
        for part in parts:
            part_path = Path(part)
            if _is_excluded(part_path, with_docs):
                excluded = True
                break

        if excluded:
            continue

        if item.is_file():
            files.append(item)

    return files


def _bump_version(version: str, bump: str) -> str:
    """按规则升级版本号（语义化版本 major.minor.patch）。

    Args:
        version: 当前版本字符串，例如 "1.2.3"
        bump: 升级类型，"major" / "minor" / "patch"

    Returns:
        升级后的版本字符串

    Raises:
        ValueError: 版本格式不合法
    """
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(.*)", version.strip())
    if not match:
        raise ValueError(f"版本号格式不合法: '{version}'，应为 major.minor.patch")

    major, minor, patch, suffix = int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4)

    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "patch":
        patch += 1

    return f"{major}.{minor}.{patch}{suffix}"


def _load_manifest(plugin_dir: Path) -> dict | None:
    """读取并解析 manifest.json，返回字典；失败返回 None。"""
    manifest_path = plugin_dir / "manifest.json"
    if not manifest_path.exists():
        print_error(f"manifest.json 不存在: {manifest_path}")
        return None
    try:
        with open(manifest_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_error(f"manifest.json 解析失败: {e}")
        return None


def _save_manifest(plugin_dir: Path, manifest: dict) -> None:
    """将 manifest 字典写回 manifest.json。"""
    manifest_path = plugin_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)


def _validate_manifest_metadata(manifest: dict, plugin_dir: Path) -> None:
    """验证打包所需的 manifest 元数据。"""
    required = ["name", "version", "description", "author", "entry_point"]
    for field in required:
        if field not in manifest:
            raise ValueError(f"manifest.json 缺少必需字段: '{field}'")

    errors = metadata_errors(manifest, plugin_dir)
    if errors:
        raise ValueError(errors[0])


def build_plugin(
    plugin_path: str = ".",
    output_dir: str = "dist",
    with_docs: bool = False,
    fmt: str = "mfp",
    bump: str | None = None,
    verbose: bool = False,
) -> None:
    """构建并打包插件为 .mfp / .zip 文件。

    Args:
        plugin_path: 插件根目录（包含 manifest.json）
        output_dir:  输出目录，默认 dist/
        with_docs:   是否将文档文件打入包中
        fmt:         输出格式，"mfp"（推荐） 或 "zip"
        bump:        自动升级版本，"major" / "minor" / "patch" / None
                     （升级后会立即写回 manifest.json，打包时使用新版本号）
        verbose:     是否显示详细信息
    """
    try:
        result = build_package(
            plugin_path=plugin_path,
            output_dir=output_dir,
            with_docs=with_docs,
            fmt=fmt,
            bump=bump,
            verbose=verbose,
            show_progress=True,
        )
    except ValueError as e:
        print_error(str(e))
        return
    except Exception as e:
        print_error(f"打包失败: {e}")
        return

    if result is None:
        return

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column(style="white")
    table.add_row("插件名称", result.plugin_name)
    table.add_row("版本", result.plugin_version)
    table.add_row("作者", result.author)
    table.add_row("入口文件", result.entry_point)
    table.add_row("打包文件数", str(result.file_count))
    table.add_row("原始大小", _format_size(result.source_size))
    table.add_row("包大小", _format_size(result.package_size))
    table.add_row("SHA256", result.sha256)
    table.add_row("输出路径", str(result.package_path))

    console.print()
    console.print(table)
    console.print()
    print_success(f"构建完成: {result.package_path.name}")


def build_package(
    plugin_path: str = ".",
    output_dir: str = "dist",
    with_docs: bool = False,
    fmt: str = "mfp",
    bump: str | None = None,
    verbose: bool = False,
    show_progress: bool = False,
) -> PackageResult | None:
    """构建插件包并返回可供市场发布使用的元数据。"""

    plugin_dir = Path(plugin_path).resolve()

    # ── 1. 基本验证 ──────────────────────────────────────────────────────────
    if not plugin_dir.exists():
        raise ValueError(f"插件路径不存在: {plugin_dir}")
    if not plugin_dir.is_dir():
        raise ValueError(f"插件路径不是目录: {plugin_dir}")

    if show_progress:
        console.print(Panel.fit(f"📦 构建插件: [cyan]{plugin_dir.name}[/cyan]", border_style="blue"))

    manifest = _load_manifest(plugin_dir)
    if manifest is None:
        return

    manifest = ensure_manifest_metadata_interactive(plugin_dir, manifest)

    _validate_manifest_metadata(manifest, plugin_dir)

    plugin_name: str = manifest["name"]
    plugin_version: str = manifest["version"]

    # ── 2. 版本升级（先写回文件，再使用新版本号进行打包） ────────────────────
    if bump:
        try:
            new_version = _bump_version(plugin_version, bump)
        except ValueError as e:
            raise ValueError(str(e)) from e
        if show_progress:
            print_step(f"版本升级: [yellow]{plugin_version}[/yellow] → [green]{new_version}[/green]")
        manifest["version"] = new_version
        # 立即写回 manifest.json，确保后续打包使用新版本
        _save_manifest(plugin_dir, manifest)        
        plugin_version = new_version

    # ── 3. 验证入口文件 ───────────────────────────────────────────────────────
    entry_point = manifest.get("entry_point", "plugin.py")
    entry_file = plugin_dir / entry_point
    if show_progress and not entry_file.exists():
        print_warning(f"入口文件不存在: {entry_point}（仍将继续构建）")

    # ── 4. 收集文件 ───────────────────────────────────────────────────────────
    if show_progress:
        print_step("收集文件...")
    files = _collect_files(plugin_dir, with_docs)

    if not files:
        if show_progress:
            print_warning("未找到任何需要打包的文件")
        return

    if verbose:
        for f in files:
            rel = f.relative_to(plugin_dir)
            console.print(f"  [dim]+ {rel}[/dim]")

    # ── 5. 确定输出路径 ───────────────────────────────────────────────────────
    # output_dir 可以是绝对路径或相对于插件目录
    out_path = Path(output_dir)
    if not out_path.is_absolute():
        out_path = plugin_dir / output_dir

    out_path.mkdir(parents=True, exist_ok=True)

    suffix = ".mfp" if fmt == "mfp" else ".zip"
    archive_name = f"{plugin_name}-{plugin_version}{suffix}"
    archive_path = out_path / archive_name

    if archive_path.exists():
        print_warning(f"目标文件已存在，将覆盖: {archive_path}")

    # ── 6. 压缩打包 ───────────────────────────────────────────────────────────
    if show_progress:
        print_step(f"正在写入 {suffix} 包...")
    total_bytes = 0

    try:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in files:
                arcname = file_path.relative_to(plugin_dir)
                zf.write(file_path, arcname)
                total_bytes += file_path.stat().st_size
                if verbose:
                    console.print(f"  [dim]  → {arcname}[/dim]")
    except Exception as e:
        # 清理不完整的文件
        if archive_path.exists():
            archive_path.unlink()
        raise RuntimeError(str(e)) from e

    # ── 7. 摘要 ──────────────────────────────────────────────────────────────
    archive_size = archive_path.stat().st_size
    digest = _sha256_file(archive_path)
    return PackageResult(
        plugin_name=plugin_name,
        plugin_version=plugin_version,
        author=str(manifest.get("author", "-")),
        entry_point=str(entry_point),
        file_count=len(files),
        source_size=total_bytes,
        package_size=archive_size,
        package_path=archive_path,
        sha256=digest,
    )


def _sha256_file(path: Path) -> str:
    """计算文件 sha256。"""

    digest = sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _format_size(size: int) -> str:
    """将字节数格式化为人类可读字符串。"""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size //= 1024
    return f"{size:.1f} TB"

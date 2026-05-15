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
import zipfile
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from mpdt.utils.color_printer import (
    console,
    get_fit_panel,
    print_empty_line,
    print_error,
    print_success,
    print_warning,
)
from mpdt.utils.managers.manifest_manager import ManifestManager

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


# _load_manifest 和 _save_manifest 函数已被 ManifestManager 替代，不再需要


def build_plugin(
    plugin_path: str = ".",
    output_dir: str = "dist",
    with_docs: bool = False,
    fmt: str = "mfp",
    bump: str | None = None,
) -> None:
    """构建并打包插件为 .mfp / .zip 文件。

    Args:
        plugin_path: 插件根目录（包含 manifest.json）
        output_dir:  输出目录，默认 dist/
        with_docs:   是否将文档文件打入包中
        fmt:         输出格式，"mfp"（推荐） 或 "zip"
        bump:        自动升级版本，"major" / "minor" / "patch" / None
                     （升级后会立即写回 manifest.json，打包时使用新版本号）
    """
    plugin_dir = Path(plugin_path).resolve()

    # ── 1. 基本验证 ──────────────────────────────────────────────────────────
    if not plugin_dir.exists():
        print_error(f"插件路径不存在: {plugin_dir}")
        return
    if not plugin_dir.is_dir():
        print_error(f"插件路径不是目录: {plugin_dir}")
        return

    # 创建动态面板
    panel = get_fit_panel(f"📦 构建插件: {plugin_dir.name}", border_style="blue")

    with panel:
        panel.update("正在读取 manifest.json...")
        manifest_manager = ManifestManager(plugin_dir)
        manifest = manifest_manager.load()
        if manifest is None:
            print_error(f"manifest.json 不存在或无法解析")
            return

        required = ["name", "version", "description", "author", "entry_point"]
        for field in required:
            if field not in manifest:
                print_error(f"manifest.json 缺少必需字段: '{field}'")
                return

        plugin_name: str = manifest["name"]
        plugin_version: str = manifest["version"]
        panel.append(f"✓ 插件: {plugin_name} v{plugin_version}")

        # ── 2. 版本升级（先写回文件，再使用新版本号进行打包） ────────────────────
        if bump:
            try:
                new_version = _bump_version(plugin_version, bump)
            except ValueError as e:
                print_error(str(e))
                return
            panel.update(f"版本升级: {plugin_version} → {new_version}")
            manifest["version"] = new_version
            # 立即写回 manifest.json，确保后续打包使用新版本
            manifest_manager.save(manifest)
            plugin_version = new_version
            panel.append(f"✓ 版本已更新")

        # ── 3. 验证入口文件 ───────────────────────────────────────────────────────
        entry_point = manifest.get("entry_point", "plugin.py")
        entry_file = plugin_dir / entry_point
        panel.update(f"验证入口文件: {entry_point}")
        if not entry_file.exists():
            print_warning(f"入口文件不存在: {entry_point}（仍将继续构建）")
            panel.append(f"⚠ 入口文件不存在")
        else:
            panel.append(f"✓ 入口文件验证通过")

        # ── 4. 收集文件 ───────────────────────────────────────────────────────────
        panel.update("正在收集文件...")
        files = _collect_files(plugin_dir, with_docs)

        if not files:
            print_warning("未找到任何需要打包的文件")
            return

        panel.append(f"✓ 收集到 {len(files)} 个文件")

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
            panel.append(f"⚠ 将覆盖现有文件")

        # ── 6. 压缩打包 ───────────────────────────────────────────────────────────
        panel.update(f"正在压缩打包为 {suffix}...")
        total_bytes = 0

        try:
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    arcname = file_path.relative_to(plugin_dir)
                    zf.write(file_path, arcname)
                    total_bytes += file_path.stat().st_size
            panel.append(f"✓ 打包完成")
        except Exception as e:
            print_error(f"打包失败: {e}")
            # 清理不完整的文件
            if archive_path.exists():
                archive_path.unlink()
            return

        panel.update("✓ 构建完成")

    # ── 7. 摘要 ──────────────────────────────────────────────────────────────
    archive_size = archive_path.stat().st_size

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column(style="white")
    table.add_row("插件名称", plugin_name)
    table.add_row("版本", plugin_version)
    table.add_row("作者", manifest.get("author", "-"))
    table.add_row("入口文件", entry_point)
    table.add_row("打包文件数", str(len(files)))
    table.add_row("原始大小", _format_size(total_bytes))
    table.add_row("包大小", _format_size(archive_size))
    table.add_row("输出路径", str(archive_path))

    print_empty_line()
    console.print(table)
    print_empty_line()
    print_success(f"构建完成: {archive_path.name}")


def _format_size(size: int) -> str:
    """将字节数格式化为人类可读字符串。"""
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size //= 1024
    return f"{size:.1f} TB"

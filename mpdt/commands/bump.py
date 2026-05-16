"""
版本号管理命令实现

提供插件版本号的升级功能。
支持语义化版本（Semantic Versioning）的三种升级类型：
- major: 主版本号 (1.0.0 -> 2.0.0)
- minor: 次版本号 (1.0.0 -> 1.1.0)
- patch: 修订号 (1.0.0 -> 1.0.1)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from rich.table import Table

from mpdt.utils.color_printer import (
    console,
    get_fit_panel,
    print_empty_line,
    print_error,
    print_success,
)
from mpdt.utils.managers.manifest_manager import ManifestManager


def bump_version(version: str, bump_type: Literal["major", "minor", "patch"]) -> str:
    """按规则升级版本号（语义化版本 major.minor.patch）
    
    Args:
        version: 当前版本字符串，例如 "1.2.3"
        bump_type: 升级类型
        
    Returns:
        升级后的版本字符串
        
    Raises:
        ValueError: 版本格式不合法
    """
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(.*)", version.strip())
    if not match:
        raise ValueError(f"版本号格式不合法: '{version}'，应为 major.minor.patch")
    
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3))
    suffix = match.group(4)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    
    return f"{major}.{minor}.{patch}{suffix}"


def bump_plugin_version(
    plugin_path: str = ".",
    bump_type: Literal["major", "minor", "patch"] = "patch",
) -> tuple[str, str] | None:
    """提升插件版本号
    
    Args:
        plugin_path: 插件根目录（包含 manifest.json）
        bump_type: 版本升级类型 ("major" / "minor" / "patch")
        
    Returns:
        (旧版本, 新版本) 元组，失败返回 None
    """
    plugin_dir = Path(plugin_path).resolve()
    
    # ── 创建动态面板 ──────────────────────────────────────────────────────────
    panel = get_fit_panel(f"📌 版本升级: {plugin_dir.name}", border_style="blue")
    
    with panel:
        try:
            # ── 1. 初始化 manifest 管理器 ────────────────────────────────────────
            panel.update("正在读取 manifest.json...")
            manifest_manager = ManifestManager(plugin_dir)
            
            # ── 2. 加载 manifest ─────────────────────────────────────────────────
            manifest = manifest_manager.load()
            if manifest is None:
                print_error(f"manifest.json 不存在或无法解析")
                return None
            
            plugin_name: str = manifest.get("name", "unknown")
            old_version: str = manifest.get("version", "0.0.0")
            panel.append(f"✓ 当前版本: {old_version}")
            
            # ── 3. 升级版本 ──────────────────────────────────────────────────────
            panel.update("正在升级版本号...")
            new_version = bump_version(old_version, bump_type)
            
            # ── 4. 保存到 manifest ───────────────────────────────────────────────
            panel.update("正在保存 manifest.json...")
            manifest["version"] = new_version
            manifest_manager.save(manifest)
            
            panel.append(f"✓ 新版本: {new_version}")
            panel.update("✓ 版本升级完成")
            
        except ValueError as e:
            print_error(f"验证失败: {e}")
            return None
        except FileNotFoundError as e:
            print_error(f"文件未找到: {e}")
            return None
        except Exception as e:
            print_error(f"未预期的错误: {e}")
            return None
    
    # ── 5. 打印升级摘要 ─────────────────────────────────────────────────────────
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column(style="white")
    table.add_row("插件名称", plugin_name)
    table.add_row("升级类型", bump_type)
    table.add_row("旧版本", old_version)
    table.add_row("新版本", f"[bold green]{new_version}[/bold green]")
    
    print_empty_line()
    console.print(table)
    print_empty_line()
    print_success(f"版本已升级: {old_version} -> {new_version}")
    
    return (old_version, new_version)

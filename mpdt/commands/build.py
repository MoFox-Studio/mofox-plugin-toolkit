"""
构建命令实现

将插件目录打包为 .mfp 文件（本质为 ZIP 压缩包）。
loader.py 支持从 .mfp 直接加载插件，与文件夹加载行为一致。

流程：
1. 验证插件目录及 manifest.json
2. 可选地自动升级版本号（major / minor / patch）
3. 收集需打包的文件（排除缓存、版本控制等）
4. 写入 .mfp（ZIP）或 .zip 文件
5. 计算校验和
6. 打印构建摘要
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from rich.panel import Panel
from rich.table import Table

from mpdt.utils.color_printer import (
    console,
    get_fit_panel,
    print_empty_line,
    print_error,
    print_success,
)
from mpdt.utils.managers.package_manager import PackageManager, PackageResult


def build_plugin(
    plugin_path: str = ".",
    output_dir: str = "dist",
    with_docs: bool = False,
    fmt: Literal["mfp", "zip"] = "mfp",
    bump: Literal["major", "minor", "patch"] | None = None,
) -> PackageResult | None:
    """构建并打包插件为 .mfp / .zip 文件

    Args:
        plugin_path: 插件根目录（包含 manifest.json）
        output_dir:  输出目录，默认 dist/
        with_docs:   是否将文档文件打入包中
        fmt:         输出格式，"mfp"（推荐） 或 "zip"
        bump:        自动升级版本，"major" / "minor" / "patch" / None
                     （升级后会立即写回 manifest.json，打包时使用新版本号）
                     
    Returns:
        PackageResult: 打包结果对象，包含路径、校验和等信息，失败返回 None
    """
    plugin_dir = Path(plugin_path).resolve()

    # ── 创建动态面板 ──────────────────────────────────────────────────────────
    panel = get_fit_panel(f"📦 构建插件: {plugin_dir.name}", border_style="blue")

    with panel:
        try:
            # ── 1. 初始化打包管理器 ─────────────────────────────────────────────
            panel.update("正在初始化打包管理器...")
            package_manager = PackageManager(plugin_dir)
            
            # ── 2. 加载并验证 manifest ──────────────────────────────────────────
            panel.update("正在读取 manifest.json...")
            manifest = package_manager.manifest_manager.load()
            if manifest is None:
                print_error(f"manifest.json 不存在或无法解析")
                return None

            plugin_name: str = manifest.get("name", "unknown")
            plugin_version: str = manifest.get("version", "0.0.0")
            panel.append(f"✓ 插件: {plugin_name} v{plugin_version}")

            # ── 3. 执行打包 ──────────────────────────────────────────────────────
            panel.update("正在构建打包...")
            result = package_manager.build_package(
                output_dir=output_dir,
                with_docs=with_docs,
                fmt=fmt,
                bump=bump,
            )
            
            panel.append(f"✓ 打包完成: {result.package_name}")
            panel.update("✓ 构建完成")

        except ValueError as e:
            print_error(f"验证失败: {e}")
            return None
        except FileNotFoundError as e:
            print_error(f"文件未找到: {e}")
            return None
        except OSError as e:
            print_error(f"打包失败: {e}")
            return None
        except Exception as e:
            print_error(f"未预期的错误: {e}")
            return None

    # ── 4. 打印构建摘要 ─────────────────────────────────────────────────────────
    manifest = package_manager.manifest_manager.load()
    entry_point = manifest.get("entry_point", "plugin.py") if manifest else "unknown"
    author = manifest.get("author", "-") if manifest else "-"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="cyan")
    table.add_column(style="white")
    table.add_row("插件名称", result.plugin_name)
    table.add_row("版本", result.version)
    table.add_row("作者", author)
    table.add_row("入口文件", entry_point)
    table.add_row("打包文件数", str(result.file_count))
    table.add_row("原始大小", result.format_size(result.original_size))
    table.add_row("包大小", result.format_size())
    table.add_row("SHA256", result.sha256[:16] + "...")
    table.add_row("输出路径", str(result.package_path))

    print_empty_line()
    console.print(table)
    print_empty_line()
    print_success(f"构建完成: {result.package_name}")
    
    return result

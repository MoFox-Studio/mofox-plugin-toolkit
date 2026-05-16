"""
插件打包管理器
统一管理插件打包的所有操作
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from mpdt.utils.color_printer import print_warning
from mpdt.utils.managers.manifest_manager import ManifestManager


@dataclass
class PackageResult:
    """打包结果数据类
    
    Attributes:
        package_path: 打包文件的完整路径
        plugin_name: 插件名称
        version: 插件版本
        file_count: 打包的文件数量
        original_size: 原始文件总大小（字节）
        package_size: 打包后的大小（字节）
        sha256: 打包文件的 SHA256 校验和
        format: 打包格式（mfp 或 zip）
    """
    
    package_path: Path
    plugin_name: str
    version: str
    file_count: int
    original_size: int
    package_size: int
    sha256: str
    format: Literal["mfp", "zip"]
    
    @property
    def package_name(self) -> str:
        """获取打包文件名"""
        return self.package_path.name
    
    def format_size(self, size: int | None = None) -> str:
        """格式化大小为人类可读字符串
        
        Args:
            size: 要格式化的字节数，默认为 package_size
            
        Returns:
            格式化后的字符串，如 "1.2 MB"
        """
        if size is None:
            size = self.package_size
            
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size //= 1024
        return f"{size:.1f} TB"


class PackageManager:
    """插件打包管理器
    
    提供插件打包的所有操作，包括：
    - 文件收集
    - 版本升级
    - ZIP 打包
    - 校验和计算
    """
    
    # 构建时默认排除的文件/目录名称（精确匹配）
    EXCLUDE_NAMES: set[str] = {
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
    EXCLUDE_EXTS: set[str] = {
        ".pyc",
        ".pyo",
        ".pyd",
        ".egg-info",
    }
    
    # 文档相关目录/文件名
    DOC_NAMES: set[str] = {
        "docs",
        "doc",
        "README.md",
        "README.rst",
        "CHANGELOG.md",
        "CHANGELOG.rst",
    }
    
    def __init__(self, plugin_path: Path | str):
        """初始化打包管理器
        
        Args:
            plugin_path: 插件目录路径
        """
        self.plugin_path = Path(plugin_path).resolve()
        self.manifest_manager = ManifestManager(self.plugin_path)
    
    def is_excluded(self, path: Path, with_docs: bool = False) -> bool:
        """判断路径是否应被排除
        
        Args:
            path: 要检查的路径
            with_docs: 是否包含文档文件
            
        Returns:
            是否应排除该路径
        """
        name = path.name
        
        # 排除的目录/文件名
        if name in self.EXCLUDE_NAMES:
            return True
        
        # 排除的扩展名
        if path.suffix in self.EXCLUDE_EXTS:
            return True
        
        # 隐藏文件/目录
        if name.startswith("."):
            return True
        
        # 文档文件（如果不包含文档）
        if not with_docs and name in self.DOC_NAMES:
            return True
        
        return False
    
    def collect_files(self, with_docs: bool = False) -> list[Path]:
        """递归收集插件目录中需要打包的文件列表
        
        Args:
            with_docs: 是否包含文档文件
            
        Returns:
            文件路径列表（绝对路径）
        """
        files: list[Path] = []
        
        for item in sorted(self.plugin_path.rglob("*")):
            # 检查路径上的每个部分是否被排除
            relative = item.relative_to(self.plugin_path)
            parts = relative.parts
            
            excluded = False
            for part in parts:
                part_path = Path(part)
                if self.is_excluded(part_path, with_docs):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            if item.is_file():
                files.append(item)
        
        return files
    
    def bump_version(self, version: str, bump: Literal["major", "minor", "patch"]) -> str:
        """按规则升级版本号（语义化版本 major.minor.patch）
        
        Args:
            version: 当前版本字符串，例如 "1.2.3"
            bump: 升级类型
            
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
    
    def calculate_sha256(self, file_path: Path) -> str:
        """计算文件的 SHA256 校验和
        
        Args:
            file_path: 文件路径
            
        Returns:
            SHA256 十六进制字符串
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def build_package(
        self,
        output_dir: Path | str = "dist",
        with_docs: bool = False,
        fmt: Literal["mfp", "zip"] = "mfp",
        bump: Literal["major", "minor", "patch"] | None = None,
    ) -> PackageResult:
        """构建插件打包
        
        Args:
            output_dir: 输出目录
            with_docs: 是否包含文档文件
            fmt: 输出格式（mfp 或 zip）
            bump: 版本升级类型（可选）
            
        Returns:
            PackageResult: 打包结果
            
        Raises:
            ValueError: manifest 验证失败或版本格式错误
            FileNotFoundError: 插件目录不存在
            OSError: 打包操作失败
        """
        # 验证插件目录
        if not self.plugin_path.exists():
            raise FileNotFoundError(f"插件路径不存在: {self.plugin_path}")
        
        if not self.plugin_path.is_dir():
            raise ValueError(f"插件路径不是目录: {self.plugin_path}")
        
        # 加载 manifest
        manifest = self.manifest_manager.load()
        if manifest is None:
            raise ValueError(f"manifest.json 不存在或无法解析")
        
        # 验证必需字段
        required = ["name", "version", "description", "author", "entry_point"]
        for field in required:
            if field not in manifest:
                raise ValueError(f"manifest.json 缺少必需字段: '{field}'")
        
        plugin_name: str = manifest["name"]
        plugin_version: str = manifest["version"]
        
        # 版本升级（如果指定）
        if bump:
            plugin_version = self.bump_version(plugin_version, bump)
            manifest["version"] = plugin_version
            self.manifest_manager.save(manifest)
        
        # 验证入口文件
        entry_point = manifest.get("entry_point", "plugin.py")
        entry_file = self.plugin_path / entry_point
        if not entry_file.exists():
            print_warning(f"入口文件不存在: {entry_point}（仍将继续构建）")
        
        # 收集文件
        files = self.collect_files(with_docs)
        if not files:
            raise ValueError("未找到任何需要打包的文件")
        
        # 确定输出路径
        out_path = Path(output_dir)
        if not out_path.is_absolute():
            out_path = self.plugin_path / output_dir
        
        out_path.mkdir(parents=True, exist_ok=True)
        
        suffix = ".mfp" if fmt == "mfp" else ".zip"
        archive_name = f"{plugin_name}-{plugin_version}{suffix}"
        archive_path = out_path / archive_name
        
        if archive_path.exists():
            print_warning(f"目标文件已存在，将覆盖: {archive_path}")
        
        # 打包
        total_bytes = 0
        try:
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for file_path in files:
                    arcname = file_path.relative_to(self.plugin_path)
                    zf.write(file_path, arcname)
                    total_bytes += file_path.stat().st_size
        except Exception as e:
            # 清理不完整的文件
            if archive_path.exists():
                archive_path.unlink()
            raise OSError(f"打包失败: {e}") from e
        
        # 计算校验和
        sha256 = self.calculate_sha256(archive_path)
        package_size = archive_path.stat().st_size
        
        # 返回结果
        return PackageResult(
            package_path=archive_path,
            plugin_name=plugin_name,
            version=plugin_version,
            file_count=len(files),
            original_size=total_bytes,
            package_size=package_size,
            sha256=sha256,
            format=fmt,
        )

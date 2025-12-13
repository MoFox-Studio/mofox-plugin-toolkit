"""
文件操作工具
"""

import shutil
from pathlib import Path
from typing import List


def ensure_dir(path: Path | str) -> Path:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        Path 对象
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_write_file(path: Path | str, content: str, force: bool = False) -> bool:
    """
    安全地写入文件
    
    Args:
        path: 文件路径
        content: 文件内容
        force: 是否覆盖已存在的文件
        
    Returns:
        是否写入成功
        
    Raises:
        FileExistsError: 文件已存在且 force=False
    """
    path = Path(path)
    
    if path.exists() and not force:
        raise FileExistsError(f"文件已存在: {path}")
    
    # 确保父目录存在
    ensure_dir(path.parent)
    
    # 写入文件
    path.write_text(content, encoding="utf-8")
    return True


def copy_directory(src: Path | str, dst: Path | str, force: bool = False) -> bool:
    """
    复制整个目录
    
    Args:
        src: 源目录
        dst: 目标目录
        force: 是否覆盖已存在的目录
        
    Returns:
        是否复制成功
    """
    src = Path(src)
    dst = Path(dst)
    
    if dst.exists() and not force:
        raise FileExistsError(f"目标目录已存在: {dst}")
    
    if dst.exists():
        shutil.rmtree(dst)
    
    shutil.copytree(src, dst)
    return True


def list_python_files(path: Path | str, recursive: bool = True) -> List[Path]:
    """
    列出目录中的所有 Python 文件
    
    Args:
        path: 目录路径
        recursive: 是否递归搜索
        
    Returns:
        Python 文件路径列表
    """
    path = Path(path)
    
    if recursive:
        return list(path.rglob("*.py"))
    else:
        return list(path.glob("*.py"))


def validate_plugin_name(name: str) -> bool:
    """
    验证插件名称是否符合规范
    
    规范: 使用小写字母、数字和下划线，以字母开头
    
    Args:
        name: 插件名称
        
    Returns:
        是否符合规范
    """
    import re
    return bool(re.match(r"^[a-z][a-z0-9_]*$", name))


def validate_component_name(name: str) -> bool:
    """
    验证组件名称是否符合规范
    
    规范: 使用 PascalCase（首字母大写的驼峰命名）
    
    Args:
        name: 组件名称
        
    Returns:
        是否符合规范
    """
    import re
    return bool(re.match(r"^[A-Z][a-zA-Z0-9]*$", name))


def get_git_user_info() -> dict[str, str]:
    """
    从 git config 获取用户信息
    
    Returns:
        包含 name 和 email 的字典
    """
    import subprocess
    
    result = {"name": "", "email": ""}
    
    try:
        name = subprocess.run(
            ["git", "config", "--get", "user.name"],
            capture_output=True,
            text=True,
            check=False,
        )
        if name.returncode == 0:
            result["name"] = name.stdout.strip()
        
        email = subprocess.run(
            ["git", "config", "--get", "user.email"],
            capture_output=True,
            text=True,
            check=False,
        )
        if email.returncode == 0:
            result["email"] = email.stdout.strip()
    except Exception:
        pass
    
    return result

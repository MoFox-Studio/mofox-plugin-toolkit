"""
文件操作工具
"""

import shutil
from pathlib import Path


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


def list_python_files(path: Path | str, recursive: bool = True) -> list[Path]:
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
    
    规范: 支持 snake_case 或 PascalCase
    
    Args:
        name: 组件名称
        
    Returns:
        是否符合规范
    """
    import re
    # 支持 snake_case 或 PascalCase
    return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name))


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


def to_pascal_case(snake_str: str) -> str:
    """
    将 snake_case 转换为 PascalCase

    Args:
        snake_str: snake_case 字符串

    Returns:
        PascalCase 字符串

    Examples:
        >>> to_pascal_case("my_action")
        'MyAction'
        >>> to_pascal_case("test_command_handler")
        'TestCommandHandler'
    """
    return "".join(word.capitalize() for word in snake_str.split("_"))


def to_snake_case(pascal_str: str) -> str:
    """
    将 PascalCase 转换为 snake_case

    Args:
        pascal_str: PascalCase 字符串

    Returns:
        snake_case 字符串

    Examples:
        >>> to_snake_case("MyAction")
        'my_action'
        >>> to_snake_case("TestCommandHandler")
        'test_command_handler'
    """
    import re
    # 在大写字母前插入下划线
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', pascal_str)
    # 处理连续大写字母
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

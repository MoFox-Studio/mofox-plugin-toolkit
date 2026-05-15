"""
Git 管理器
统一管理 Git 相关操作
"""

import subprocess
from pathlib import Path
from typing import Any


class GitManager:
    """Git 统一管理器

    提供所有 Git 相关操作，包括：
    - 获取 Git 用户信息
    - 初始化 Git 仓库
    - Git 常用命令封装
    """

    def __init__(self, work_dir: Path | str | None = None):
        """初始化 Git 管理器

        Args:
            work_dir: 工作目录，默认为当前目录
        """
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()

    @staticmethod
    def get_user_info() -> dict[str, str]:
        """从 git config 获取用户信息

        Returns:
            包含 name 和 email 的字典
        """
        result = {"name": "", "email": ""}

        try:
            name = subprocess.run(
                ["git", "config", "--get", "user.name"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="ignore",
            )
            if name.returncode == 0:
                result["name"] = name.stdout.strip()

            email = subprocess.run(
                ["git", "config", "--get", "user.email"],
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
                errors="ignore",
            )
            if email.returncode == 0:
                result["email"] = email.stdout.strip()
        except Exception:
            pass

        return result

    @staticmethod
    def is_git_available() -> bool:
        """检查 Git 是否可用

        Returns:
            Git 是否可用
        """
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def is_git_repo(self) -> bool:
        """检查当前目录是否是 Git 仓库

        Returns:
            是否是 Git 仓库
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.work_dir,
                capture_output=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def init_repository(
        self, create_gitignore: bool = True, initial_commit: bool = True
    ) -> tuple[bool, str]:
        """初始化 Git 仓库

        Args:
            create_gitignore: 是否创建 .gitignore 文件
            initial_commit: 是否执行初始提交

        Returns:
            (是否成功, 消息)
        """
        if not self.is_git_available():
            return False, "未找到 Git 命令，请确保已安装 Git"

        try:
            # 初始化 Git 仓库
            subprocess.run(
                ["git", "init"],
                cwd=self.work_dir,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )

            # 创建 .gitignore 文件
            if create_gitignore:
                self._create_default_gitignore()

            # 执行初始提交
            if initial_commit:
                success, msg = self.commit("Initial commit", add_all=True)
                if not success:
                    return False, f"初始提交失败: {msg}"

            return True, "Git 仓库初始化成功"

        except subprocess.CalledProcessError as e:
            return False, f"Git 初始化失败: {e}"
        except Exception as e:
            return False, f"Git 初始化异常: {e}"

    def add(self, paths: list[str] | str | None = None) -> tuple[bool, str]:
        """添加文件到暂存区

        Args:
            paths: 要添加的文件路径列表，为 None 时添加所有文件

        Returns:
            (是否成功, 消息)
        """
        try:
            if paths is None:
                cmd = ["git", "add", "."]
            elif isinstance(paths, str):
                cmd = ["git", "add", paths]
            else:
                cmd = ["git", "add"] + paths

            subprocess.run(
                cmd,
                cwd=self.work_dir,
                check=True,
                capture_output=True,
                encoding="utf-8",
                errors="ignore",
            )
            return True, "文件添加成功"
        except subprocess.CalledProcessError as e:
            return False, f"添加文件失败: {e}"

    def commit(
        self, message: str, add_all: bool = False
    ) -> tuple[bool, str]:
        """提交更改

        Args:
            message: 提交消息
            add_all: 是否先添加所有文件

        Returns:
            (是否成功, 消息)
        """
        try:
            if add_all:
                success, msg = self.add()
                if not success:
                    return False, f"添加文件失败: {msg}"

            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.work_dir,
                check=True,
                capture_output=True,
                encoding="utf-8",
                errors="ignore",
            )
            return True, "提交成功"
        except subprocess.CalledProcessError as e:
            return False, f"提交失败: {e}"

    def get_current_branch(self) -> str | None:
        """获取当前分支名

        Returns:
            分支名，失败返回 None
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="ignore",
            )
            return result.stdout.strip()
        except Exception:
            return None

    def get_status(self) -> tuple[bool, str]:
        """获取 Git 状态

        Returns:
            (是否成功, 状态信息)
        """
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="ignore",
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"获取状态失败: {e}"

    def has_uncommitted_changes(self) -> bool:
        """检查是否有未提交的更改

        Returns:
            是否有未提交的更改
        """
        success, status = self.get_status()
        if not success:
            return False
        return bool(status.strip())

    def create_tag(self, tag_name: str, message: str | None = None) -> tuple[bool, str]:
        """创建 Git 标签

        Args:
            tag_name: 标签名称
            message: 标签消息

        Returns:
            (是否成功, 消息)
        """
        try:
            if message:
                cmd = ["git", "tag", "-a", tag_name, "-m", message]
            else:
                cmd = ["git", "tag", tag_name]

            subprocess.run(
                cmd,
                cwd=self.work_dir,
                check=True,
                capture_output=True,
                encoding="utf-8",
                errors="ignore",
            )
            return True, f"标签 {tag_name} 创建成功"
        except subprocess.CalledProcessError as e:
            return False, f"创建标签失败: {e}"

    def get_remote_url(self, remote: str = "origin") -> str | None:
        """获取远程仓库 URL

        Args:
            remote: 远程仓库名称

        Returns:
            远程仓库 URL，失败返回 None
        """
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="ignore",
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _create_default_gitignore(self) -> None:
        """创建默认的 .gitignore 文件"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
.pytest_cache/
.coverage
htmlcov/

# MoFox-Bot specific
config/local_*.toml
*.log
"""
        gitignore_path = self.work_dir / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding="utf-8")

    @classmethod
    def from_path(cls, path: Path | str) -> "GitManager":
        """从路径创建 GitManager

        Args:
            path: 工作目录路径

        Returns:
            GitManager 实例
        """
        return cls(path)

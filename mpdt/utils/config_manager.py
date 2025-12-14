"""
MPDT 配置管理器
管理 mmc 路径、虚拟环境等配置信息
"""

import os
from pathlib import Path
from typing import Literal

try:
    import tomli
    import tomli_w
except ImportError:
    # 如果没有安装 tomli，使用 toml
    try:
        import toml as tomli
        import toml as tomli_w
    except ImportError:
        tomli = None
        tomli_w = None

VenvType = Literal["venv", "uv", "conda", "poetry", "none"]


class MPDTConfig:
    """MPDT 配置管理器"""

    def __init__(self, config_path: Path | None = None):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 ~/.mpdt/config.toml
        """
        if config_path is None:
            config_path = Path.home() / ".mpdt" / "config.toml"

        self.config_path = config_path
        self._config: dict = {}

        # 加载配置
        if self.config_path.exists():
            self.load()

    def load(self) -> None:
        """加载配置文件"""
        if not self.config_path.exists():
            self._config = {}
            return

        if tomli is None:
            raise ImportError("需要安装 tomli 库来读取配置文件")

        with open(self.config_path, "rb") as f:
            self._config = tomli.load(f)

    def save(self) -> None:
        """保存配置文件"""
        if tomli_w is None:
            raise ImportError("需要安装 tomli-w 库来写入配置文件")

        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "wb") as f:
            tomli_w.dump(self._config, f)

    @property
    def mmc_path(self) -> Path | None:
        """获取 mmc 主程序路径"""
        path_str = self._config.get("mmc", {}).get("path")
        return Path(path_str) if path_str else None

    @mmc_path.setter
    def mmc_path(self, path: Path | str) -> None:
        """设置 mmc 主程序路径"""
        if "mmc" not in self._config:
            self._config["mmc"] = {}
        self._config["mmc"]["path"] = str(Path(path).absolute())

    @property
    def venv_path(self) -> Path | None:
        """获取虚拟环境路径"""
        path_str = self._config.get("mmc", {}).get("venv_path")
        return Path(path_str) if path_str else None

    @venv_path.setter
    def venv_path(self, path: Path | str | None) -> None:
        """设置虚拟环境路径"""
        if "mmc" not in self._config:
            self._config["mmc"] = {}
        if path is None:
            self._config["mmc"]["venv_path"] = None
        else:
            self._config["mmc"]["venv_path"] = str(Path(path).absolute())

    @property
    def venv_type(self) -> VenvType:
        """获取虚拟环境类型"""
        return self._config.get("mmc", {}).get("venv_type", "venv")

    @venv_type.setter
    def venv_type(self, venv_type: VenvType) -> None:
        """设置虚拟环境类型"""
        if "mmc" not in self._config:
            self._config["mmc"] = {}
        self._config["mmc"]["venv_type"] = venv_type

    @property
    def auto_reload(self) -> bool:
        """是否自动重载"""
        return self._config.get("dev", {}).get("auto_reload", True)

    @auto_reload.setter
    def auto_reload(self, value: bool) -> None:
        """设置是否自动重载"""
        if "dev" not in self._config:
            self._config["dev"] = {}
        self._config["dev"]["auto_reload"] = value

    @property
    def reload_delay(self) -> float:
        """重载延迟（秒）"""
        return self._config.get("dev", {}).get("reload_delay", 0.3)

    @reload_delay.setter
    def reload_delay(self, value: float) -> None:
        """设置重载延迟"""
        if "dev" not in self._config:
            self._config["dev"] = {}
        self._config["dev"]["reload_delay"] = value

    def get_python_command(self) -> list[str]:
        """获取 Python 启动命令
        
        Returns:
            Python 命令列表，例如:
            - ["E:/venv/Scripts/python.exe"]
            - ["conda", "run", "-p", "E:/conda_env", "python"]
            - ["poetry", "run", "python"]
        """
        venv_type = self.venv_type
        venv_path = self.venv_path

        if venv_type == "none" or not venv_path:
            return ["python"]

        if venv_type == "venv" or venv_type == "uv":
            # venv 和 uv 使用相同的结构
            if os.name == "nt":  # Windows
                python_exe = venv_path / "Scripts" / "python.exe"
            else:  # Unix-like
                python_exe = venv_path / "bin" / "python"

            if python_exe.exists():
                return [str(python_exe)]
            else:
                # 降级到系统 Python
                return ["python"]

        elif venv_type == "conda":
            return ["conda", "run", "-p", str(venv_path), "python"]

        elif venv_type == "poetry":
            # poetry 需要在 mmc 目录中执行
            return ["poetry", "run", "python"]

        else:
            return ["python"]

    def validate(self) -> tuple[bool, list[str]]:
        """验证配置
        
        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        # 检查 mmc 路径
        if not self.mmc_path:
            errors.append("未配置 mmc 主程序路径")
        elif not self.mmc_path.exists():
            errors.append(f"mmc 路径不存在: {self.mmc_path}")
        else:
            # 检查是否有 bot.py
            bot_file = self.mmc_path / "bot.py"
            if not bot_file.exists():
                errors.append(f"未找到 bot.py: {bot_file}")

        # 检查虚拟环境
        if self.venv_type != "none" and self.venv_path:
            if not self.venv_path.exists():
                errors.append(f"虚拟环境路径不存在: {self.venv_path}")
            else:
                # 检查 Python 可执行文件
                python_cmd = self.get_python_command()
                if self.venv_type in ["venv", "uv"]:
                    python_path = Path(python_cmd[0])
                    if not python_path.exists():
                        errors.append(f"Python 可执行文件不存在: {python_path}")

        return len(errors) == 0, errors

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.mmc_path is not None


def get_default_config() -> MPDTConfig:
    """获取默认配置实例"""
    return MPDTConfig()


def interactive_config() -> MPDTConfig:
    """交互式配置向导
    
    Returns:
        配置好的 MPDTConfig 实例
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt

    console = Console()
    config = MPDTConfig()

    console.print(Panel.fit(
        "[bold cyan]MPDT 配置向导[/bold cyan]\n\n"
        "让我们配置 MoFox 主程序的路径和虚拟环境"
    ))

    # 配置 mmc 路径
    while True:
        mmc_path_str = Prompt.ask(
            "\n[bold]请输入 mmc 主程序路径[/bold]",
            default=str(Path.cwd().parent / "mmc") if Path.cwd().parent.name != "mmc" else str(Path.cwd())
        )
        mmc_path = Path(mmc_path_str).expanduser().absolute()

        if not mmc_path.exists():
            console.print(f"[red]路径不存在: {mmc_path}[/red]")
            if not Confirm.ask("重新输入?", default=True):
                break
            continue

        bot_file = mmc_path / "bot.py"
        if not bot_file.exists():
            console.print("[yellow]警告: 未找到 bot.py[/yellow]")
            if not Confirm.ask("仍然使用此路径?", default=False):
                continue

        config.mmc_path = mmc_path
        console.print(f"[green]✓ mmc 路径已设置: {mmc_path}[/green]")
        break

    # 配置虚拟环境
    console.print("\n[bold]虚拟环境配置[/bold]")
    venv_type_choice = Prompt.ask(
        "请选择虚拟环境类型",
        choices=["venv", "uv", "conda", "poetry", "none"],
        default="venv"
    )
    config.venv_type = venv_type_choice

    if venv_type_choice != "none":
        if venv_type_choice == "poetry":
            console.print("[cyan]使用 poetry，将在 mmc 目录中执行命令[/cyan]")
            config.venv_path = config.mmc_path
        else:
            default_venv_path = str(config.mmc_path.parent / "venv")
            if venv_type_choice == "uv":
                default_venv_path = str(config.mmc_path.parent / ".venv")
            elif venv_type_choice == "conda":
                default_venv_path = str(config.mmc_path.parent / "conda_env")

            venv_path_str = Prompt.ask(
                f"请输入 {venv_type_choice} 虚拟环境路径",
                default=default_venv_path
            )
            venv_path = Path(venv_path_str).expanduser().absolute()

            if not venv_path.exists():
                console.print(f"[yellow]警告: 虚拟环境路径不存在: {venv_path}[/yellow]")
                if not Confirm.ask("仍然使用此路径?", default=True):
                    config.venv_type = "none"
                else:
                    config.venv_path = venv_path
            else:
                config.venv_path = venv_path
                console.print(f"[green]✓ 虚拟环境路径已设置: {venv_path}[/green]")
    else:
        console.print("[cyan]将使用系统 Python[/cyan]")

    # 保存配置
    config.save()
    console.print(f"\n[bold green]✓ 配置已保存: {config.config_path}[/bold green]")

    return config

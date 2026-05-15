"""
MPDT 配置管理器
管理 mofox 路径、虚拟环境等配置信息
"""

from pathlib import Path

import tomli
import tomli_w


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

        with open(self.config_path, "rb") as f:
            self._config = tomli.load(f)

    def save(self) -> None:
        """保存配置文件"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "wb") as f:
            tomli_w.dump(self._config, f)

    @property
    def mofox_path(self) -> Path | None:
        """获取 mofox 主程序路径"""
        path_str = self._config.get("mofox", {}).get("path")
        return Path(path_str) if path_str else None

    @mofox_path.setter
    def mofox_path(self, path: Path | str) -> None:
        """设置 mofox 主程序路径"""
        if "mofox" not in self._config:
            self._config["mofox"] = {}
        self._config["mofox"]["path"] = str(Path(path).absolute())

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
            Python 命令列表，使用 uv run
        """
        return ["uv", "run"]

    def validate(self) -> tuple[bool, list[str]]:
        """验证配置

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        if not self.mofox_path:
            errors.append("未配置 Neo-MoFox 主程序路径")

        return len(errors) == 0, errors

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.mofox_path is not None


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

    console.print(Panel.fit("[bold cyan]MPDT 配置向导[/bold cyan]\n\n让我们配置 Neo-MoFox 主程序的路径"))

    # 配置 Neo-MoFox 路径
    mofox_path_str = Prompt.ask(
        "\n[bold]请输入 Neo-MoFox 主程序路径[/bold]",
        default=str(Path.cwd().parent / "Neo-MoFox") if Path.cwd().parent.name != "Neo-MoFox" else str(Path.cwd()),
    )
    mofox_path = Path(mofox_path_str).expanduser().absolute()

    config.mofox_path = mofox_path
    console.print(f"[green]✓ Neo-MoFox 路径已设置: {mofox_path}[/green]")

    # 保存配置
    config.save()
    console.print(f"\n[bold green]✓ 配置已保存: {config.config_path}[/bold green]")

    return config

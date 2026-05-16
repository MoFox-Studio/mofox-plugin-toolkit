"""
MPDT 配置管理器
管理 mofox 路径、虚拟环境等配置信息
"""

from pathlib import Path

import tomli
import tomli_w

# 全局单例实例
_global_config: "MPDTConfig | None" = None

# 默认市场 URL
DEFAULT_MARKET_URL = "http://39.96.71.162/"


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

    @property
    def github_token(self) -> str | None:
        """获取 GitHub Token"""
        token = self._config.get("github", {}).get("token")
        return str(token) if token else None

    @github_token.setter
    def github_token(self, token: str) -> None:
        """设置 GitHub Token"""
        if "github" not in self._config:
            self._config["github"] = {}
        self._config["github"]["token"] = token

    def clear_github_token(self) -> None:
        """清除 GitHub Token"""
        if "github" in self._config:
            self._config["github"].pop("token", None)
            if not self._config["github"]:
                self._config.pop("github")

    @property
    def market_url(self) -> str:
        """获取市场 URL"""
        url = self._config.get("market", {}).get("url")
        if url:
            return str(url).rstrip("/")
        return DEFAULT_MARKET_URL.rstrip("/")

    @market_url.setter
    def market_url(self, url: str) -> None:
        """设置市场 URL"""
        if "market" not in self._config:
            self._config["market"] = {}
        self._config["market"]["url"] = url.rstrip("/")

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


def get_or_init_mpdt_config() -> MPDTConfig:
    """获取或初始化全局配置实例（单例模式）
    
    Returns:
        全局配置实例
    """
    global _global_config
    if _global_config is None:
        _global_config = MPDTConfig()
    return _global_config



def interactive_config() -> MPDTConfig:
    """交互式配置向导

    Returns:
        配置好的 MPDTConfig 实例
    """
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt

    from mpdt.utils.color_printer import console, print_fit_panel, print_success

    config = MPDTConfig()

    print_fit_panel("MPDT 配置向导\n\n让我们配置 Neo-MoFox 主程序的路径和 GitHub Token", "", rgb=(0, 255, 255))

    # 配置 Neo-MoFox 路径
    mofox_path_str = Prompt.ask(
        "\n[bold]请输入 Neo-MoFox 主程序路径[/bold]",
        default=str(Path.cwd().parent / "Neo-MoFox") if Path.cwd().parent.name != "Neo-MoFox" else str(Path.cwd()),
    )
    mofox_path = Path(mofox_path_str).expanduser().absolute()

    config.mofox_path = mofox_path
    print_success(f"Neo-MoFox 路径已设置: {mofox_path}")

    # 配置 GitHub Token（可选）
    console.print("\n[cyan]GitHub Token 用于插件市场发布功能[/cyan]")
    console.print("[dim]如果暂不需要发布插件到市场，可以跳过此步骤[/dim]")
    
    need_github_token = Confirm.ask("\n是否配置 GitHub Token？", default=False)
    if need_github_token:
        github_token = Prompt.ask(
            "[bold]请输入 GitHub Personal Access Token[/bold]",
            password=True
        )
        if github_token and github_token.strip():
            config.github_token = github_token.strip()
            print_success("GitHub Token 已保存")
        else:
            console.print("[yellow]未设置 GitHub Token，稍后可使用 'mpdt config set-github-token' 命令设置[/yellow]")

    # 保存配置
    config.save()
    print_success(f"\n配置已保存: {config.config_path}")

    return config

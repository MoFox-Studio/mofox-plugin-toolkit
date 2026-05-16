"""
MPDT 配置管理器
管理 mofox 路径、虚拟环境等配置信息
"""

from pathlib import Path
from typing import Any

import tomli
import tomli_w

# 全局单例实例
_global_config: "MPDTConfig | None" = None

# 默认市场 URL
DEFAULT_MARKET_URL = "http://39.96.71.162/"

# 默认 PyPI 源
DEFAULT_PYPI_INDEX_URL = "https://pypi.org"


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
    def editor_command(self) -> str | None:
        """获取编辑器命令"""
        editor_command = self._config.get("editor", {}).get("command")
        return str(editor_command) if editor_command else None

    @editor_command.setter
    def editor_command(self, value: str) -> None:
        """设置编辑器命令"""
        if "editor" not in self._config:
            self._config["editor"] = {}
        self._config["editor"]["command"] = value

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

    @property
    def pypi_index_url(self) -> str:
        """获取 PyPI 索引 URL（镜像源）"""
        url = self._config.get("pypi", {}).get("index_url")
        if url:
            return str(url).rstrip("/")
        return DEFAULT_PYPI_INDEX_URL.rstrip("/")

    @pypi_index_url.setter
    def pypi_index_url(self, url: str) -> None:
        """设置 PyPI 索引 URL（镜像源）"""
        if "pypi" not in self._config:
            self._config["pypi"] = {}
        self._config["pypi"]["index_url"] = url.rstrip("/")

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

    def get_config(self, key: str) -> str | None:
        """获取配置值（支持点号分隔的键）
        
        Args:
            key: 配置键，如 "mofox.path" 或 "github.token"
            
        Returns:
            配置值，如果不存在返回 None
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None
                
        return str(value) if value is not None else None

    def set_config(self, key: str, value: str) -> None:
        """设置配置值（支持点号分隔的键）
        
        Args:
            key: 配置键，如 "mofox.path" 或 "github.token"
            value: 配置值
        """
        keys = key.split(".")
        
        # 特殊处理某些配置项
        actual_value: Any = value
        if key == "mofox.path":
            # 展开路径并转换为绝对路径
            actual_value = str(Path(value).expanduser().absolute())
        elif key in ["market.url", "pypi.index_url"]:
            # 移除尾部斜杠
            actual_value = value.rstrip("/")
        elif key == "dev.auto_reload":
            # 转换布尔值
            actual_value = value.lower() in ("true", "yes", "1", "on")
        elif key == "dev.reload_delay":
            # 转换为浮点数
            try:
                actual_value = float(value)
            except ValueError:
                raise ValueError(f"reload_delay 必须是数字，得到: {value}")
        
        # 逐层创建字典并设置值
        current = self._config
        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                raise ValueError(f"配置键 '{'.'.join(keys[:i+1])}' 已存在且不是字典")
            current = current[k]
        
        current[keys[-1]] = actual_value

    def unset_config(self, key: str) -> bool:
        """删除配置值（支持点号分隔的键）
        
        Args:
            key: 配置键，如 "github.token"
            
        Returns:
            是否成功删除
        """
        keys = key.split(".")
        current = self._config
        
        # 导航到父字典
        for k in keys[:-1]:
            if not isinstance(current, dict) or k not in current:
                return False
            current = current[k]
        
        # 删除最后一个键
        if isinstance(current, dict) and keys[-1] in current:
            del current[keys[-1]]
            
            # 清理空的父字典
            self._cleanup_empty_dicts()
            return True
        
        return False

    def _cleanup_empty_dicts(self) -> None:
        """清理配置中的空字典"""
        def clean(d: dict) -> dict:
            return {
                k: clean(v) if isinstance(v, dict) else v
                for k, v in d.items()
                if not (isinstance(v, dict) and not v)
            }
        
        self._config = clean(self._config)

    def list_all_configs(self) -> dict[str, str]:
        """列出所有配置项（扁平化）
        
        Returns:
            配置键值对字典
        """
        def flatten(d: dict, prefix: str = "") -> dict[str, str]:
            result = {}
            for k, v in d.items():
                key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    result.update(flatten(v, key))
                else:
                    result[key] = str(v)
            return result
        
        return flatten(self._config)


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

    from mpdt.utils.color_printer import console, print_colored, print_success

    config = MPDTConfig()

    print_colored(f"MPDT 配置向导\n\n让我们配置 Neo-MoFox 主程序的路径和 GitHub Token", rgb=(0, 255, 255))

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
            console.print("[yellow]未设置 GitHub Token，稍后可使用 'mpdt config edit github.token <token>' 命令设置[/yellow]")

        # 配置 editor.command（可选）
        console.print("\n[cyan]编辑器命令用于 'mpdt config open' 命令打开文件[/cyan]")
        console.print("[dim]如果不确定，可以跳过此步骤，默认为系统默认编辑器[/dim]")
        editor_command = Prompt.ask(
            "[bold]请输入编辑器命令[/bold]",
            default=""
        )
        if editor_command and editor_command.strip():
            config.editor_command = editor_command.strip()
            print_success(f"编辑器命令已设置: {config.editor_command}")

    # 保存配置
    config.save()
    print_success(f"\n配置已保存: {config.config_path}")

    return config

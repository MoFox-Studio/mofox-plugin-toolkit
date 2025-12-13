"""
配置加载器
"""

from pathlib import Path
from typing import Any

import toml


class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_path: Path | str | None = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path) if config_path else None
        self.config: dict[str, Any] = {}

        if self.config_path and self.config_path.exists():
            self.load()

    def load(self) -> dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
        """
        if not self.config_path or not self.config_path.exists():
            return {}

        self.config = toml.load(str(self.config_path))
        return self.config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        支持点号分隔的嵌套键，例如: "mpdt.check.level"
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split(".")
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Path | str | None = None) -> None:
        """
        保存配置到文件
        
        Args:
            path: 保存路径，如果为 None 则使用初始化时的路径
        """
        save_path = Path(path) if path else self.config_path

        if not save_path:
            raise ValueError("未指定配置文件路径")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            toml.dump(self.config, f)


def load_mpdt_config(project_dir: Path | str = ".") -> ConfigLoader:
    """
    加载 MPDT 配置文件
    
    优先级:
    1. .mpdtrc.toml
    2. pyproject.toml 中的 [tool.mpdt] 部分
    
    Args:
        project_dir: 项目目录
        
    Returns:
        ConfigLoader 对象
    """
    project_dir = Path(project_dir)

    # 首先尝试加载 .mpdtrc.toml
    mpdtrc_path = project_dir / ".mpdtrc.toml"
    if mpdtrc_path.exists():
        return ConfigLoader(mpdtrc_path)

    # 然后尝试从 pyproject.toml 加载
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        config = toml.load(str(pyproject_path))
        if "tool" in config and "mpdt" in config["tool"]:
            loader = ConfigLoader()
            loader.config = config["tool"]["mpdt"]
            return loader

    # 返回空配置
    return ConfigLoader()


def get_default_config() -> dict[str, Any]:
    """
    获取默认配置
    
    Returns:
        默认配置字典
    """
    return {
        "mpdt": {
            "version": "0.1.2",
        },
        "check": {
            "level": "warning",
            "auto_fix": False,
            "ignore_patterns": ["tests/*", "*.pyc", "__pycache__/*"],
        },
        "test": {
            "coverage_threshold": 80,
            "pytest_args": ["-v", "--tb=short"],
        },
        "build": {
            "output_dir": "dist",
            "include_docs": True,
            "include_tests": False,
            "format": "zip",
        },
        "dev": {
            "port": 8080,
            "host": "127.0.0.1",
            "reload": True,
            "check_on_save": True,
        },
        "templates": {
            "author": "",
            "license": "GPL-v3.0",
            "python_version": "^3.11",
        },
    }

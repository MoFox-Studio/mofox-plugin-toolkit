"""Market CLI configuration."""

from __future__ import annotations

import os

from mpdt.utils.config_manager import MPDTConfig

DEFAULT_MARKET_BASE_URL = "http://39.96.71.162/"
DEFAULT_AUTHOR_TOKEN = "tAZUljLMi7xldea5LjXYMjpfFhuKcZcmLx7xQDPT0OzJg6KQdqxVwBE3QkVblia1"


def resolve_market_url(market_url: str | None = None) -> str:
    """Resolve the market base URL from CLI option, env or default."""

    return (
        market_url
        or os.getenv("PLUGIN_MARKET_BASE_URL")
        or os.getenv("MOFOX_MARKET_BASE_URL")
        or DEFAULT_MARKET_BASE_URL
    ).rstrip("/")


def resolve_author_token(token: str | None = None) -> str:
    """Resolve the author token from CLI option, env or development default."""

    return token or os.getenv("PLUGIN_MARKET_AUTHOR_TOKEN") or os.getenv("MOFOX_MARKET_TOKEN") or DEFAULT_AUTHOR_TOKEN


def resolve_github_token(token: str | None = None) -> str:
    """Resolve the GitHub token from CLI option or environment variables."""

    value = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN") or MPDTConfig().github_token
    if not value:
        raise ValueError("GitHub token is required. Pass --github-token or set GITHUB_TOKEN.")
    return value


def save_github_token(token: str) -> None:
    """Persist a GitHub token in the MPDT user config."""

    config = MPDTConfig()
    config.github_token = token
    config.save()

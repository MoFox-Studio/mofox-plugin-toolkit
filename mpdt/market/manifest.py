"""Manifest mapping for market API payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_manifest(plugin_path: str = ".") -> dict[str, Any]:
    """Load manifest.json from a plugin directory."""

    manifest_path = Path(plugin_path).resolve() / "manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"manifest.json 不存在: {manifest_path}")
    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("manifest.json 必须是对象")
    return data


def plugin_payload(manifest: dict[str, Any], repository_url: str | None = None) -> dict[str, Any]:
    """Convert MPDT manifest.json to market plugin registration payload."""

    plugin_id = str(manifest.get("name") or "").strip()
    if not plugin_id:
        raise ValueError("manifest.json 缺少 name 字段")
    repo = repository_url or manifest.get("repository_url") or f"https://github.com/MoFox-Studio/{plugin_id}"
    return {
        "plugin_id": plugin_id,
        "display_name": str(manifest.get("display_name") or plugin_id),
        "summary": str(manifest.get("summary") or manifest.get("description") or f"{plugin_id} 插件"),
        "description": str(manifest.get("description") or ""),
        "homepage": manifest.get("homepage") or repo,
        "repository_url": repo,
        "license": str(manifest.get("license") or "UNKNOWN"),
        "categories": list(manifest.get("categories") or []),
        "tags": list(manifest.get("tags") or []),
        "maintainers": _maintainers(manifest),
    }


def version_payload(
    manifest: dict[str, Any],
    asset_name: str,
    asset_download_url: str,
    release_url: str,
    sha256: str,
    file_size: int,
) -> dict[str, Any]:
    """Build market version submission payload."""

    plugin_id = str(manifest.get("name") or "").strip()
    version = str(manifest.get("version") or "").strip()
    if not plugin_id or not version:
        raise ValueError("manifest.json 必须包含 name 和 version 字段")
    return {
        "version": version,
        "release_tag": f"v{version}",
        "release_title": f"{plugin_id} {version}",
        "release_url": release_url,
        "asset_name": asset_name,
        "asset_download_url": asset_download_url,
        "checksum_sha256": sha256,
        "file_size": file_size,
        "is_prerelease": "-" in version,
        "plugin_api_version": str(manifest.get("plugin_api_version") or "1.0"),
        "min_host_version": str(manifest.get("min_host_version") or manifest.get("min_core_version") or "1.0.0"),
        "max_host_version": manifest.get("max_host_version"),
        "supported_platforms": list(manifest.get("supported_platforms") or ["all"]),
    }


def release_tag_for_version(version: str) -> str:
    """Return the normalized GitHub release tag for a plugin version."""

    return version if version.startswith("v") else f"v{version}"


def release_url_for(plugin_id: str, version: str) -> str:
    """Return the default GitHub Release page URL."""

    tag = release_tag_for_version(version)
    return f"https://github.com/MoFox-Studio/{plugin_id}/releases/tag/{tag}"


def asset_download_url_for(plugin_id: str, version: str, asset_name: str) -> str:
    """Return the default GitHub Release asset URL."""

    tag = release_tag_for_version(version)
    return f"https://github.com/MoFox-Studio/{plugin_id}/releases/download/{tag}/{asset_name}"


def _maintainers(manifest: dict[str, Any]) -> list[str]:
    """Extract maintainers from manifest fields."""

    maintainers = manifest.get("maintainers")
    if isinstance(maintainers, list) and maintainers:
        return [str(item) for item in maintainers]
    author = str(manifest.get("author") or "mock-author").strip()
    return [author or "mock-author"]

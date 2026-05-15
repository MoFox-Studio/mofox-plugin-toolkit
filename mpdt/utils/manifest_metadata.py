"""Manifest metadata rules and interactive prompts."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import questionary

from .color_printer import print_success, print_warning

ALLOWED_CATEGORIES = ("tool", "chat", "fun", "information", "moderation")


def get_display_name(manifest: dict[str, Any]) -> str:
    """Return normalized display_name from manifest."""

    value = manifest.get("display_name")
    if not isinstance(value, str):
        return ""
    return value.strip()


def get_categories(manifest: dict[str, Any]) -> list[str]:
    """Return normalized categories from manifest."""
    value = manifest.get("categories")
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def get_tags(manifest: dict[str, Any]) -> list[str]:
    """Return normalized tags from manifest."""
    value = manifest.get("tags")
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        tag = item.strip()
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized


def normalize_tags(raw_tags: str) -> list[str]:
    """Parse raw tag input into a de-duplicated tag list."""
    tags: list[str] = []
    normalized_input = raw_tags.replace("，", ",").replace("\n", ",")
    for part in normalized_input.split(","):
        tag = part.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def categories_are_valid(manifest: dict[str, Any]) -> bool:
    """Return whether manifest categories satisfy the packaging rules."""
    categories = get_categories(manifest)
    return len(categories) == 1 and categories[0] in ALLOWED_CATEGORIES


def tags_are_valid(manifest: dict[str, Any]) -> bool:
    """Return whether manifest tags satisfy the packaging rules."""
    return bool(get_tags(manifest))


def metadata_errors(manifest: dict[str, Any], plugin_dir: Path | None = None) -> list[str]:
    """Return validation errors for required manifest metadata."""
    errors: list[str] = []
    if not get_display_name(manifest):
        errors.append("manifest.json 的 display_name 必须是非空字符串")
    if not categories_are_valid(manifest):
        allowed = ", ".join(ALLOWED_CATEGORIES)
        errors.append(f"manifest.json 的 categories 必须是只包含一个值的数组，且取值只能是: {allowed}")
    if not tags_are_valid(manifest):
        errors.append("manifest.json 的 tags 必须是至少包含一个非空字符串的数组")
    icon_error = _icon_error(manifest, plugin_dir)
    if icon_error:
        errors.append(icon_error)
    return errors


def _is_interactive_terminal() -> bool:
    """Return whether stdin/stdout are attached to a TTY."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _has_running_event_loop() -> bool:
    """Return whether the current thread is already inside a running event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return False
    return True


def _finalize_manifest_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy single-value metadata keys."""
    manifest.pop("category", None)
    manifest.pop("tag", None)
    return manifest


def _save_manifest(plugin_dir: Path, manifest: dict[str, Any]) -> None:
    """Persist manifest.json after interactive metadata repair."""
    manifest_path = plugin_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=4)


def prompt_manifest_metadata(existing_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collect required manifest metadata from the console."""
    manifest = existing_manifest or {}
    display_name = get_display_name(manifest) or str(manifest.get("name") or "").strip()
    existing_categories = get_categories(manifest)
    default_category = existing_categories[0] if existing_categories else ALLOWED_CATEGORIES[0]
    existing_tags = ", ".join(get_tags(manifest))

    resolved_display_name = questionary.text(
        "填写插件展示名 display_name:",
        default=display_name,
        validate=lambda value: bool(str(value).strip()) or "display_name 不能为空",
    ).ask()
    if resolved_display_name is None:
        raise ValueError("已取消填写 display_name")

    category = questionary.select(
        "选择插件分类 categories（只能选一个）:",
        choices=[questionary.Choice(item, value=item) for item in ALLOWED_CATEGORIES],
        default=default_category,
    ).ask()
    if category is None:
        raise ValueError("已取消填写 categories")

    tags_text = questionary.text(
        "填写插件 tags（多个标签用逗号分隔）:",
        default=existing_tags,
        validate=lambda value: bool(normalize_tags(value)) or "至少填写一个 tag",
    ).ask()
    if tags_text is None:
        raise ValueError("已取消填写 tags")

    return {
        "display_name": str(resolved_display_name).strip(),
        "categories": [category],
        "tags": normalize_tags(tags_text),
    }


async def prompt_manifest_metadata_async(existing_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    """Collect required manifest metadata from the console inside an event loop."""
    manifest = existing_manifest or {}
    display_name = get_display_name(manifest) or str(manifest.get("name") or "").strip()
    existing_categories = get_categories(manifest)
    default_category = existing_categories[0] if existing_categories else ALLOWED_CATEGORIES[0]
    existing_tags = ", ".join(get_tags(manifest))

    resolved_display_name = await questionary.text(
        "填写插件展示名 display_name:",
        default=display_name,
        validate=lambda value: bool(str(value).strip()) or "display_name 不能为空",
    ).ask_async()
    if resolved_display_name is None:
        raise ValueError("已取消填写 display_name")

    category = await questionary.select(
        "选择插件分类 categories（只能选一个）:",
        choices=[questionary.Choice(item, value=item) for item in ALLOWED_CATEGORIES],
        default=default_category,
    ).ask_async()
    if category is None:
        raise ValueError("已取消填写 categories")

    tags_text = await questionary.text(
        "填写插件 tags（多个标签用逗号分隔）:",
        default=existing_tags,
        validate=lambda value: bool(normalize_tags(value)) or "至少填写一个 tag",
    ).ask_async()
    if tags_text is None:
        raise ValueError("已取消填写 tags")

    return {
        "display_name": str(resolved_display_name).strip(),
        "categories": [category],
        "tags": normalize_tags(tags_text),
    }


def ensure_manifest_metadata_interactive(plugin_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Prompt for missing manifest metadata and persist it when running in a TTY."""
    errors = metadata_errors(manifest, plugin_dir)
    if not errors:
        return _finalize_manifest_metadata(manifest)

    if not _is_interactive_terminal() or _has_running_event_loop():
        return manifest

    print_warning("检测到 manifest.json 缺少或无效的市场元数据，进入交互补全...")
    for error in errors:
        print_warning(error)

    manifest.update(prompt_manifest_metadata(manifest))
    _finalize_manifest_metadata(manifest)
    _save_manifest(plugin_dir, manifest)

    print_success("已更新 manifest.json 中的市场元数据")
    return manifest


async def ensure_manifest_metadata_interactive_async(plugin_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Async prompt for missing manifest metadata and persist it when running in a TTY."""
    errors = metadata_errors(manifest, plugin_dir)
    if not errors:
        return _finalize_manifest_metadata(manifest)

    if not _is_interactive_terminal():
        return manifest

    print_warning("检测到 manifest.json 缺少或无效的市场元数据，进入交互补全...")
    for error in errors:
        print_warning(error)

    manifest.update(await prompt_manifest_metadata_async(manifest))
    _finalize_manifest_metadata(manifest)
    _save_manifest(plugin_dir, manifest)

    print_success("已更新 manifest.json 中的市场元数据")
    return manifest


def _icon_error(manifest: dict[str, Any], plugin_dir: Path | None) -> str | None:
    """Return a validation error for the optional icon field, if any."""

    icon = manifest.get("icon")
    if icon is None or str(icon).strip() == "":
        return None
    if not isinstance(icon, str):
        return "manifest.json 的 icon 必须是字符串路径"
    if plugin_dir is None:
        return None
    icon_path = plugin_dir / icon
    if not icon_path.exists() or not icon_path.is_file():
        return f"manifest.json 的 icon 指向的文件不存在: {icon}"
    if icon_path.suffix.lower() != ".png":
        return "manifest.json 的 icon 必须指向 .png 文件"
    return None
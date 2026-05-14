"""Plugin market command implementations."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.table import Table

from mpdt.commands.build import build_package
from mpdt.market.client import MarketClient, MarketClientError
from mpdt.market.config import resolve_author_token, resolve_github_token, resolve_market_url, save_github_token
from mpdt.market.git import (
    GitError,
    current_branch,
    ensure_commit,
    ensure_git_repo,
    ensure_tag,
    github_push_url,
    push_branch_and_tag,
    set_remote,
)
from mpdt.market.github import GitHubClient, GitHubClientError
from mpdt.market.manifest import (
    asset_download_url_for,
    load_manifest,
    plugin_payload,
    release_tag_for_version,
    release_url_for,
    version_payload,
)
from mpdt.utils.color_printer import console


def market_doctor(market_url: str | None = None, token: str | None = None) -> None:
    """Check connectivity to the market backend."""

    async def run() -> None:
        client = _client(market_url, token)
        result = await client.health()
        _print_ok(f"Market server reachable: {client.base_url}")
        _print_info(f"Service status: {result.get('status', '-')}")
        _print_info(f"Service name: {result.get('service', '-')}")

    _run_market(run())


def market_register(plugin_path: str = ".", market_url: str | None = None, token: str | None = None, repository_url: str | None = None) -> None:
    """Register a plugin in the market."""

    async def run() -> None:
        manifest = load_manifest(plugin_path)
        payload = plugin_payload(manifest, repository_url=repository_url)
        result = await _client(market_url, token).register_plugin(payload)
        _print_ok(f"Plugin registered: {result['plugin_id']} ({result['status']})")

    _run_market(run())


def market_update(plugin_path: str = ".", market_url: str | None = None, token: str | None = None, repository_url: str | None = None) -> None:
    """Update plugin metadata in the market."""

    async def run() -> None:
        manifest = load_manifest(plugin_path)
        payload = plugin_payload(manifest, repository_url=repository_url)
        plugin_id = payload.pop("plugin_id")
        result = await _client(market_url, token).update_plugin(plugin_id, payload)
        _print_ok(f"Plugin updated: {result['plugin_id']} ({result['status']})")

    _run_market(run())


def market_package(plugin_path: str = ".", output_dir: str = "dist", with_docs: bool = False) -> None:
    """Build a package and print market metadata."""

    result = build_package(plugin_path=plugin_path, output_dir=output_dir, with_docs=with_docs, fmt="mfp", show_progress=False)
    if result is None:
        return
    table = Table(title="Market package")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("asset_name", result.package_path.name)
    table.add_row("file_size", str(result.package_size))
    table.add_row("sha256", result.sha256)
    table.add_row("path", str(result.package_path))
    console.print(table)


def market_submit_version(
    plugin_path: str = ".",
    market_url: str | None = None,
    token: str | None = None,
    asset_url: str | None = None,
    release_url: str | None = None,
    output_dir: str = "dist",
    with_docs: bool = False,
) -> None:
    """Build and submit a plugin version to the market."""

    async def run() -> None:
        manifest = load_manifest(plugin_path)
        package = build_package(plugin_path=plugin_path, output_dir=output_dir, with_docs=with_docs, fmt="mfp", show_progress=False)
        if package is None:
            return
        plugin_id = str(manifest["name"])
        version = str(manifest["version"])
        default_release_url = release_url or release_url_for(plugin_id, version)
        default_asset_url = asset_url or asset_download_url_for(plugin_id, version, package.package_path.name)
        payload = version_payload(
            manifest,
            asset_name=package.package_path.name,
            asset_download_url=default_asset_url,
            release_url=default_release_url,
            sha256=package.sha256,
            file_size=package.package_size,
        )
        result = await _client(market_url, token).submit_version(plugin_id, payload)
        _print_ok(f"Version submitted: {plugin_id}@{result['version']} ({result['status']})")

    _run_market(run())


def market_sync(
    plugin_path: str = ".",
    market_url: str | None = None,
    token: str | None = None,
    asset_url: str | None = None,
    release_url: str | None = None,
    output_dir: str = "dist",
    with_docs: bool = False,
) -> None:
    """Rebuild and sync version metadata."""

    async def run() -> None:
        manifest = load_manifest(plugin_path)
        package = build_package(plugin_path=plugin_path, output_dir=output_dir, with_docs=with_docs, fmt="mfp", show_progress=False)
        if package is None:
            return
        plugin_id = str(manifest["name"])
        version = str(manifest["version"])
        default_release_url = release_url or release_url_for(plugin_id, version)
        payload = {
            "version": version,
            "release_url": default_release_url,
            "asset_name": package.package_path.name,
            "asset_download_url": asset_url or asset_download_url_for(plugin_id, version, package.package_path.name),
            "checksum_sha256": package.sha256,
            "file_size": package.package_size,
        }
        result = await _client(market_url, token).sync_version(plugin_id, payload)
        _print_ok(f"Version synced: {plugin_id}@{result['version']} ({result['last_sync_status']})")

    _run_market(run())


def market_publish(
    plugin_path: str = ".",
    market_url: str | None = None,
    token: str | None = None,
    github_token: str | None = None,
    owner: str | None = None,
    repo: str | None = None,
    private: bool = False,
    output_dir: str = "dist",
    with_docs: bool = False,
    release_notes: str | None = None,
    skip_push: bool = False,
    save_token: bool | None = None,
) -> None:
    """Build, publish a GitHub release, and sync metadata to the market backend."""

    resolved_save_token = _should_save_github_token(save_token) if github_token else False

    async def run() -> None:
        plugin_dir = Path(plugin_path).resolve()
        manifest = load_manifest(str(plugin_dir))
        package = build_package(plugin_path=str(plugin_dir), output_dir=output_dir, with_docs=with_docs, fmt="mfp", show_progress=False)
        if package is None:
            return

        plugin_id = str(manifest["name"])
        version = str(manifest["version"])
        tag = release_tag_for_version(version)
        if github_token and resolved_save_token:
            save_github_token(github_token)
            _print_ok("GitHub token saved to MPDT user config")
        github_api_token = resolve_github_token(github_token)
        github = GitHubClient(github_api_token)

        user = await github.current_user()
        resolved_owner = owner or str(manifest.get("github_owner") or user["login"])
        resolved_repo = repo or str(manifest.get("github_repo") or plugin_id)
        release_title = f"{plugin_id} {version}"
        release_body = release_notes or str(manifest.get("release_notes") or f"Release {version}")
        is_prerelease = "-" in version

        _print_info(f"Ensuring GitHub repository: {resolved_owner}/{resolved_repo}")
        repository = await github.ensure_repo(
            resolved_owner,
            resolved_repo,
            description=str(manifest.get("summary") or manifest.get("description") or f"{plugin_id} plugin"),
            private=private,
        )
        repo_html_url = str(repository["html_url"])
        clone_url = str(repository["clone_url"])

        ensure_git_repo(plugin_dir)
        set_remote(plugin_dir, clone_url)
        ensure_commit(plugin_dir, f"Release {version}")
        branch = current_branch(plugin_dir)
        ensure_tag(plugin_dir, tag)
        if skip_push:
            _print_info("Skipping git push because --skip-push was set")
        else:
            _print_info(f"Pushing {branch} and {tag} to GitHub")
            push_branch_and_tag(plugin_dir, branch, tag, github_push_url(resolved_owner, resolved_repo, github_api_token))

        _print_info(f"Ensuring GitHub Release: {tag}")
        release = await github.ensure_release(
            resolved_owner,
            resolved_repo,
            tag,
            title=release_title,
            body=release_body,
            prerelease=is_prerelease,
        )
        _print_info(f"Uploading release asset: {package.package_path.name}")
        asset = await github.upload_asset(release, package.package_path)

        release_url = str(release.get("html_url") or release_url_for(plugin_id, version))
        asset_url = str(asset.get("browser_download_url") or asset_download_url_for(plugin_id, version, package.package_path.name))

        market = _client(market_url, token or github_api_token)
        plugin_registration_payload = plugin_payload(manifest, repository_url=repo_html_url)
        try:
            plugin = await market.register_plugin(plugin_registration_payload)
            _print_ok(f"Plugin registered: {plugin['plugin_id']} ({plugin['status']})")
        except MarketClientError as exc:
            if not str(exc).startswith("PLUGIN_ALREADY_EXISTS"):
                raise
            update_payload = dict(plugin_registration_payload)
            update_payload.pop("plugin_id", None)
            plugin = await market.update_plugin(plugin_id, update_payload)
            _print_ok(f"Plugin metadata updated: {plugin['plugin_id']} ({plugin['status']})")

        version_registration_payload = version_payload(
            manifest,
            asset_name=package.package_path.name,
            asset_download_url=asset_url,
            release_url=release_url,
            sha256=package.sha256,
            file_size=package.package_size,
        )
        try:
            submitted = await market.submit_version(plugin_id, version_registration_payload)
            _print_ok(f"Version submitted: {plugin_id}@{submitted['version']} ({submitted['status']})")
        except MarketClientError as exc:
            if not str(exc).startswith("VERSION_ALREADY_EXISTS"):
                raise
            synced = await market.sync_version(
                plugin_id,
                {
                    "version": version,
                    "release_url": release_url,
                    "release_title": release_title,
                    "asset_name": package.package_path.name,
                    "asset_download_url": asset_url,
                    "checksum_sha256": package.sha256,
                    "file_size": package.package_size,
                },
            )
            _print_ok(f"Version synced: {plugin_id}@{synced['version']} ({synced['last_sync_status']})")

        _print_ok(f"Publish complete: {repo_html_url}/releases/tag/{tag}")

    _run_market(run())


def _should_save_github_token(save_token: bool | None) -> bool:
    """Return whether a provided GitHub token should be persisted."""

    if save_token is not None:
        return save_token
    try:
        import questionary

        return bool(questionary.confirm("Save this GitHub token to ~/.mpdt/config.toml for future publish commands?", default=False).ask())
    except Exception:
        return False


def market_status(plugin_path: str = ".", market_url: str | None = None, token: str | None = None, plugin_id: str | None = None) -> None:
    """Show plugin market status."""

    async def run() -> None:
        resolved_plugin_id = plugin_id
        if not resolved_plugin_id:
            resolved_plugin_id = str(load_manifest(plugin_path)["name"])
        result = await _client(market_url, token).status(resolved_plugin_id)
        table = Table(title=f"Market status: {resolved_plugin_id}")
        table.add_column("Version", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Sync", style="yellow")
        table.add_column("Yanked", style="red")
        for item in result.get("versions", []):
            table.add_row(item["version"], item["status"], item["last_sync_status"], str(item.get("is_yanked", False)))
        console.print(f"Plugin status: [bold]{result.get('plugin_status')}[/bold]")
        console.print(table)

    _run_market(run())


def market_yank(plugin_path: str = ".", version: str | None = None, market_url: str | None = None, token: str | None = None, reason: str | None = None) -> None:
    """Yank a plugin version as its author."""

    async def run() -> None:
        manifest = load_manifest(plugin_path)
        plugin_id = str(manifest["name"])
        resolved_version = version or str(manifest["version"])
        result = await _client(market_url, token).yank_version(plugin_id, resolved_version, reason=reason)
        _print_ok(f"Version yanked: {plugin_id}@{result['version']} ({result['status']})")

    _run_market(run())


def market_search(query: str | None = None, category: str | None = None, tag: str | None = None, limit: int = 20, market_url: str | None = None) -> None:
    """Search public market plugins."""

    async def run() -> None:
        result = await _client(market_url, None).search_plugins(query=query, category=category, tag=tag, limit=limit)
        table = Table(title=f"Market plugins ({result.get('total', 0)})")
        table.add_column("Plugin", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Summary")
        for item in result.get("items", []):
            table.add_row(item["plugin_id"], item["display_name"], item["status"], item["summary"])
        console.print(table)

    _run_market(run())


def market_info(plugin_id: str, market_url: str | None = None) -> None:
    """Show public plugin detail and versions."""

    async def run() -> None:
        client = _client(market_url, None)
        detail = await client.plugin_detail(plugin_id)
        versions = await client.plugin_versions(plugin_id)
        console.print(f"Plugin: [bold]{detail['plugin_id']}[/bold]")
        console.print(f"Name: {detail['display_name']}")
        console.print(f"Status: {detail['status']}")
        console.print(f"Repository: {detail['repository_url']}")
        console.print(f"Summary: {detail['summary']}")
        if detail.get("risk_notice"):
            console.print(f"Risk: [red]{detail['risk_notice']}[/red]")
        table = Table(title="Versions")
        table.add_column("Version", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Prerelease", style="yellow")
        table.add_column("Platforms")
        table.add_column("SHA256")
        for item in versions.get("items", []):
            table.add_row(
                item["version"],
                item["status"],
                str(item.get("is_prerelease", False)),
                ",".join(item.get("supported_platforms") or []),
                item["checksum_sha256"],
            )
        console.print(table)

    _run_market(run())


def market_install_info(
    plugin_id: str,
    market_url: str | None = None,
    host_version: str | None = None,
    plugin_api_version: str | None = None,
    platform: str | None = None,
    include_prerelease: bool = False,
) -> None:
    """Show install metadata for the recommended version."""

    async def run() -> None:
        result = await _client(market_url, None).install_info(
            plugin_id,
            host_version=host_version,
            plugin_api_version=plugin_api_version,
            platform=platform,
            include_prerelease=include_prerelease,
        )
        plugin = result["plugin"]
        version = result["version"]
        table = Table(title=f"Install info: {plugin['plugin_id']}")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("version", version["version"])
        table.add_row("plugin_api_version", version["plugin_api_version"])
        table.add_row("host_range", f"{version['min_host_version']} - {version.get('max_host_version') or '*'}")
        table.add_row("platforms", ",".join(version.get("supported_platforms") or []))
        table.add_row("prerelease", str(version.get("is_prerelease", False)))
        table.add_row("asset", version["asset_name"])
        table.add_row("download_url", version["asset_download_url"])
        table.add_row("sha256", version["checksum_sha256"])
        table.add_row("file_size", str(version["file_size"]))
        console.print(table)

    _run_market(run())


def _client(market_url: str | None, token: str | None) -> MarketClient:
    """Create a configured market client."""

    return MarketClient(resolve_market_url(market_url), resolve_author_token(token))


def _run_market(awaitable) -> None:
    """Run an async market command and render failures."""

    try:
        asyncio.run(awaitable)
    except MarketClientError as e:
        _print_error(str(e))
    except GitHubClientError as e:
        _print_error(f"GitHub request failed: {e}")
    except GitError as e:
        _print_error(f"Git command failed: {e}")
    except ValueError as e:
        _print_error(str(e))
    except OSError as e:
        _print_error(f"Market server connection failed: {e}")


def _print_ok(message: str) -> None:
    """Print an ASCII success message."""

    console.print(f"[bold green][OK][/bold green] {message}")


def _print_info(message: str) -> None:
    """Print an ASCII info message."""

    console.print(f"[bold blue][INFO][/bold blue] {message}")


def _print_error(message: str) -> None:
    """Print an ASCII error message."""

    console.print(f"[bold red][ERROR][/bold red] {message}")

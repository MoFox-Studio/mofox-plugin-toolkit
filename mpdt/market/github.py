"""GitHub REST API client for plugin market publishing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import aiohttp


class GitHubClientError(RuntimeError):
    """Raised when GitHub returns an error response."""


class GitHubClient:
    """Minimal async GitHub client for repository and release publishing."""

    def __init__(self, token: str, timeout: int = 60) -> None:
        """Initialize the GitHub API client."""

        self.token = token
        self.timeout = timeout

    async def current_user(self) -> dict[str, Any]:
        """Return the authenticated GitHub user."""

        return await self._request("GET", "https://api.github.com/user")

    async def get_repo(self, owner: str, repo: str) -> dict[str, Any] | None:
        """Return a repository or None when it does not exist."""

        try:
            return await self._request("GET", f"https://api.github.com/repos/{owner}/{repo}")
        except GitHubClientError as exc:
            if str(exc).startswith("HTTP_404"):
                return None
            raise

    async def create_repo(self, owner: str, repo: str, description: str, private: bool = False) -> dict[str, Any]:
        """Create a user or organization repository."""

        user = await self.current_user()
        payload = {"name": repo, "description": description, "private": private, "auto_init": False}
        if owner.lower() == str(user.get("login", "")).lower():
            return await self._request("POST", "https://api.github.com/user/repos", json=payload)
        return await self._request("POST", f"https://api.github.com/orgs/{owner}/repos", json=payload)

    async def ensure_repo(self, owner: str, repo: str, description: str, private: bool = False) -> dict[str, Any]:
        """Return an existing repository or create it."""

        existing = await self.get_repo(owner, repo)
        if existing is not None:
            return existing
        return await self.create_repo(owner, repo, description, private=private)

    async def get_release_by_tag(self, owner: str, repo: str, tag: str) -> dict[str, Any] | None:
        """Return a release by tag or None when missing."""

        try:
            return await self._request("GET", f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}")
        except GitHubClientError as exc:
            if str(exc).startswith("HTTP_404"):
                return None
            raise

    async def create_release(
        self,
        owner: str,
        repo: str,
        tag: str,
        title: str,
        body: str,
        prerelease: bool = False,
    ) -> dict[str, Any]:
        """Create a GitHub release."""

        return await self._request(
            "POST",
            f"https://api.github.com/repos/{owner}/{repo}/releases",
            json={"tag_name": tag, "name": title, "body": body, "draft": False, "prerelease": prerelease},
        )

    async def ensure_release(
        self,
        owner: str,
        repo: str,
        tag: str,
        title: str,
        body: str,
        prerelease: bool = False,
    ) -> dict[str, Any]:
        """Return an existing release or create it."""

        existing = await self.get_release_by_tag(owner, repo, tag)
        if existing is not None:
            return existing
        return await self.create_release(owner, repo, tag, title, body, prerelease=prerelease)

    async def upload_asset(self, release: dict[str, Any], asset_path: Path, replace: bool = True) -> dict[str, Any]:
        """Upload a release asset, replacing an existing asset with the same name when requested."""

        assets = release.get("assets") or []
        for asset in assets:
            if asset.get("name") == asset_path.name:
                if not replace:
                    return asset
                await self._request("DELETE", str(asset["url"]), expect_json=False)
                break
        upload_url = str(release["upload_url"]).split("{", 1)[0]
        headers = {"Content-Type": "application/octet-stream"}
        params = {"name": asset_path.name}
        data = asset_path.read_bytes()
        return await self._request("POST", upload_url, params=params, data=data, headers=headers)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        expect_json: bool = True,
    ) -> dict[str, Any]:
        """Send a GitHub API request and normalize errors."""

        request_headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            **(headers or {}),
        }
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout, headers=request_headers) as session:
            async with session.request(method, url, json=json, params=params, data=data) as response:
                if response.status == 204 and not expect_json:
                    return {}
                payload = await response.json(content_type=None)
                if response.status >= 400:
                    message = payload.get("message", "GitHub request failed.") if isinstance(payload, dict) else "GitHub request failed."
                    raise GitHubClientError(f"HTTP_{response.status}: {message}")
                if not isinstance(payload, dict):
                    raise GitHubClientError("INVALID_RESPONSE: GitHub response is not an object.")
                return payload

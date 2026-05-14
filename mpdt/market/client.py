"""HTTP client for the plugin market API."""

from __future__ import annotations

from typing import Any

import aiohttp


class MarketClientError(RuntimeError):
    """Raised when the market API returns an error response."""


class MarketClient:
    """Small async client for the plugin market backend."""

    def __init__(self, base_url: str, token: str, timeout: int = 30) -> None:
        """Initialize the market client."""

        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    async def health(self) -> dict[str, Any]:
        """Check market service health."""

        return await self._request("GET", "/health", authenticated=False)

    async def register_plugin(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a plugin."""

        return await self._request("POST", "/api/v1/plugins", json=payload)

    async def update_plugin(self, plugin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update plugin metadata."""

        return await self._request("PUT", f"/api/v1/plugins/{plugin_id}", json=payload)

    async def submit_version(self, plugin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit a plugin version."""

        return await self._request("POST", f"/api/v1/plugins/{plugin_id}/versions", json=payload)

    async def sync_version(self, plugin_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Sync version metadata."""

        return await self._request("POST", f"/api/v1/plugins/{plugin_id}/sync", json=payload)

    async def yank_version(self, plugin_id: str, version: str, reason: str | None = None) -> dict[str, Any]:
        """Yank a plugin version."""

        return await self._request("POST", f"/api/v1/plugins/{plugin_id}/versions/{version}/yank", json={"reason": reason})

    async def status(self, plugin_id: str) -> dict[str, Any]:
        """Fetch plugin market status."""

        return await self._request("GET", f"/api/v1/plugins/{plugin_id}/status")

    async def search_plugins(
        self,
        query: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search public plugins."""

        params = {"limit": str(limit)}
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        return await self._request("GET", "/api/v1/plugins", params=params, authenticated=False)

    async def plugin_detail(self, plugin_id: str) -> dict[str, Any]:
        """Fetch public plugin detail."""

        return await self._request("GET", f"/api/v1/plugins/{plugin_id}", authenticated=False)

    async def plugin_versions(self, plugin_id: str) -> dict[str, Any]:
        """Fetch public plugin versions."""

        return await self._request("GET", f"/api/v1/plugins/{plugin_id}/versions", authenticated=False)

    async def recommended_version(
        self,
        plugin_id: str,
        host_version: str | None = None,
        plugin_api_version: str | None = None,
        platform: str | None = None,
        include_prerelease: bool = False,
    ) -> dict[str, Any]:
        """Fetch the recommended compatible version."""

        params = self._compat_params(host_version, plugin_api_version, platform, include_prerelease)
        return await self._request("GET", f"/api/v1/plugins/{plugin_id}/recommended-version", params=params, authenticated=False)

    async def install_info(
        self,
        plugin_id: str,
        host_version: str | None = None,
        plugin_api_version: str | None = None,
        platform: str | None = None,
        include_prerelease: bool = False,
    ) -> dict[str, Any]:
        """Fetch install metadata."""

        params = self._compat_params(host_version, plugin_api_version, platform, include_prerelease)
        return await self._request("GET", f"/api/v1/plugins/{plugin_id}/install", params=params, authenticated=False)

    def _compat_params(
        self,
        host_version: str | None,
        plugin_api_version: str | None,
        platform: str | None,
        include_prerelease: bool,
    ) -> dict[str, str]:
        """Build compatibility query parameters used by install decisions."""

        params: dict[str, str] = {"include_prerelease": str(include_prerelease).lower()}
        if host_version:
            params["host_version"] = host_version
        if plugin_api_version:
            params["plugin_api_version"] = plugin_api_version
        if platform:
            params["platform"] = platform
        return params

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Send a request and normalize market errors."""

        headers = {"Authorization": f"Bearer {self.token}"} if authenticated else None
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, f"{self.base_url}{path}", json=json, params=params, headers=headers) as response:
                data = await response.json(content_type=None)
                if response.status >= 400:
                    error = data.get("error", {}) if isinstance(data, dict) else {}
                    code = error.get("code", f"HTTP_{response.status}")
                    message = error.get("message", "Market request failed.")
                    raise MarketClientError(f"{code}: {message}")
                if not isinstance(data, dict | list):
                    raise MarketClientError("INVALID_RESPONSE: Market response is not an object or list.")
                return data

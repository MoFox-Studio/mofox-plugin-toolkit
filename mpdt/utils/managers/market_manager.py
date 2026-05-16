"""
插件市场管理器
处理与插件市场 API 的交互
"""

from __future__ import annotations

import sys
from typing import Any

import aiohttp

from mpdt.utils.managers.config_manager import get_or_init_mpdt_config
from mpdt.utils.color_printer import print_error


class MarketError(RuntimeError):
    """插件市场 API 错误"""


class MarketManager:
    """插件市场统一管理器
    
    提供与 Neo-MoFox Plugin Market API 的交互功能：
    - 插件注册、更新和查询
    - 版本提交、同步和撤回
    - 兼容性查询和安装信息获取
    """

    def __init__(self, timeout: int = 30):
        """初始化市场管理器
        
        Args:
            timeout: 请求超时时间（秒）
        """
        self.base_url = self._resolve_url()
        self.token = self._resolve_token()
        self.timeout = timeout

    @classmethod
    def _resolve_url(cls) -> str:
        """解析市场 URL，从配置管理器读取"""
        config = get_or_init_mpdt_config()
        return config.market_url

    @classmethod
    def _resolve_token(cls) -> str:
        """从配置文件解析 GitHub Token，同时用于市场和 GitHub 操作
        
        Returns:
            GitHub Token
            
        Raises:
            RuntimeError: 如果未配置 GitHub Token
        """
        config = get_or_init_mpdt_config()
        token = config.github_token
        
        if not token:
            print_error("未找到 GitHub Token，请运行 'mpdt config edit github.token <your_token>' 进行配置")
            sys.exit(1)

        return token

    async def health(self) -> Any:
        """检查市场服务进程健康状态
        
        API: GET /health
        
        Returns:
            dict: 健康状态信息
        """
        return await self._request("GET", "/health", authenticated=False)

    async def register_plugin(self, payload: dict[str, Any]) -> Any:
        """注册新插件到市场
        
        API: POST /api/v1/plugins
        
        Args:
            payload: 插件注册数据 (PluginCreate schema)
            
        Returns:
            dict: 注册的插件信息 (Plugin schema)
            
        Raises:
            MarketError: 插件已存在或验证失败
        """
        return await self._request("POST", "/api/v1/plugins", json=payload)

    async def update_plugin(
        self, plugin_id: str, payload: dict[str, Any]
    ) -> Any:
        """更新插件的可变元数据
        
        API: PUT /api/v1/plugins/{plugin_id}
        
        Args:
            plugin_id: 插件唯一标识符
            payload: 更新数据 (PluginUpdate schema)
            
        Returns:
            dict: 更新后的插件信息 (Plugin schema)
        """
        return await self._request("PUT", f"/api/v1/plugins/{plugin_id}", json=payload)

    async def submit_version(
        self, plugin_id: str, payload: dict[str, Any]
    ) -> Any:
        """提交插件的新版本
        
        API: POST /api/v1/plugins/{plugin_id}/versions
        
        Args:
            plugin_id: 插件唯一标识符
            payload: 版本数据 (PluginVersionCreate schema)
            
        Returns:
            dict: 提交的版本信息 (PluginVersion schema)
            
        Raises:
            MarketError: 版本已存在或验证失败
        """
        return await self._request(
            "POST", f"/api/v1/plugins/{plugin_id}/versions", json=payload
        )

    async def sync_version(
        self, plugin_id: str, payload: dict[str, Any]
    ) -> Any:
        """同步已存在版本的元数据（从 GitHub Release 更新）
        
        API: POST /api/v1/plugins/{plugin_id}/sync
        
        Args:
            plugin_id: 插件唯一标识符
            payload: 同步数据 (VersionSyncRequest schema)，至少包含 version 字段
            
        Returns:
            dict: 同步后的版本信息 (PluginVersion schema)
        """
        return await self._request(
            "POST", f"/api/v1/plugins/{plugin_id}/sync", json=payload
        )

    async def yank_version(
        self, plugin_id: str, version: str, reason: str | None = None
    ) -> Any:
        """撤回（标记为不推荐）插件的某个版本
        
        API: POST /api/v1/plugins/{plugin_id}/versions/{version}/yank
        
        Args:
            plugin_id: 插件唯一标识符
            version: 要撤回的版本号
            reason: 撤回原因说明（可选）
            
        Returns:
            dict: 撤回后的版本信息 (PluginVersion schema)，is_yanked 字段为 true
        """
        return await self._request(
            "POST",
            f"/api/v1/plugins/{plugin_id}/versions/{version}/yank",
            json={"reason": reason},
        )

    async def yank_my_plugin_version(
        self, plugin_id: str, version: str, reason: str | None = None
    ) -> Any:
        """作为插件owner/maintainer撤回插件的某个版本
        
        API: POST /api/v1/me/plugins/{plugin_id}/versions/{version}/yank
        
        Args:
            plugin_id: 插件唯一标识符
            version: 要撤回的版本号
            reason: 撤回原因说明（可选）
            
        Returns:
            dict: 撤回后的版本信息 (PluginVersion schema)，is_yanked 字段为 true
        """
        payload = {"reason": reason} if reason else None
        return await self._request(
            "POST",
            f"/api/v1/me/plugins/{plugin_id}/versions/{version}/yank",
            json=payload,
        )

    async def delete_my_plugin(self, plugin_id: str) -> Any:
        """作为插件owner/maintainer删除插件
        
        API: DELETE /api/v1/me/plugins/{plugin_id}
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            dict: 空响应（HTTP 204）
            
        Raises:
            MarketError: 无权限或插件不存在
        """
        return await self._request(
            "DELETE",
            f"/api/v1/me/plugins/{plugin_id}",
        )

    async def get_plugin_status(self, plugin_id: str) -> Any:
        """获取插件的发布和同步状态
        
        API: GET /api/v1/plugins/{plugin_id}/status
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            dict: 插件状态信息，包括发布状态和同步状态
        """
        return await self._request("GET", f"/api/v1/plugins/{plugin_id}/status")

    async def search_plugins(
        self,
        query: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Any:
        """搜索和列出市场中的公开插件
        
        API: GET /api/v1/plugins
        
        Args:
            query: 搜索关键词（匹配插件名称、描述等）
            category: 按分类筛选
            tag: 按标签筛选
            limit: 返回结果数量限制（1-100，默认 50）
            offset: 分页偏移量（默认 0）
            
        Returns:
            dict: 分页结果，包含 items (插件列表) 和 total (总数) 字段
        """
        params = {"limit": str(limit), "offset": str(offset)}
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag

        return await self._request(
            "GET", "/api/v1/plugins", params=params, authenticated=False
        )

    async def get_plugin_detail(self, plugin_id: str) -> Any:
        """获取插件的完整详情信息
        
        API: GET /api/v1/plugins/{plugin_id}
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            dict: 插件详情 (Plugin schema)，包含元数据、统计信息等
        """
        return await self._request(
            "GET", f"/api/v1/plugins/{plugin_id}", authenticated=False
        )

    async def get_plugin_versions(self, plugin_id: str) -> Any:
        """获取插件的所有版本列表
        
        API: GET /api/v1/plugins/{plugin_id}/versions
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            dict: 版本列表响应，包含 items (版本列表) 和 total (总数) 字段
        """
        return await self._request(
            "GET", f"/api/v1/plugins/{plugin_id}/versions", authenticated=False
        )

    async def get_version(self, plugin_id: str, version: str) -> Any:
        """获取插件的指定版本详情
        
        API: GET /api/v1/plugins/{plugin_id}/versions/{version}
        
        Args:
            plugin_id: 插件唯一标识符
            version: 版本号（如 "1.0.0"）
            
        Returns:
            dict: 版本信息 (PluginVersion schema)，包含下载链接等详细信息
            
        Raises:
            MarketError: 版本不存在或获取失败
        """
        return await self._request(
            "GET", f"/api/v1/plugins/{plugin_id}/versions/{version}", authenticated=False
        )

    async def get_recommended_version(
        self,
        plugin_id: str,
        host_version: str | None = None,
        plugin_api_version: str | None = None,
        platform: str | None = None,
        include_prerelease: bool = False,
    ) -> Any:
        """根据兼容性条件获取推荐安装的插件版本
        
        API: GET /api/v1/plugins/{plugin_id}/recommended-version
        
        Args:
            plugin_id: 插件唯一标识符
            host_version: Neo-MoFox 宿主程序版本号
            plugin_api_version: 插件 API 版本号
            platform: 运行平台（如 linux, windows, darwin）
            include_prerelease: 是否包含预发布版本（默认 false）
            
        Returns:
            dict: 推荐的版本信息 (PluginVersion schema)
        """
        params = self._build_compat_params(
            host_version, plugin_api_version, platform, include_prerelease
        )
        return await self._request(
            "GET",
            f"/api/v1/plugins/{plugin_id}/recommended-version",
            params=params,
            authenticated=False,
        )

    async def get_install_info(
        self,
        plugin_id: str,
        host_version: str | None = None,
        plugin_api_version: str | None = None,
        platform: str | None = None,
        include_prerelease: bool = False,
    ) -> Any:
        """获取用于安装的插件和版本元数据（客户端和 CLI 使用）
        
        API: GET /api/v1/plugins/{plugin_id}/install
        
        Args:
            plugin_id: 插件唯一标识符
            host_version: Neo-MoFox 宿主程序版本号
            plugin_api_version: 插件 API 版本号
            platform: 运行平台（如 linux, windows, darwin）
            include_prerelease: 是否包含预发布版本（默认 false）
            
        Returns:
            dict: 安装信息 (InstallInfo schema)，包含 plugin 和 version 字段
        """
        params = self._build_compat_params(
            host_version, plugin_api_version, platform, include_prerelease
        )
        return await self._request(
            "GET",
            f"/api/v1/plugins/{plugin_id}/install",
            params=params,
            authenticated=False,
        )

    @staticmethod
    def _build_compat_params(
        host_version: str | None,
        plugin_api_version: str | None,
        platform: str | None,
        include_prerelease: bool,
    ) -> dict[str, str]:
        """构建兼容性查询参数"""
        params: dict[str, str] = {
            "include_prerelease": str(include_prerelease).lower()
        }
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
        """发送 API 请求
        
        Args:
            method: HTTP 方法
            path: 请求路径
            json: JSON 数据
            params: URL 参数
            authenticated: 是否需要认证
            
        Returns:
            响应数据
            
        Raises:
            MarketError: API 请求失败
        """
        headers = {"Authorization": f"Bearer {self.token}"} if authenticated else None
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method,
                f"{self.base_url}{path}",
                json=json,
                params=params,
                headers=headers,
            ) as response:
                try:
                    data = await response.json(content_type=None)
                except Exception:
                    data = {}

                if response.status >= 400:
                    error = data.get("error", {}) if isinstance(data, dict) else {}
                    code = error.get("code", f"HTTP_{response.status}")
                    message = error.get("message", "市场请求失败")
                    raise MarketError(f"{code}: {message}")

                if not isinstance(data, (dict, list)):
                    raise MarketError("无效的市场响应格式")

                return data

"""
PyPI 包管理器
处理与 PyPI/镜像源的交互
"""

from __future__ import annotations

from typing import Any

import aiohttp

from mpdt.utils.managers.config_manager import get_or_init_mpdt_config


class PyPIError(RuntimeError):
    """PyPI API 错误"""


class PyPIManager:
    """PyPI 统一管理器
    
    提供与 PyPI 和镜像源的交互功能：
    - 搜索 Python 包
    - 获取包的详细信息
    - 获取包的可用版本列表
    - 提供 PyPI 包页面链接
    """

    # 默认 PyPI 源
    DEFAULT_INDEX_URL = "https://pypi.org"
    DEFAULT_JSON_API = "https://pypi.org/pypi"

    def __init__(self, index_url: str | None = None, timeout: int = 30):
        """初始化 PyPI 管理器
        
        Args:
            index_url: PyPI 镜像源 URL，不提供则从配置读取或使用默认值
            timeout: 请求超时时间（秒）
        """
        self.index_url = self._resolve_index_url(index_url)
        # JSON API 通常使用主站的 API
        if self.index_url != self.DEFAULT_INDEX_URL:
            # 对于镜像源，尝试使用其 JSON API（如果支持）
            self.json_api = f"{self.index_url}/pypi"
        else:
            self.json_api = self.DEFAULT_JSON_API
        self.timeout = timeout

    @classmethod
    def _resolve_index_url(cls, index_url: str | None) -> str:
        """解析 PyPI 镜像源 URL"""
        if index_url:
            return index_url.rstrip("/")
        
        config = get_or_init_mpdt_config()
        return config.pypi_index_url

    async def search_packages(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """搜索 Python 包
        
        注意：PyPI 已废弃了官方搜索 API，这里使用第三方搜索服务
        
        Args:
            query: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            list: 包信息列表
        """
        # 使用 PyPI 的 JSON API + 简单过滤（不够完善，但可用）
        # 实际生产中可能需要使用专门的搜索服务
        
        # 这里我们直接尝试获取包信息，如果存在则返回
        try:
            package_info = await self.get_package_info(query)
            if package_info:
                return [{
                    "name": package_info["info"]["name"],
                    "version": package_info["info"]["version"],
                    "summary": package_info["info"]["summary"],
                    "author": package_info["info"].get("author", ""),
                    "project_url": package_info["info"]["project_url"],
                }]
        except PyPIError:
            pass
        
        return []

    async def get_package_info(self, package_name: str) -> dict[str, Any]:
        """获取包的详细信息
        
        API: GET /pypi/{package_name}/json
        
        Args:
            package_name: 包名称
            
        Returns:
            dict: 包的详细信息
            
        Raises:
            PyPIError: 包不存在或请求失败
        """
        url = f"{self.json_api}/{package_name}/json"
        return await self._request("GET", url)

    async def get_package_versions(self, package_name: str) -> list[str]:
        """获取包的所有可用版本
        
        Args:
            package_name: 包名称
            
        Returns:
            list: 版本号列表（从旧到新排序）
            
        Raises:
            PyPIError: 包不存在或请求失败
        """
        package_info = await self.get_package_info(package_name)
        releases = package_info.get("releases", {})
        # 过滤掉没有文件的版本（可能是被删除的版本）
        return [
            version for version, files in releases.items()
            if files  # 只保留有文件的版本
        ]

    async def get_latest_version(self, package_name: str) -> str:
        """获取包的最新版本
        
        Args:
            package_name: 包名称
            
        Returns:
            str: 最新版本号
            
        Raises:
            PyPIError: 包不存在或请求失败
        """
        package_info = await self.get_package_info(package_name)
        return package_info["info"]["version"]

    def get_package_url(self, package_name: str) -> str:
        """获取包在 PyPI 上的页面链接
        
        Args:
            package_name: 包名称
            
        Returns:
            str: PyPI 包页面 URL
        """
        # 始终返回 PyPI.org 的链接（镜像源可能没有 web 界面）
        return f"https://pypi.org/project/{package_name}/"

    async def _request(
        self,
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """发送 HTTP 请求
        
        Args:
            method: HTTP 方法
            url: 完整 URL
            json: JSON 数据
            params: URL 参数
            
        Returns:
            响应数据
            
        Raises:
            PyPIError: 请求失败
        """
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method,
                url,
                json=json,
                params=params,
            ) as response:
                if response.status == 404:
                    raise PyPIError("包不存在")
                
                if response.status >= 400:
                    raise PyPIError(f"HTTP {response.status}: PyPI 请求失败")

                try:
                    data = await response.json(content_type=None)
                except Exception as e:
                    raise PyPIError(f"无效的响应格式: {e}")

                if not isinstance(data, dict):
                    raise PyPIError("无效的 PyPI 响应格式")

                return data

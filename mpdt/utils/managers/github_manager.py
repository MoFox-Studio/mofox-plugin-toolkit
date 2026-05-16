"""
GitHub 管理器
处理 GitHub API 相关操作
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import aiohttp


class GitHubError(RuntimeError):
    """GitHub API 错误"""


class GitHubManager:
    """GitHub 统一管理器
    
    提供 GitHub API 相关操作：
    - 仓库管理
    - Release 管理
    - 资产上传
    """

    def __init__(self, token: str, timeout: int = 60):
        """初始化 GitHub 管理器
        
        Args:
            token: GitHub Personal Access Token
            timeout: 请求超时时间（秒）
        """
        self.token = token
        self.timeout = timeout
        self._base_url = "https://api.github.com"

    async def get_current_user(self) -> dict[str, Any]:
        """获取当前认证用户信息
        
        Returns:
            用户信息字典
        """
        return await self._request("GET", f"{self._base_url}/user")

    async def get_repo(self, owner: str, repo: str) -> dict[str, Any] | None:
        """获取仓库信息
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            
        Returns:
            仓库信息，不存在则返回 None
        """
        try:
            return await self._request("GET", f"{self._base_url}/repos/{owner}/{repo}")
        except GitHubError as e:
            if "HTTP_404" in str(e):
                return None
            raise

    async def create_repo(
        self,
        owner: str,
        repo: str,
        description: str = "",
        private: bool = False,
    ) -> dict[str, Any]:
        """创建仓库
        
        Args:
            owner: 仓库所有者（用户名或组织名）
            repo: 仓库名称
            description: 仓库描述
            private: 是否为私有仓库
            
        Returns:
            创建的仓库信息
            
        Raises:
            GitHubError: 创建仓库失败（如权限不足、组织不存在等）
        """
        user = await self.get_current_user()
        payload = {
            "name": repo,
            "description": description,
            "private": private,
            "auto_init": False,
        }

        # 判断是用户仓库还是组织仓库
        is_user_repo = owner.lower() == str(user.get("login", "")).lower()
        
        if is_user_repo:
            url = f"{self._base_url}/user/repos"
        else:
            # 组织仓库 - 先检查用户是否有权限
            await self._check_org_membership(owner)
            url = f"{self._base_url}/orgs/{owner}/repos"

        try:
            return await self._request("POST", url, json=payload)
        except GitHubError as e:
            # 提供更友好的错误消息
            if "HTTP_403" in str(e):
                if is_user_repo:
                    raise GitHubError(
                        f"创建仓库失败：权限不足。请检查 GitHub Token 是否有 'repo' 或 'public_repo' 权限。"
                    )
                else:
                    raise GitHubError(
                        f"创建仓库失败：你没有在组织 {owner} 中创建仓库的权限。"
                        "请联系组织管理员授予权限。"
                    )
            elif "HTTP_422" in str(e):
                raise GitHubError(
                    f"创建仓库失败：仓库名称 {repo} 可能已被使用或无效。"
                )
            # 其他错误直接抛出
            raise
    
    async def _check_org_membership(self, org: str) -> None:
        """检查当前用户是否是组织成员
        
        Args:
            org: 组织名称
            
        Raises:
            GitHubError: 如果不是组织成员或组织不存在
        """
        try:
            user = await self.get_current_user()
            username = user.get("login")
            await self._request(
                "GET",
                f"{self._base_url}/orgs/{org}/members/{username}"
            )
        except GitHubError as e:
            if "HTTP_404" in str(e):
                raise GitHubError(
                    f"组织 {org} 不存在，或你不是该组织的成员。"
                    "请检查组织名称是否正确。"
                )
            raise

    async def ensure_repo(
        self,
        owner: str,
        repo: str,
        description: str = "",
        private: bool = False,
    ) -> dict[str, Any]:
        """确保仓库存在，不存在则创建
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            description: 仓库描述
            private: 是否为私有仓库
            
        Returns:
            仓库信息
            
        Raises:
            GitHubError: 仓库存在但没有写入权限
        """
        existing = await self.get_repo(owner, repo)
        if existing:
            # 检查仓库权限
            if not self._has_push_permission(existing):
                raise GitHubError(
                    f"仓库 {owner}/{repo} 已存在但当前用户没有写入权限。"
                    "请确保你有该仓库的 push 权限，或使用不同的仓库名称。"
                )
            return existing
        return await self.create_repo(owner, repo, description, private)
    
    def _has_push_permission(self, repo: dict[str, Any]) -> bool:
        """检查是否有仓库的 push 权限
        
        Args:
            repo: 仓库信息字典
            
        Returns:
            是否有 push 权限
        """
        permissions = repo.get("permissions")
        if permissions is None:
            # 如果没有 permissions 字段，说明没有权限信息
            return False
        # 需要 push 或 admin 权限
        return bool(permissions.get("push") or permissions.get("admin"))

    async def get_release_by_tag(
        self, owner: str, repo: str, tag: str
    ) -> dict[str, Any] | None:
        """根据 tag 获取 Release
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            tag: Release 标签
            
        Returns:
            Release 信息，不存在则返回 None
        """
        try:
            return await self._request(
                "GET", f"{self._base_url}/repos/{owner}/{repo}/releases/tags/{tag}"
            )
        except GitHubError as e:
            if "HTTP_404" in str(e):
                return None
            raise

    async def create_release(
        self,
        owner: str,
        repo: str,
        tag: str,
        title: str,
        body: str = "",
        prerelease: bool = False,
    ) -> dict[str, Any]:
        """创建 Release
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            tag: Release 标签
            title: Release 标题
            body: Release 说明
            prerelease: 是否为预发布版本
            
        Returns:
            创建的 Release 信息
        """
        payload = {
            "tag_name": tag,
            "name": title,
            "body": body,
            "draft": False,
            "prerelease": prerelease,
        }
        return await self._request(
            "POST", f"{self._base_url}/repos/{owner}/{repo}/releases", json=payload
        )

    async def ensure_release(
        self,
        owner: str,
        repo: str,
        tag: str,
        title: str,
        body: str = "",
        prerelease: bool = False,
    ) -> dict[str, Any]:
        """确保 Release 存在，不存在则创建
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            tag: Release 标签
            title: Release 标题
            body: Release 说明
            prerelease: 是否为预发布版本
            
        Returns:
            Release 信息
        """
        existing = await self.get_release_by_tag(owner, repo, tag)
        if existing:
            return existing
        return await self.create_release(owner, repo, tag, title, body, prerelease)

    async def upload_asset(
        self, release: dict[str, Any], asset_path: Path, replace: bool = True
    ) -> dict[str, Any]:
        """上传 Release 资产
        
        Args:
            release: Release 信息
            asset_path: 资产文件路径
            replace: 如果资产已存在是否替换
            
        Returns:
            上传的资产信息
        """
        assets = release.get("assets", [])
        
        # 检查是否已存在同名资产
        for asset in assets:
            if asset.get("name") == asset_path.name:
                if not replace:
                    return asset
                # 删除旧资产
                await self._request("DELETE", str(asset["url"]), expect_json=False)
                break

        # 上传新资产
        upload_url = str(release["upload_url"]).split("{", 1)[0]
        headers = {"Content-Type": "application/octet-stream"}
        params = {"name": asset_path.name}
        data = asset_path.read_bytes()

        return await self._request(
            "POST", upload_url, params=params, data=data, headers=headers
        )

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
        """发送 GitHub API 请求
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            json: JSON 数据
            params: URL 参数
            data: 二进制数据
            headers: 额外的请求头
            expect_json: 是否期望 JSON 响应
            
        Returns:
            响应数据
            
        Raises:
            GitHubError: API 请求失败
        """
        request_headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            **(headers or {}),
        }

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(
            timeout=timeout, headers=request_headers
        ) as session:
            async with session.request(
                method, url, json=json, params=params, data=data
            ) as response:
                if response.status == 204 and not expect_json:
                    return {}

                try:
                    payload = await response.json(content_type=None)
                except Exception:
                    payload = {}

                if response.status >= 400:
                    message = (
                        payload.get("message", "GitHub 请求失败")
                        if isinstance(payload, dict)
                        else "GitHub 请求失败"
                    )
                    raise GitHubError(f"HTTP_{response.status}: {message}")

                if not isinstance(payload, dict):
                    raise GitHubError("无效的 GitHub 响应格式")

                return payload

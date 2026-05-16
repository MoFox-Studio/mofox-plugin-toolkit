"""
GitHub 管理器
处理 GitHub API 相关操作
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast, overload

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

    async def check_permissions(
        self,
        owner: str,
        repo: str,
        need_push: bool = True,
        need_release: bool = True,
    ) -> dict[str, Any]:
        """统一权限检查
        
        在开始 GitHub 操作前检查所有需要的权限。
        不抛出异常，只返回权限状态，由调用方自行处理。
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            need_push: 是否检查 push 权限
            need_release: 是否检查 release 权限
            
        Returns:
            权限检查结果字典，包含：
            - repo_exists: 仓库是否存在
            - is_user_repo: 是否是用户仓库（而非组织仓库）
            - repo_info: 仓库信息（如果存在，否则为 None）
            - can_push: 是否有 push 权限
            - can_create_release: 是否有创建 release 权限
            - can_create_repo: 是否可以创建仓库
            
            如果检查过程出现异常，返回空字典 {}
        """
        try:
            user = await self.get_current_user()
            username = user.get("login", "")
            is_user_repo = owner.lower() == username.lower()
            
            # 1. 检查仓库是否存在
            repo_info = await self.get_repo(owner, repo)
            
            if repo_info:
                # 仓库存在 - 检查权限
                permissions = repo_info.get("permissions")
                
                # 检查 push 权限
                can_push = False
                if need_push and permissions is not None:
                    can_push = bool(permissions.get("push") or permissions.get("admin"))
                
                # 检查 release 权限（通过尝试列出 releases 来验证）
                can_create_release = False
                if need_release:
                    try:
                        await self._request(
                            "GET",
                            f"{self._base_url}/repos/{owner}/{repo}/releases",
                            params={"per_page": "1"},
                        )
                        can_create_release = True
                    except GitHubError as e:
                        if "HTTP_403" not in str(e):
                            # 其他错误可以忽略（如 404 表示没有 releases，但这是正常的）
                            can_create_release = True
                
                return {
                    "repo_exists": True,
                    "is_user_repo": is_user_repo,
                    "repo_info": repo_info,
                    "can_push": can_push,
                    "can_create_release": can_create_release,
                    "can_create_repo": False,
                }
            else:
                # 仓库不存在 - 检查是否有创建权限
                can_create_repo = True  # 默认可以创建
                
                if not is_user_repo:
                    # 组织仓库 - 检查组织成员身份和权限
                    try:
                        await self._request(
                            "GET",
                            f"{self._base_url}/orgs/{owner}/members/{username}"
                        )
                    except GitHubError as e:
                        if "HTTP_404" in str(e):
                            # 不是组织成员，无法创建
                            can_create_repo = False
                            return {
                                "repo_exists": False,
                                "is_user_repo": is_user_repo,
                                "repo_info": None,
                                "can_push": False,
                                "can_create_release": False,
                                "can_create_repo": can_create_repo,
                            }
                        # 其他错误继续
                    
                    # 检查在组织中创建仓库的权限（通过检查用户在组织中的角色）
                    try:
                        result = await self._request(
                            "GET",
                            f"{self._base_url}/orgs/{owner}/memberships/{username}",
                            return_headers=True,
                        )
                        membership = cast(tuple[dict[str, Any], dict[str, str]], result)[0]
                        role = membership.get("role")
                        # admin 可以创建仓库，member 需要组织设置允许
                        if role != "admin":
                            # 获取组织设置
                            result2 = await self._request(
                                "GET",
                                f"{self._base_url}/orgs/{owner}",
                                return_headers=True,
                            )
                            org_info = cast(tuple[dict[str, Any], dict[str, str]], result2)[0]
                            members_can_create = org_info.get("members_can_create_repositories", False)
                            can_create_repo = members_can_create
                    except GitHubError as e:
                        if "HTTP_403" in str(e) or "HTTP_404" in str(e):
                            # 无法验证权限，标记为不能创建
                            can_create_repo = False
                
                # 用户仓库或已验证组织权限 - 检查 token 是否有创建仓库的权限
                if can_create_repo:
                    try:
                        # 获取 token 的 scopes 信息
                        result = await self._request(
                            "GET",
                            f"{self._base_url}/user",
                            expect_json=True,
                            return_headers=True,
                        )
                        response_headers = cast(tuple[dict[str, Any], dict[str, str]], result)[1]
                        
                        # 解析 X-OAuth-Scopes 头
                        scopes_header = response_headers.get("X-OAuth-Scopes", "")
                        scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
                        
                        # 检查是否有仓库相关权限
                        has_repo_permission = any(
                            scope in scopes
                            for scope in ["repo", "public_repo"]
                        )
                        
                        if not has_repo_permission:
                            can_create_repo = False
                    except Exception:
                        # 无法验证 token 权限，标记为不能创建
                        can_create_repo = False
                
                return {
                    "repo_exists": False,
                    "is_user_repo": is_user_repo,
                    "repo_info": None,
                    "can_push": False,
                    "can_create_release": False,
                    "can_create_repo": can_create_repo,
                }
        except Exception:
            # 顶层异常处理：任何未捕获的异常都返回空字典
            return {}

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
        is_user_repo: bool | None = None,
    ) -> dict[str, Any]:
        """创建仓库
        
        注意：调用此方法前应先调用 check_permissions 验证权限。
        
        Args:
            owner: 仓库所有者（用户名或组织名）
            repo: 仓库名称
            description: 仓库描述
            private: 是否为私有仓库
            is_user_repo: 是否是用户仓库（可选，如不提供则自动判断）
            
        Returns:
            创建的仓库信息
            
        Raises:
            GitHubError: 创建仓库失败
        """
        if is_user_repo is None:
            user = await self.get_current_user()
            is_user_repo = owner.lower() == str(user.get("login", "")).lower()
        
        payload = {
            "name": repo,
            "description": description,
            "private": private,
            "auto_init": False,
        }

        url = (
            f"{self._base_url}/user/repos"
            if is_user_repo
            else f"{self._base_url}/orgs/{owner}/repos"
        )

        try:
            return await self._request("POST", url, json=payload)
        except GitHubError as e:
            if "HTTP_422" in str(e):
                raise GitHubError(
                    f"创建仓库失败：仓库名称 {repo} 可能已被使用或无效。"
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
        
        注意：调用此方法前应先调用 check_permissions 验证权限，
        并将结果传入 permission_check_result 参数以避免重复检查。
        
        Args:
            owner: 仓库所有者
            repo: 仓库名称
            description: 仓库描述
            private: 是否为私有仓库
            
        Returns:
            仓库信息
            
        Raises:
            GitHubError: 创建仓库失败
        """
        existing = await self.get_repo(owner, repo)
        if existing:
            return existing
        return await self.create_repo(owner, repo, description, private)

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

    @overload
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
        return_headers: bool = False,
    ) -> dict[str, Any]:
        ...

    @overload
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
        return_headers: bool = True,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        ...

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
        return_headers: bool = False,
    ) -> dict[str, Any] | tuple[dict[str, Any], dict[str, str]]:
        """发送 GitHub API 请求
        
        Args:
            method: HTTP 方法
            url: 请求 URL
            json: JSON 数据
            params: URL 参数
            data: 二进制数据
            headers: 额外的请求头
            expect_json: 是否期望 JSON 响应
            return_headers: 是否返回响应头
            
        Returns:
            响应数据，如果 return_headers=True 则返回 (响应数据, 响应头) 元组
            
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
                # 保存响应头
                response_headers = dict(response.headers)
                
                if response.status == 204 and not expect_json:
                    result = {}
                    return (result, response_headers) if return_headers else result

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

                return (payload, response_headers) if return_headers else payload

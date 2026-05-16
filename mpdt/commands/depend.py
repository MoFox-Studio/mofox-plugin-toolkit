"""
依赖管理命令
处理插件依赖和 Python 包依赖的添加、搜索、下载等操作
"""

import asyncio
from pathlib import Path

from mpdt.utils.color_printer import (
    print_error,
    print_info,
    print_success,
    print_warning,
)
from mpdt.utils.managers.config_manager import get_or_init_mpdt_config
from mpdt.utils.managers.manifest_manager import ManifestManager
from mpdt.utils.managers.market_manager import MarketError, MarketManager
from mpdt.utils.managers.pypi_manager import PyPIError, PyPIManager


def _run_async(coro):
    """运行异步协程"""
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def depend_add(
    plugin_path: str,
    dependency: str,
    dep_type: str = "auto",
) -> None:
    """添加依赖到插件
    
    Args:
        plugin_path: 插件根目录
        dependency: 依赖规范（如 "requests>=2.28.0" 或 "plugin-name>=1.0.0"）
        dep_type: 依赖类型（plugin/python/auto）
    """
    
    async def run() -> None:
        nonlocal dep_type
        
        plugin_dir = Path(plugin_path).resolve()
        manifest_mgr = ManifestManager(plugin_dir)
        
        if not manifest_mgr.exists:
            print_error(f"未找到 manifest.json: {plugin_dir}")
            return
        
        manifest_mgr.load()
        
        # 从依赖规范中提取包名（用于类型判断）
        dependency_name = manifest_mgr._parse_dependency_name(dependency)
        
        # 自动判断依赖类型
        if dep_type == "auto":
            # 先尝试作为插件
            print_info(f"正在检查 '{dependency_name}' 是否为插件...")
            market = MarketManager()
            try:
                plugin_info = await market.get_plugin_detail(dependency_name)
                dep_type = "plugin"
                print_success(f"找到插件: {plugin_info.get('display_name', plugin_info.get('plugin_id', dependency_name))}")
            except MarketError:
                # 尝试作为 Python 包
                print_info(f"未找到插件，检查是否为 Python 包...")
                pypi = PyPIManager()
                try:
                    package_info = await pypi.get_package_info(dependency_name)
                    dep_type = "python"
                    print_success(f"找到 Python 包: {package_info['info']['name']}")
                except PyPIError:
                    print_error(f"未找到插件或 Python 包: {dependency_name}")
                    return
        
        # 处理插件依赖
        if dep_type == "plugin":
            print_info(f"正在添加插件依赖: {dependency}")
            
            # 添加到 manifest
            if manifest_mgr.add_plugin_dependency(dependency):
                print_success(f"已添加插件依赖到 manifest: {dependency}")
            else:
                print_warning(f"插件依赖已存在: {dependency_name}")
                return
            
            # 下载插件到 Neo-MoFox
            config = get_or_init_mpdt_config()
            if not config.mofox_path or not config.mofox_path.exists():
                print_warning("未配置 Neo-MoFox 路径，跳过插件下载")
                print_info("使用 'mpdt config set-mofox <path>' 配置路径")
                return
            
            plugins_dir = config.mofox_path / "plugins"
            if not plugins_dir.exists():
                print_error(f"Neo-MoFox 插件目录不存在: {plugins_dir}")
                return
            
            print_info(f"正在下载插件到 {plugins_dir}...")
            
            # 解析依赖规范以获取版本信息
            market = MarketManager()
            try:
                # 从依赖规范中解析版本约束
                version_info = None
                if dependency != dependency_name:
                    # 如果依赖规范包含版本约束，解析操作符和版本号
                    # 支持格式：plugin-name==1.0.0, plugin-name>=1.0.0, plugin-name>1.0.0 等
                    import re
                    from packaging import version as pkg_version
                    
                    match = re.search(r'([=><~!]+)([0-9.]+(?:[a-zA-Z0-9\-]+)?)', dependency)
                    if match:
                        operator = match.group(1)
                        version_str = match.group(2)
                        
                        if operator == "==":
                            # 精确匹配，直接获取指定版本
                            print_info(f"获取指定版本: {version_str}")
                            version_info = await market.get_version(dependency_name, version_str)
                        else:
                            # 范围匹配，获取所有版本并筛选
                            print_info(f"查找满足 {operator}{version_str} 条件的版本...")
                            versions_response = await market.get_plugin_versions(dependency_name)
                            all_versions = versions_response.get("items", [])
                            
                            # 筛选符合条件的版本
                            target_version = pkg_version.parse(version_str)
                            matching_versions = []
                            
                            for v in all_versions:
                                v_str = v.get("version")
                                if not v_str:
                                    continue
                                try:
                                    v_parsed = pkg_version.parse(v_str)
                                    # 检查版本状态，排除被撤回或阻止的版本
                                    if v.get("is_yanked") or v.get("status") == "blocked":
                                        continue
                                    
                                    # 根据操作符判断
                                    if operator == ">=" and v_parsed >= target_version:
                                        matching_versions.append((v_parsed, v))
                                    elif operator == ">" and v_parsed > target_version:
                                        matching_versions.append((v_parsed, v))
                                    elif operator == "<=" and v_parsed <= target_version:
                                        matching_versions.append((v_parsed, v))
                                    elif operator == "<" and v_parsed < target_version:
                                        matching_versions.append((v_parsed, v))
                                    elif operator == "~=" and v_parsed.major == target_version.major and v_parsed >= target_version:
                                        matching_versions.append((v_parsed, v))
                                except Exception:
                                    continue
                            
                            if matching_versions:
                                # 选择最新的符合条件的版本
                                matching_versions.sort(key=lambda x: x[0], reverse=True)
                                selected_version = matching_versions[0][1]
                                selected_version_str = selected_version.get("version")
                                print_success(f"找到符合条件的版本: {selected_version_str}")
                                version_info = selected_version
                            else:
                                print_error(f"未找到满足 {operator}{version_str} 条件的版本")
                                return
                
                if not version_info:
                    # 如果没有指定版本约束，获取推荐版本
                    print_info("获取推荐版本...")
                    install_info = await market.get_install_info(dependency_name)
                    version_info = install_info.get("version", {})
                
                asset_url = version_info.get("asset_download_url")
                
                if not asset_url:
                    print_error("无法获取插件下载地址")
                    return
                
                # 下载插件包
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(asset_url) as response:
                        if response.status != 200:
                            print_error(f"下载失败: HTTP {response.status}")
                            return
                        
                        # 保存到临时文件
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix=".mfp", delete=False) as tmp_file:
                            tmp_file.write(await response.read())
                            tmp_path = Path(tmp_file.name)
                        
                        # 解压到插件目录
                        import zipfile
                        target_dir = plugins_dir / dependency_name
                        target_dir.mkdir(parents=True, exist_ok=True)
                        
                        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                            zip_ref.extractall(target_dir)
                        
                        tmp_path.unlink()  # 删除临时文件
                        
                        print_success(f"插件已下载到: {target_dir}")
                
            except MarketError as e:
                print_error(f"获取插件安装信息失败: {e}")
                return
        
        # 处理 Python 包依赖
        elif dep_type == "python":
            print_info(f"正在添加 Python 包依赖: {dependency}")
            
            # 添加到 manifest
            if manifest_mgr.add_python_dependency(dependency):
                print_success(f"已添加 Python 包依赖到 manifest: {dependency}")
            else:
                print_warning(f"Python 包依赖已存在: {dependency_name}")
                return
            
            # 使用 uv 安装包
            config = get_or_init_mpdt_config()
            if not config.mofox_path or not config.mofox_path.exists():
                print_warning("未配置 Neo-MoFox 路径，跳过包安装")
                print_info("使用 'mpdt config set-mofox <path>' 配置路径")
                return
            
            # 检查是否存在 .venv
            venv_path = config.mofox_path / ".venv"
            if not venv_path.exists():
                print_warning(f"虚拟环境不存在: {venv_path}")
                print_info("请先在 Neo-MoFox 目录创建虚拟环境")
                return
            
            print_info(f"正在使用 uv 安装 Python 包: {dependency}")
            
            import subprocess
            pypi_index = config.pypi_index_url
            
            try:
                # 使用 uv pip install
                result = subprocess.run(
                    [
                        "uv", "pip", "install",
                        "--index-url", f"{pypi_index}/simple",
                        "--python", str(venv_path / "bin" / "python"),
                        dependency
                    ],
                    cwd=config.mofox_path,
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    print_success(f"Python 包安装成功: {dependency}")
                else:
                    print_error(f"Python 包安装失败: {result.stderr}")
                    
            except FileNotFoundError:
                print_error("未找到 uv 命令，请先安装 uv: pip install uv")
            except Exception as e:
                print_error(f"执行安装命令失败: {e}")
        
        else:
            print_error(f"未知的依赖类型: {dep_type}")
            return
    
    _run_async(run())


def depend_search(
    query: str,
    dep_type: str = "all",
    limit: int = 20,
) -> None:
    """搜索依赖（插件或 Python 包）
    
    Args:
        query: 搜索关键词
        dep_type: 搜索类型（plugin/python/all）
        limit: 返回结果数量
    """
    
    async def run() -> None:
        from rich.table import Table
        from mpdt.utils.color_printer import console
        
        found_results = False
        
        # 搜索插件
        plugins = []
        if dep_type in ("plugin", "all"):
            if dep_type == "plugin":
                print_info("正在搜索插件...")
            market = MarketManager()
            try:
                result = await market.search_plugins(query=query, limit=limit)
                plugins = result.get("items", [])
                
                if plugins:
                    found_results = True
                    table = Table(title=f"插件搜索结果 ({len(plugins)} 个)")
                    table.add_column("ID", style="cyan")
                    table.add_column("名称", style="green")
                    table.add_column("版本", style="yellow")
                    table.add_column("描述", style="white")
                    table.add_column("链接", style="blue")
                    
                    for plugin in plugins:
                        plugin_id = plugin.get("plugin_id", "")
                        name = plugin.get("display_name", "")
                        version = plugin.get("latest_version", {}).get("version", "N/A")
                        summary = plugin.get("summary", "")
                        link = f"https://market.mofox-sama.com/plugins/{plugin_id}"
                        
                        table.add_row(plugin_id, name, version, summary, link)
                    
                    console.print(table)
                    
            except MarketError as e:
                if dep_type == "plugin":
                    print_error(f"搜索插件失败: {e}")
        
        # 搜索 Python 包
        package_info = None
        if dep_type in ("python", "all"):
            if dep_type == "python":
                print_info("正在搜索 Python 包...")
            pypi = PyPIManager()
            try:
                # PyPI 搜索功能有限，尝试直接获取包信息
                package_info = await pypi.get_package_info(query)
                
                if package_info:
                    found_results = True
                    table = Table(title="Python 包搜索结果")
                    table.add_column("包名", style="cyan")
                    table.add_column("版本", style="yellow")
                    table.add_column("描述", style="white")
                    table.add_column("作者", style="green")
                    table.add_column("链接", style="blue")
                    
                    info = package_info["info"]
                    table.add_row(
                        info["name"],
                        info["version"],
                        info.get("summary", ""),
                        info.get("author", ""),
                        pypi.get_package_url(info["name"])
                    )
                    
                    console.print(table)
                
            except PyPIError:
                if dep_type == "python":
                    print_info(f"未找到 Python 包: {query}")
        
        # 如果是 all 模式且两个都没找到，显示提示
        if dep_type == "all" and not found_results:
            print_info(f"未找到匹配的插件或 Python 包: {query}")
    
    _run_async(run())


def depend_info(
    dependency: str,
    dep_type: str = "auto",
) -> None:
    """获取依赖的详细信息和可用版本
    
    Args:
        dependency: 依赖名称
        dep_type: 依赖类型（plugin/python/auto）
    """
    
    async def run() -> None:
        nonlocal dep_type
        
        from rich.panel import Panel
        from rich.table import Table
        from mpdt.utils.color_printer import console
        
        # 自动判断类型
        if dep_type == "auto":
            market = MarketManager()
            try:
                await market.get_plugin_detail(dependency)
                dep_type = "plugin"
            except MarketError:
                dep_type = "python"
        
        # 获取插件信息
        if dep_type == "plugin":
            print_info(f"正在获取插件信息: {dependency}")
            market = MarketManager()
            try:
                plugin_info = await market.get_plugin_detail(dependency)
                versions_response = await market.get_plugin_versions(dependency)
                
                # 显示基本信息
                info_text = f"""
[bold cyan]插件 ID:[/bold cyan] {plugin_info.get('plugin_id', '')}
[bold cyan]名称:[/bold cyan] {plugin_info.get('display_name', '')}
[bold cyan]描述:[/bold cyan] {plugin_info.get('summary', '')}
[bold cyan]作者:[/bold cyan] {plugin_info.get('owner_display_name', plugin_info.get('owner_login', ''))}
[bold cyan]状态:[/bold cyan] {plugin_info.get('status', '')}
[bold cyan]分类:[/bold cyan] {', '.join(plugin_info.get('categories', []))}
[bold cyan]标签:[/bold cyan] {', '.join(plugin_info.get('tags', []))}
[bold cyan]仓库:[/bold cyan] {plugin_info.get('repository_url', '')}
[bold cyan]链接:[/bold cyan] https://market.mofox-sama.com/plugins/{dependency}
                """.strip()
                
                console.print(Panel(info_text, title="插件信息"))
                
                # 显示可用版本
                versions = versions_response.get("items", [])
                if versions:
                    table = Table(title=f"可用版本 ({len(versions)} 个)")
                    table.add_column("版本", style="yellow")
                    table.add_column("状态", style="green")
                    table.add_column("发布时间", style="cyan")
                    
                    for ver in versions:
                        table.add_row(
                            ver.get("version", ""),
                            ver.get("status", ""),
                            ver.get("published_at", "")[:10] if ver.get("published_at") else ""
                        )
                    
                    console.print(table)
                    
            except MarketError as e:
                print_error(f"获取插件信息失败: {e}")
        
        # 获取 Python 包信息
        elif dep_type == "python":
            print_info(f"正在获取 Python 包信息: {dependency}")
            pypi = PyPIManager()
            try:
                package_info = await pypi.get_package_info(dependency)
                versions = await pypi.get_package_versions(dependency)
                
                info = package_info["info"]
                
                # 显示基本信息
                info_text = f"""
[bold cyan]包名:[/bold cyan] {info['name']}
[bold cyan]版本:[/bold cyan] {info['version']}
[bold cyan]描述:[/bold cyan] {info.get('summary', '')}
[bold cyan]作者:[/bold cyan] {info.get('author', '')}
[bold cyan]许可证:[/bold cyan] {info.get('license', '')}
[bold cyan]主页:[/bold cyan] {info.get('home_page', '')}
[bold cyan]PyPI:[/bold cyan] {pypi.get_package_url(info['name'])}
                """.strip()
                
                console.print(Panel(info_text, title="Python 包信息"))
                
                # 显示最近的版本
                if versions:
                    recent_versions = versions[-10:]  # 最近 10 个版本
                    table = Table(title=f"可用版本（显示最近 {len(recent_versions)} 个，共 {len(versions)} 个）")
                    table.add_column("版本", style="yellow")
                    
                    for ver in reversed(recent_versions):
                        table.add_row(ver)
                    
                    console.print(table)
                    
            except PyPIError as e:
                print_error(f"获取 Python 包信息失败: {e}")
    
    _run_async(run())


def depend_remove(
    plugin_path: str,
    dependency: str,
    dep_type: str = "auto",
) -> None:
    """从插件中移除依赖
    
    Args:
        plugin_path: 插件根目录
        dependency: 依赖名称
        dep_type: 依赖类型（plugin/python/auto）
    """
    plugin_dir = Path(plugin_path).resolve()
    manifest_mgr = ManifestManager(plugin_dir)
    
    if not manifest_mgr.exists:
        print_error(f"未找到 manifest.json: {plugin_dir}")
        return
    
    manifest_mgr.load()
    
    # 确定依赖类型
    actual_dep_type = dep_type
    if actual_dep_type == "auto":
        # 检查是否在插件依赖中
        plugin_deps = manifest_mgr.get_plugin_dependencies()
        is_plugin = any(
            manifest_mgr._parse_dependency_name(dep).lower() == dependency.lower()
            for dep in plugin_deps
        )
        actual_dep_type = "plugin" if is_plugin else "python"
    
    # 移除依赖
    if actual_dep_type == "plugin":
        if manifest_mgr.remove_plugin_dependency(dependency):
            print_success(f"已从 manifest 移除插件依赖: {dependency}")
            print_warning("注意: 插件文件未自动删除，请手动清理")
        else:
            print_error(f"插件依赖不存在: {dependency}")
    
    elif actual_dep_type == "python":
        if manifest_mgr.remove_python_dependency(dependency):
            print_success(f"已从 manifest 移除 Python 包依赖: {dependency}")
            print_warning("注意: 包未自动卸载，请手动执行 uv pip uninstall")
        else:
            print_error(f"Python 包依赖不存在: {dependency}")


def depend_list(
    plugin_path: str = ".",
    dep_type: str = "all",
) -> None:
    """列出插件的所有依赖
    
    Args:
        plugin_path: 插件根目录
        dep_type: 依赖类型（plugin/python/all）
    """
    plugin_dir = Path(plugin_path).resolve()
    manifest_mgr = ManifestManager(plugin_dir)
    
    if not manifest_mgr.exists:
        print_error(f"未找到 manifest.json: {plugin_dir}")
        return
    
    manifest_mgr.load()
    
    from rich.table import Table
    from mpdt.utils.color_printer import console
    
    # 列出插件依赖
    if dep_type in ("plugin", "all"):
        plugin_deps = manifest_mgr.get_plugin_dependencies()
        if plugin_deps:
            table = Table(title=f"插件依赖 ({len(plugin_deps)} 个)")
            table.add_column("插件 ID", style="cyan")
            
            for dep in plugin_deps:
                table.add_row(dep)
            
            console.print(table)
        else:
            print_info("无插件依赖")
    
    # 列出 Python 包依赖
    if dep_type in ("python", "all"):
        python_deps = manifest_mgr.get_python_dependencies()
        if python_deps:
            table = Table(title=f"Python 包依赖 ({len(python_deps)} 个)")
            table.add_column("包规范", style="yellow")
            
            for dep in python_deps:
                table.add_row(dep)
            
            console.print(table)
        else:
            print_info("无 Python 包依赖")

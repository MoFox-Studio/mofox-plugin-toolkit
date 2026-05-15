"""
Manifest 管理器
统一管理 manifest.json 的所有操作
"""

import json
from pathlib import Path
from typing import Any


class ManifestManager:
    """Manifest.json 统一管理器

    提供对 manifest.json 文件的所有操作，包括：
    - 读取/保存
    - 创建/生成
    - 更新组件
    - 验证
    """

    def __init__(self, plugin_path: Path | str):
        """初始化 Manifest 管理器

        Args:
            plugin_path: 插件目录路径
        """
        self.plugin_path = Path(plugin_path)
        self.manifest_file = self.plugin_path / "manifest.json"
        self._manifest_cache: dict[str, Any] | None = None

    @property
    def exists(self) -> bool:
        """检查 manifest.json 是否存在"""
        return self.manifest_file.exists()

    def load(self, use_cache: bool = True) -> dict[str, Any] | None:
        """读取 manifest.json

        Args:
            use_cache: 是否使用缓存

        Returns:
            manifest 字典，失败返回 None
        """
        if use_cache and self._manifest_cache is not None:
            return self._manifest_cache

        if not self.exists:
            return None

        try:
            with open(self.manifest_file, encoding="utf-8") as f:
                self._manifest_cache = json.load(f)
                return self._manifest_cache
        except json.JSONDecodeError as e:
            raise ValueError(f"manifest.json 解析失败: {e}") from e
        except Exception as e:
            raise OSError(f"读取 manifest.json 失败: {e}") from e

    def save(self, manifest: dict[str, Any] | None = None) -> None:
        """保存 manifest.json

        Args:
            manifest: 要保存的 manifest 字典，为 None 时保存缓存的内容
        """
        if manifest is None:
            if self._manifest_cache is None:
                raise ValueError("没有可保存的 manifest 数据")
            manifest = self._manifest_cache
        else:
            self._manifest_cache = manifest

        self.manifest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=4)

    def create(
        self,
        name: str,
        version: str = "1.0.0",
        description: str = "",
        author: str = "Your Name",
        template: str = "basic",
        **kwargs,
    ) -> dict[str, Any]:
        """创建新的 manifest.json

        Args:
            name: 插件名称
            version: 版本号
            description: 描述
            author: 作者
            template: 模板类型
            **kwargs: 其他字段

        Returns:
            创建的 manifest 字典
        """
        # 根据模板类型生成组件列表
        template_components = self._get_template_components(template)

        manifest = {
            "name": name,
            "version": version,
            "description": description or f"{name} 插件",
            "author": author,
            "dependencies": {"plugins": [], "components": []},
            "include": template_components,
            "entry_point": "plugin.py",
            "min_core_version": "1.0.0",
            **kwargs,
        }

        self._manifest_cache = manifest
        return manifest

    def update_component(
        self,
        component_type: str,
        component_name: str,
        dependencies: list[str] | None = None,
    ) -> bool:
        """添加或更新组件

        Args:
            component_type: 组件类型
            component_name: 组件名称
            dependencies: 组件依赖列表

        Returns:
            是否成功
        """
        manifest = self.load()
        if manifest is None:
            return False

        # 获取 include 列表
        include_list = manifest.get("include", [])

        # 检查组件是否已存在
        for item in include_list:
            if (
                item.get("component_name") == component_name
                and item.get("component_type") == component_type
            ):
                # 组件已存在，更新依赖
                if dependencies is not None:
                    item["dependencies"] = dependencies
                self.save(manifest)
                return True

        # 添加新组件
        new_component = {
            "component_type": component_type,
            "component_name": component_name,
            "dependencies": dependencies or [],
        }
        include_list.append(new_component)
        manifest["include"] = include_list

        self.save(manifest)
        return True

    def remove_component(self, component_type: str, component_name: str) -> bool:
        """移除组件

        Args:
            component_type: 组件类型
            component_name: 组件名称

        Returns:
            是否成功
        """
        manifest = self.load()
        if manifest is None:
            return False

        include_list = manifest.get("include", [])
        original_length = len(include_list)

        # 过滤掉指定的组件
        include_list = [
            item
            for item in include_list
            if not (
                item.get("component_name") == component_name
                and item.get("component_type") == component_type
            )
        ]

        if len(include_list) == original_length:
            return False  # 没有找到要删除的组件

        manifest["include"] = include_list
        self.save(manifest)
        return True

    def get_components(
        self, component_type: str | None = None
    ) -> list[dict[str, Any]]:
        """获取所有组件或指定类型的组件

        Args:
            component_type: 组件类型，为 None 时返回所有组件

        Returns:
            组件列表
        """
        manifest = self.load()
        if manifest is None:
            return []

        include_list = manifest.get("include", [])

        if component_type is None:
            return include_list

        return [
            item for item in include_list if item.get("component_type") == component_type
        ]

    def update_version(self, new_version: str) -> None:
        """更新版本号

        Args:
            new_version: 新版本号
        """
        manifest = self.load()
        if manifest is None:
            raise ValueError("无法加载 manifest.json")

        manifest["version"] = new_version
        self.save(manifest)

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """获取指定字段的值

        Args:
            field_name: 字段名称
            default: 默认值

        Returns:
            字段值
        """
        manifest = self.load()
        if manifest is None:
            return default

        return manifest.get(field_name, default)

    def set_field(self, field_name: str, value: Any) -> None:
        """设置指定字段的值

        Args:
            field_name: 字段名称
            value: 字段值
        """
        manifest = self.load()
        if manifest is None:
            raise ValueError("无法加载 manifest.json")

        manifest[field_name] = value
        self.save(manifest)

    def validate(self) -> tuple[bool, list[str]]:
        """验证 manifest 的完整性

        Returns:
            (是否有效, 错误信息列表)
        """
        if not self.exists:
            return False, ["manifest.json 文件不存在"]

        manifest = self.load()
        if manifest is None:
            return False, ["无法解析 manifest.json"]

        errors = []

        # 检查必需字段
        required_fields = [
            "name",
            "version",
            "description",
            "author",
            "dependencies",
            "entry_point",
        ]
        for field in required_fields:
            if field not in manifest or not manifest[field]:
                errors.append(f"缺少必需字段: {field}")

        # 验证 dependencies 结构
        if "dependencies" in manifest:
            deps = manifest["dependencies"]
            if not isinstance(deps, dict):
                errors.append("dependencies 字段必须是一个对象")
            else:
                if "plugins" in deps and not isinstance(deps["plugins"], list):
                    errors.append("dependencies.plugins 必须是列表")
                if "components" in deps and not isinstance(deps["components"], list):
                    errors.append("dependencies.components 必须是列表")

        # 验证 include 列表
        if "include" in manifest:
            include_list = manifest["include"]
            if not isinstance(include_list, list):
                errors.append("include 字段必须是列表")
            else:
                for idx, item in enumerate(include_list):
                    if not isinstance(item, dict):
                        errors.append(f"include[{idx}] 必须是对象")
                        continue
                    if "component_type" not in item:
                        errors.append(f"include[{idx}] 缺少 component_type 字段")
                    if "component_name" not in item:
                        errors.append(f"include[{idx}] 缺少 component_name 字段")

        return len(errors) == 0, errors

    def _get_template_components(self, template: str) -> list[dict[str, Any]]:
        """根据模板类型获取组件列表

        Args:
            template: 模板类型

        Returns:
            组件列表
        """
        template_components = {
            "basic": [
                {"component_type": "config", "component_name": "config", "dependencies": []}
            ],
            "action": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "action",
                    "component_name": "example_action",
                    "dependencies": [],
                },
            ],
            "tool": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "tool",
                    "component_name": "example_tool",
                    "dependencies": [],
                },
            ],
            "collection": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "collection",
                    "component_name": "example_collection",
                    "dependencies": [],
                },
            ],
            "plus_command": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "plus_command",
                    "component_name": "example_command",
                    "dependencies": [],
                },
            ],
            "adapter": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "adapter",
                    "component_name": "example_adapter",
                    "dependencies": [],
                },
            ],
            "chatter": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "chatter",
                    "component_name": "example_chatter",
                    "dependencies": [],
                },
            ],
            "router": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "router",
                    "component_name": "example_router",
                    "dependencies": [],
                },
            ],
            "event_handler": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "event_handler",
                    "component_name": "example_event",
                    "dependencies": [],
                },
            ],
            "full": [
                {"component_type": "config", "component_name": "config", "dependencies": []},
                {
                    "component_type": "action",
                    "component_name": "example_action",
                    "dependencies": [],
                },
                {
                    "component_type": "tool",
                    "component_name": "example_tool",
                    "dependencies": [],
                },
                {
                    "component_type": "collection",
                    "component_name": "example_collection",
                    "dependencies": [],
                },
                {
                    "component_type": "plus_command",
                    "component_name": "example_command",
                    "dependencies": [],
                },
                {
                    "component_type": "event_handler",
                    "component_name": "example_event",
                    "dependencies": [],
                },
                {
                    "component_type": "service",
                    "component_name": "example_service",
                    "dependencies": [],
                },
            ],
        }

        return template_components.get(template, [])

    @classmethod
    def from_plugin_path(cls, plugin_path: Path | str) -> "ManifestManager":
        """从插件路径创建 ManifestManager

        Args:
            plugin_path: 插件目录路径

        Returns:
            ManifestManager 实例
        """
        return cls(plugin_path)

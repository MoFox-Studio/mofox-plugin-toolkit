"""
插件元数据验证器
"""

import json

from .base import BaseValidator, ValidationResult


class MetadataValidator(BaseValidator):
    """插件清单验证器

    检查 manifest.json 是否完整且格式正确
    """

    # 必需的元数据字段
    REQUIRED_FIELDS = ["name", "version", "description", "author", "dependencies", "entry_point"]

    # 推荐的元数据字段
    RECOMMENDED_FIELDS = ["min_core_version", "include"]

    def validate(self) -> ValidationResult:
        """执行清单验证

        Returns:
            ValidationResult: 验证结果
        """
        # 检查 manifest.json 是否存在
        manifest_file = self.plugin_path / "manifest.json"
        if not manifest_file.exists():
            self.result.add_error(
                "manifest.json 文件不存在",
                suggestion="请创建 manifest.json 文件并定义插件清单 | 可运行 'mpdt check --fix' 自动修复",
            )
            return self.result

        # 读取并解析 manifest.json
        try:
            with open(manifest_file, encoding="utf-8") as f:
                manifest_data = json.load(f)
        except json.JSONDecodeError as e:
            self.result.add_error(
                f"manifest.json 存在 JSON 语法错误: {e.msg}",
                file_path="manifest.json",
                line_number=e.lineno if hasattr(e, "lineno") else None,
                suggestion="请检查 JSON 格式是否正确",
            )
            return self.result
        except Exception as e:
            self.result.add_error(
                f"读取 manifest.json 失败: {e}",
                file_path="manifest.json",
            )
            return self.result

        self.result.add_info("找到 manifest.json 文件")

        # 检查必需字段
        missing_required = []
        for field in self.REQUIRED_FIELDS:
            if field not in manifest_data or not manifest_data[field]:
                missing_required.append(field)

        if missing_required:
            for field in missing_required:
                self.result.add_error(
                    f"manifest.json 缺少必需字段: {field}",
                    file_path="manifest.json",
                    suggestion=f'请在 manifest.json 中添加 "{field}" 字段 | 可运行 \'mpdt check --fix\' 自动修复',
                )
        else:
            self.result.add_info("所有必需的元数据字段都已提供")

        # 检查推荐字段
        missing_recommended = []
        for field in self.RECOMMENDED_FIELDS:
            if field not in manifest_data or not manifest_data[field]:
                missing_recommended.append(field)

        if missing_recommended:
            fields_str = ", ".join(f'"{f}"' for f in missing_recommended)
            self.result.add_warning(
                f"建议添加以下元数据字段: {', '.join(missing_recommended)}",
                file_path="manifest.json",
                suggestion=f"在 manifest.json 中添加: {fields_str}",
            )

        # 验证 dependencies 结构
        if "dependencies" in manifest_data:
            deps = manifest_data["dependencies"]
            if not isinstance(deps, dict):
                self.result.add_error(
                    "dependencies 字段必须是一个对象",
                    file_path="manifest.json",
                    suggestion='请使用格式: "dependencies": {"plugins": [], "components": []}',
                )
            else:
                # 检查 plugins 和 components 列表
                if "plugins" in deps and not isinstance(deps["plugins"], list):
                    self.result.add_error(
                        'dependencies.plugins 必须是数组',
                        file_path="manifest.json",
                    )
                if "components" in deps and not isinstance(deps["components"], list):
                    self.result.add_error(
                        'dependencies.components 必须是数组',
                        file_path="manifest.json",
                    )

        # 验证 include 结构（如果存在）
        if "include" in manifest_data:
            include_list = manifest_data["include"]
            if not isinstance(include_list, list):
                self.result.add_error(
                    "include 字段必须是一个数组",
                    file_path="manifest.json",
                    suggestion='请使用格式: "include": [{"component_type": "...", "component_name": "..."}]',
                )
            else:
                # 验证每个 include 项
                for i, item in enumerate(include_list):
                    if not isinstance(item, dict):
                        self.result.add_warning(
                            f"include[{i}] 必须是对象",
                            file_path="manifest.json",
                        )
                        continue

                    # 检查必需的组件字段
                    if "component_type" not in item:
                        self.result.add_warning(
                            f"include[{i}] 缺少 component_type 字段",
                            file_path="manifest.json",
                        )
                    if "component_name" not in item:
                        self.result.add_warning(
                            f"include[{i}] 缺少 component_name 字段",
                            file_path="manifest.json",
                        )

                    # 验证 dependencies 字段（组件级依赖）
                    if "dependencies" in item and not isinstance(item["dependencies"], list):
                        self.result.add_warning(
                            f"include[{i}].dependencies 必须是数组",
                            file_path="manifest.json",
                        )

        # 验证 entry_point 文件是否存在
        if "entry_point" in manifest_data:
            entry_point = self.plugin_path / manifest_data["entry_point"]
            if not entry_point.exists():
                self.result.add_warning(
                    f"entry_point 指向的文件不存在: {manifest_data['entry_point']}",
                    file_path="manifest.json",
                    suggestion=f"请确保文件 {manifest_data['entry_point']} 存在",
                )

        # 验证版本号格式
        if "version" in manifest_data:
            version = manifest_data["version"]
            # 简单的版本号格式检查（支持 x.y.z 格式）
            import re
            if not re.match(r'^\d+\.\d+\.\d+', str(version)):
                self.result.add_warning(
                    f"版本号格式建议使用语义化版本（如 1.0.0）: {version}",
                    file_path="manifest.json",
                )

        return self.result

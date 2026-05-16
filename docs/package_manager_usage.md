# PackageManager 使用示例

## 概述

新的 `PackageManager` 提供了统一的插件打包管理功能，返回结构化的 `PackageResult` 对象。

## 基本用法

### 1. 直接使用 PackageManager

```python
from pathlib import Path
from mpdt.utils.managers import PackageManager, PackageResult

# 初始化管理器
plugin_dir = Path("./my-plugin")
manager = PackageManager(plugin_dir)

# 构建打包
result: PackageResult = manager.build_package(
    output_dir="dist",
    with_docs=True,
    fmt="mfp",
    bump="patch"  # 可选：升级版本
)

# 访问结果
print(f"包路径: {result.package_path}")
print(f"插件名: {result.plugin_name}")
print(f"版本: {result.version}")
print(f"文件数: {result.file_count}")
print(f"SHA256: {result.sha256}")
print(f"大小: {result.format_size()}")
```

### 2. 使用构建命令

```python
from mpdt.commands.build import build_plugin

# build_plugin 现在返回 PackageResult 或 None
result = build_plugin(
    plugin_path="./my-plugin",
    output_dir="dist",
    with_docs=False,
    fmt="mfp",
    bump=None
)

if result:
    print(f"构建成功: {result.package_name}")
    print(f"SHA256: {result.sha256}")
else:
    print("构建失败")
```

### 3. 在市场发布中使用

```python
from mpdt.commands.market import market_publish

# market_publish 内部使用 build_plugin
# 自动获取 PackageResult 并使用其属性
market_publish(
    plugin_path="./my-plugin",
    github_token="your_token",
    output_dir="dist",
    with_docs=True
)
```

## PackageResult 属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `package_path` | Path | 打包文件的完整路径 |
| `plugin_name` | str | 插件名称 |
| `version` | str | 插件版本 |
| `file_count` | int | 打包的文件数量 |
| `original_size` | int | 原始文件总大小（字节） |
| `package_size` | int | 打包后的大小（字节） |
| `sha256` | str | SHA256 校验和 |
| `format` | Literal["mfp", "zip"] | 打包格式 |
| `package_name` | str | 打包文件名（属性） |

## PackageManager 方法

### collect_files(with_docs: bool = False) -> list[Path]
收集需要打包的文件列表

### bump_version(version: str, bump: Literal["major", "minor", "patch"]) -> str
升级语义化版本号

### calculate_sha256(file_path: Path) -> str
计算文件的 SHA256 校验和

### build_package(...) -> PackageResult
执行完整的打包流程

## 错误处理

```python
from mpdt.utils.managers import PackageManager

manager = PackageManager("./my-plugin")

try:
    result = manager.build_package()
    print(f"成功: {result.package_name}")
except ValueError as e:
    print(f"验证错误: {e}")
except FileNotFoundError as e:
    print(f"文件未找到: {e}")
except OSError as e:
    print(f"打包失败: {e}")
```

## 兼容性

- ✅ `market.py` 完全兼容，无需修改
- ✅ `build.py` 现在返回 `PackageResult`
- ✅ 保持向后兼容的命令行接口

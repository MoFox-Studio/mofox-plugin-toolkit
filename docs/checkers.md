# Checkers 模块

检查器模块，包含验证器（validators）和修复器（fixers）两个子系统。

## 架构

```
mpdt/checkers/
├── base.py                    # 基类定义
├── __init__.py               # 模块导出
├── validators/               # 验证器子模块
│   ├── __init__.py
│   ├── component_validator.py
│   ├── config_validator.py
│   ├── metadata_validator.py
│   ├── structure_validator.py
│   ├── style_validator.py
│   └── type_validator.py
└── fixers/                   # 修复器子模块
    ├── __init__.py
    ├── attribute_fixer.py    # 属性修复器
    ├── decorator_fixer.py    # 装饰器修复器
    ├── manifest_fixer.py     # Manifest 修复器
    ├── method_fixer.py       # 方法修复器
    ├── style_fixer.py        # 代码风格修复器
    └── transformers.py       # libcst 转换器工具
```

## 基类

### BaseValidator

验证器基类，所有验证器都继承自此类。

```python
from pathlib import Path
from mpdt.checkers import BaseValidator, ValidationResult

class MyValidator(BaseValidator):
    def validate(self) -> ValidationResult:
        # 实现验证逻辑
        pass
```

### BaseFixer

修复器基类，所有修复器都继承自此类。

```python
from pathlib import Path
from mpdt.checkers import BaseFixer, FixResult, ValidationIssue

class MyFixer(BaseFixer):
    def can_fix(self, issue: ValidationIssue) -> bool:
        # 判断是否可以修复
        return True
    
    def fix(self, issues: list[ValidationIssue]) -> FixResult:
        # 实现修复逻辑
        pass
```

## 验证器（Validators）

### StructureValidator
检查插件目录结构是否符合规范。

### MetadataValidator
检查 manifest.json 等元数据文件。

### ComponentValidator
检查组件类的元数据和方法签名。

### ConfigValidator
检查配置文件的格式和内容。

### StyleValidator
使用 ruff 检查代码风格。

### TypeValidator
使用 mypy 进行类型检查。

## 修复器（Fixers）

### ManifestFixer
修复缺失的 manifest.json 文件，自动创建基本的 manifest 结构。

**可修复的问题：**
- 缺失的 manifest.json 文件

### DecoratorFixer
修复插件类缺失的装饰器。

**可修复的问题：**
- 缺失的 `@register_plugin` 装饰器

### AttributeFixer
修复类属性相关的问题。

**可修复的问题：**
- 插件类缺失的属性（plugin_name、plugin_description、plugin_version）
- 组件类缺失的必需属性

### MethodFixer
修复方法相关的问题。

**可修复的问题：**
- 缺失的必需方法
- 方法异步性错误（应该是异步但实际是同步，或反之）
- 方法参数错误
- 缺失的返回类型注解

### StyleFixer
使用 ruff 自动修复代码风格问题。

**可修复的问题：**
- 所有 ruff 可以自动修复的代码风格问题（如未使用的导入、格式问题等）

## 使用示例

### 手动使用验证器

```python
from pathlib import Path
from mpdt.checkers.validators import StructureValidator

plugin_path = Path("path/to/plugin")
validator = StructureValidator(plugin_path)
result = validator.validate()

if result.success:
    print("验证通过！")
else:
    for issue in result.issues:
        print(f"{issue.level}: {issue.message}")
```

### 手动使用修复器

```python
from pathlib import Path
from mpdt.checkers.fixers import ManifestFixer
from mpdt.checkers.validators import MetadataValidator

plugin_path = Path("path/to/plugin")

# 先验证
validator = MetadataValidator(plugin_path)
result = validator.validate()

# 再修复
if not result.success:
    fixer = ManifestFixer(plugin_path)
    fix_result = fixer.fix(result.issues)
    
    if fix_result.fixes_applied:
        print(f"成功修复 {len(fix_result.fixes_applied)} 个问题")
```

### 使用 CLI

```bash
# 只验证
mpdt check path/to/plugin

# 验证并自动修复
mpdt check path/to/plugin --auto-fix

# 详细输出
mpdt check path/to/plugin --auto-fix --verbose
```

## 扩展

### 创建自定义验证器

```python
from pathlib import Path
from mpdt.checkers import BaseValidator, ValidationResult

class CustomValidator(BaseValidator):
    def validate(self) -> ValidationResult:
        self.result = ValidationResult(validator_name=self.__class__.__name__)
        
        # 实现你的验证逻辑
        if some_condition:
            self.result.add_error("发现错误", file_path="plugin.py")
        
        return self.result
```

### 创建自定义修复器

```python
from pathlib import Path
from mpdt.checkers import BaseFixer, FixResult, ValidationIssue

class CustomFixer(BaseFixer):
    def can_fix(self, issue: ValidationIssue) -> bool:
        # 判断此修复器是否能处理这个问题
        return "specific_error" in issue.message
    
    def fix(self, issues: list[ValidationIssue]) -> FixResult:
        self.result = FixResult(fixer_name=self.__class__.__name__)
        
        for issue in issues:
            if self.can_fix(issue):
                try:
                    # 实现修复逻辑
                    self._do_fix(issue)
                    self.result.add_fix("成功修复问题", issue)
                except Exception as e:
                    self.result.add_failure(f"修复失败: {e}")
        
        return self.result
    
    def _do_fix(self, issue: ValidationIssue) -> None:
        # 具体的修复实现
        pass
```

## 变更历史

### v2.0.0 (2026-05-15)
- **重大重构**：将 `validators` 重命名为 `checkers`
- 将验证器移动到 `checkers/validators/` 子目录
- 创建新的 `checkers/fixers/` 子目录
- 拆分原有的 `AutoFixValidator` 为多个独立的修复器：
  - ManifestFixer
  - DecoratorFixer
  - AttributeFixer
  - MethodFixer
  - StyleFixer
- 引入 `BaseFixer` 基类和 `FixResult` 结果类
- 每个修复器现在都是独立的、可组合的

### v1.x
- 使用单一的 `AutoFixValidator` 处理所有修复
- 所有验证器在 `validators/` 目录下

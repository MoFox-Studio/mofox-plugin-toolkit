"""
Config 组件模板（Neo-MoFox 架构）
"""

CONFIG_TEMPLATE = '''"""
{description}

Created by: {author}
Created at: {date}
"""

from src.core.components.base import BaseConfig
from src.kernel.config.core import config_section, Field, SectionBase


class {class_name}(BaseConfig):
    """
    {description}

    Config 组件用于管理插件配置。
    扩展 ConfigBase，提供插件特定的配置管理。
    """

    config_name = "{component_name}"
    config_description = "{description}"

    @config_section("general")
    class GeneralSection(SectionBase):
        """通用配置节"""
        enabled: bool = Field(default=True, description="是否启用插件")
        version: str = Field(default="1.0.0", description="配置版本")
        debug_mode: bool = Field(default=False, description="调试模式")

    @config_section("features")
    class FeaturesSection(SectionBase):
        """功能配置节"""
        # TODO: 添加功能相关配置
        feature_a_enabled: bool = Field(default=True, description="功能A是否启用")
        feature_b_enabled: bool = Field(default=False, description="功能B是否启用")

    @config_section("advanced")
    class AdvancedSection(SectionBase):
        """高级配置节"""
        # TODO: 添加高级配置
        timeout: int = Field(default=30, description="超时时间（秒）")
        max_retries: int = Field(default=3, description="最大重试次数")

    # 配置节实例
    general: GeneralSection = Field(default_factory=GeneralSection)
    features: FeaturesSection = Field(default_factory=FeaturesSection)
    advanced: AdvancedSection = Field(default_factory=AdvancedSection)
'''


def get_config_template() -> str:
    """获取 Config 组件模板"""
    return CONFIG_TEMPLATE

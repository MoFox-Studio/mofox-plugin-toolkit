"""
组件模板索引

此模块导出所有组件模板的获取函数。
"""

from datetime import datetime

from mpdt.templates.action_template import get_action_template
from mpdt.templates.adapter_template import get_adapter_template
from mpdt.templates.chatter_template import get_chatter_template
from mpdt.templates.event_template import get_event_handler_template
from mpdt.templates.plus_command_template import get_plus_command_template
from mpdt.templates.prompt_template import get_prompt_template
from mpdt.templates.router_template import get_router_template
from mpdt.templates.tool_template import get_tool_template

# 导出所有模板获取函数
__all__ = [
    "get_action_template",
    "get_tool_template",
    "get_event_handler_template",
    "get_adapter_template",
    "get_prompt_template",
    "get_plus_command_template",
    "get_chatter_template",
    "get_router_template",
    "get_component_template",
    "prepare_component_context",
]


def get_component_template(component_type: str) -> str:
    """
    根据组件类型获取对应的模板

    Args:
        component_type: 组件类型 (action, tool, event, adapter, prompt, plus_command, chatter, router)

    Returns:
        模板字符串

    Raises:
        ValueError: 不支持的组件类型
    """
    template_map = {
        "action": get_action_template,
        "tool": get_tool_template,
        "event": get_event_handler_template,
        "adapter": get_adapter_template,
        "prompt": get_prompt_template,
        "plus_command": get_plus_command_template,
        "chatter": get_chatter_template,
        "router": get_router_template,
    }

    if component_type not in template_map:
        raise ValueError(
            f"不支持的组件类型: {component_type}. "
            f"支持的类型: {', '.join(template_map.keys())}"
        )

    return template_map[component_type]()


def prepare_component_context(
    component_type: str,
    component_name: str,
    plugin_name: str,
    author: str = "",
    description: str = "",
    is_async: bool = False,
) -> dict[str, str]:
    """
    准备组件模板上下文

    Args:
        component_type: 组件类型 (action, tool, event, adapter, prompt, plus_command,router,chatter)
        component_name: 组件名称 (snake_case)
        plugin_name: 插件名称
        author: 作者
        description: 描述
        is_async: 是否异步

    Returns:
        模板上下文字典
    """
    from mpdt.utils.file_ops import to_pascal_case

    # 转换为 PascalCase 并添加类型后缀
    class_name = to_pascal_case(component_name)

    # 根据组件类型添加合适的后缀
    suffix_map = {
        "action": "Action",
        "tool": "Tool",
        "event": "EventHandler",
        "adapter": "Adapter",
        "prompt": "Prompt",
        "plus_command": "PlusCommand",
        "chatter": "Chatter",
        "router": "Router",
    }

    suffix = suffix_map.get(component_type, "")
    if suffix and not class_name.endswith(suffix):
        class_name = f"{class_name}{suffix}"

    date = datetime.now().strftime("%Y-%m-%d")

    # 基础上下文
    context = {
        "component_name": component_name,
        "class_name": class_name,
        "plugin_name": plugin_name,
        "author": author,
        "description": description or f"{class_name} 组件",
        "date": date,
        "async_keyword": "async " if is_async else "",
        "await_keyword": "await " if is_async else "",
        "component_type": component_type + "s",  # actions, tools, etc.
        "module_name": component_name,
        "method_name": _get_method_name(component_type),
    }

    # 特定组件类型的额外字段
    if component_type == "plus_command":
        context["command_name"] = component_name
    elif component_type == "tool":
        context["tool_name"] = component_name
    elif component_type == "event":
        context["event_type"] = component_name.replace("_handler", "").replace("_event", "")
    elif component_type == "adapter":
        context["adapter_name"] = component_name
    elif component_type == "prompt":
        context["prompt_name"] = component_name
    elif component_type == "chatter":
        context["chatter_name"] = component_name
    elif component_type == "router":
        context["router_name"] = component_name

    return context


def _get_method_name(component_type: str) -> str:
    """
    根据组件类型获取主要方法名

    Args:
        component_type: 组件类型

    Returns:
        方法名
    """
    method_map = {
        "action": "execute",
        "plus_command": "execute",
        "tool": "run",
        "event": "handle",
        "adapter": "connect",
        "prompt": "build",
        "chatter": "chat",
        "router": "route",
    }
    return method_map.get(component_type, "execute")

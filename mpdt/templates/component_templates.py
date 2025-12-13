"""
组件代码生成模板
"""

from datetime import datetime


def get_action_template() -> str:
    """获取 Action 组件模板"""
    return '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.common.logger import get_logger
from src.plugin_system import BaseAction

logger = get_logger(__name__)


class {class_name}(BaseAction):
    """
    {description}
    
    这个 Action 用于...
    
    Args:
        context: 执行上下文
        **kwargs: 其他参数
    
    Returns:
        执行结果
    """
    
    def __init__(self):
        super().__init__()
        # TODO: 初始化你的 Action
    
    {async_keyword}def execute(self, context: Any, **kwargs: Any) -> Any:
        """
        执行 Action
        
        Args:
            context: 执行上下文
            **kwargs: 其他参数
        
        Returns:
            执行结果
        """
        try:
            logger.info("开始执行 {class_name}")
            
            # TODO: 实现你的逻辑
            result = None
            
            logger.info("执行完成")
            return result
            
        except Exception as e:
            logger.error(f"执行失败: {{e}}")
            raise
'''


def get_tool_template() -> str:
    """获取 Tool 组件模板"""
    return '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.common.logger import get_logger
from src.plugin_system import BaseTool

logger = get_logger(__name__)


class {class_name}(BaseTool):
    """
    {description}
    
    这个 Tool 提供...功能
    """
    
    def __init__(self):
        super().__init__()
        self.name = "{tool_name}"
        self.description = "{description}"
        
        # Tool Schema 定义
        self.schema = {{
            "type": "function",
            "function": {{
                "name": self.name,
                "description": self.description,
                "parameters": {{
                    "type": "object",
                    "properties": {{
                        # TODO: 定义参数
                        "param1": {{
                            "type": "string",
                            "description": "参数1说明"
                        }}
                    }},
                    "required": ["param1"]
                }}
            }}
        }}
    
    {async_keyword}def run(self, **kwargs: Any) -> Any:
        """
        运行 Tool
        
        Args:
            **kwargs: Tool 参数
        
        Returns:
            执行结果
        """
        try:
            logger.info(f"运行 Tool: {{self.name}}")
            
            # TODO: 验证参数
            # TODO: 实现 Tool 逻辑
            
            result = {{"status": "success", "data": None}}
            logger.info("Tool 运行完成")
            return result
            
        except Exception as e:
            logger.error(f"Tool 运行失败: {{e}}")
            raise
'''


def get_event_handler_template() -> str:
    """获取 Event Handler 组件模板"""
    return '''"""
{description}

Created by: {author}
Created at: {date}
"""

from typing import Any

from src.common.logger import get_logger
from src.plugin_system import BaseEventHandler

logger = get_logger(__name__)


class {class_name}(BaseEventHandler):
    """
    {description}
    
    处理的事件类型: {event_type}
    """
    
    def __init__(self):
        super().__init__()
        self.event_type = "{event_type}"  # 事件类型
        self.priority = 100  # 优先级 (0-1000, 数字越小优先级越高)
    
    {async_keyword}def handle(self, event: Any, **kwargs: Any) -> Any:
        """
        处理事件
        
        Args:
            event: 事件对象
            **kwargs: 其他参数
        
        Returns:
            处理结果
        """
        try:
            logger.info(f"处理事件: {{self.event_type}}")
            
            # TODO: 实现事件处理逻辑
            
            logger.info("事件处理完成")
            return True
            
        except Exception as e:
            logger.error(f"事件处理失败: {{e}}")
            raise
    
    def should_handle(self, event: Any) -> bool:
        """
        判断是否应该处理该事件
        
        Args:
            event: 事件对象
        
        Returns:
            是否处理
        """
        # TODO: 实现判断逻辑
        return True
'''


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
        component_type: 组件类型 (action, tool, event)
        component_name: 组件名称 (snake_case)
        plugin_name: 插件名称
        author: 作者
        description: 描述
        is_async: 是否异步

    Returns:
        模板上下文字典
    """
    from mpdt.utils.file_ops import to_pascal_case

    class_name = to_pascal_case(component_name)
    if not class_name.endswith(component_type.title()):
        class_name = f"{class_name}{component_type.title()}"

    date = datetime.now().strftime("%Y-%m-%d")

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
        "method_name": "execute" if component_type == "action" else ("run" if component_type == "tool" else "handle"),
    }

    # 特定组件类型的额外字段
    if component_type == "tool":
        context["tool_name"] = component_name
    elif component_type == "event":
        context["event_type"] = component_name.replace("_handler", "")

    return context

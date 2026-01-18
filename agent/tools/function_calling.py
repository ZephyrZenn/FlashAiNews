"""工具 Schema 转换为 Function Calling 格式的工具函数

提供将 ToolSchema 转换为 OpenAI 和 Gemini function calling 格式的功能。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.tools.base import BaseTool, ToolType


def _map_type_to_json_schema(python_type: str) -> dict:
    """将 Python 类型映射到 JSON Schema 类型
    
    Args:
        python_type: Python 类型字符串，如 "str", "int", "list[int]"
    
    Returns:
        JSON Schema 类型定义
    """
    python_type = python_type.lower().strip()
    
    # 基本类型映射
    if python_type in ("str", "string"):
        return {"type": "string"}
    elif python_type in ("int", "integer"):
        return {"type": "integer"}
    elif python_type in ("float", "number"):
        return {"type": "number"}
    elif python_type in ("bool", "boolean"):
        return {"type": "boolean"}
    elif python_type.startswith("list") or python_type.startswith("sequence"):
        # 处理 list[str], list[int] 等
        # 简单处理：提取内部类型，如果没有则默认为 string
        inner_type = "string"
        if "[" in python_type and "]" in python_type:
            inner_type = python_type[python_type.index("[") + 1:python_type.index("]")]
        return {
            "type": "array",
            "items": _map_type_to_json_schema(inner_type)
        }
    elif python_type.startswith("dict") or python_type.startswith("typing.dict"):
        return {"type": "object"}
    else:
        # 默认返回 string
        return {"type": "string"}


def tool_schema_to_openai_format(tool: "BaseTool") -> dict:
    """将 ToolSchema 转换为 OpenAI function calling 格式
    
    Args:
        tool: 工具实例
    
    Returns:
        OpenAI function calling 格式的字典
    """
    schema = tool.schema
    properties = {}
    required = []
    
    for param in schema.parameters:
        param_schema = _map_type_to_json_schema(param.type)
        param_schema["description"] = param.description
        
        if param.default:
            # 尝试解析默认值
            try:
                if param_schema["type"] == "integer":
                    param_schema["default"] = int(param.default)
                elif param_schema["type"] == "number":
                    param_schema["default"] = float(param.default)
                elif param_schema["type"] == "boolean":
                    param_schema["default"] = param.default.lower() in ("true", "1", "yes")
                else:
                    param_schema["default"] = param.default
            except (ValueError, TypeError):
                param_schema["default"] = param.default
        
        properties[param.name] = param_schema
        
        if param.required:
            required.append(param.name)
    
    return {
        "type": "function",
        "function": {
            "name": schema.name,
            "description": schema.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,  # 始终使用数组，即使是空数组也符合 JSON Schema 规范
            }
        }
    }


def tool_schema_to_gemini_format(tool: "BaseTool") -> dict:
    """将 ToolSchema 转换为 Gemini function calling 格式
    
    Args:
        tool: 工具实例
    
    Returns:
        Gemini function calling 格式的字典
    """
    schema = tool.schema
    properties = {}
    required = []
    
    for param in schema.parameters:
        param_schema = _map_type_to_json_schema(param.type)
        param_schema["description"] = param.description
        
        if param.default:
            try:
                if param_schema["type"] == "integer":
                    param_schema["default"] = int(param.default)
                elif param_schema["type"] == "number":
                    param_schema["default"] = float(param.default)
                elif param_schema["type"] == "boolean":
                    param_schema["default"] = param.default.lower() in ("true", "1", "yes")
                else:
                    param_schema["default"] = param.default
            except (ValueError, TypeError):
                param_schema["default"] = param.default
        
        properties[param.name] = param_schema
        
        if param.required:
            required.append(param.name)
    
    return {
        "function_declarations": [{
            "name": schema.name,
            "description": schema.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,  # 始终使用数组，即使是空数组也符合 JSON Schema 规范
            }
        }]
    }


def tools_to_openai_format(tools: list["ToolType"]) -> list[dict]:
    """将工具列表转换为 OpenAI function calling 格式
    
    Args:
        tools: 工具实例列表
    
    Returns:
        OpenAI function calling 格式的工具列表
    """
    return [tool_schema_to_openai_format(tool) for tool in tools if tool]


def tools_to_gemini_format(tools: list["ToolType"]) -> list[dict]:
    """将工具列表转换为 Gemini function calling 格式
    
    Args:
        tools: 工具实例列表
    
    Returns:
        Gemini function calling 格式的工具列表
    """
    return [tool_schema_to_gemini_format(tool) for tool in tools if tool]

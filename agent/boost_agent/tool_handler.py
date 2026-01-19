"""工具调用处理

处理工具调用的执行、结果序列化和错误处理。
"""

import json
import logging
from typing import Any

from agent.models import log_step
from agent.tools.base import BaseTool
from core.config import get_config

logger = logging.getLogger(__name__)


class ToolHandler:
    """处理工具调用"""

    def __init__(self, state: dict, arg_converter: Any, context_manager: Any):
        """初始化工具处理器
        
        Args:
            state: AgentState 字典
            arg_converter: ArgumentConverter 实例
            context_manager: ContextManager 实例
        """
        self.state = state
        self.arg_converter = arg_converter
        self.context_manager = context_manager

    async def execute_tool(
        self, tool_name: str, tool: BaseTool, tool_args: dict
    ) -> Any:
        """执行工具并处理参数转换
        
        Args:
            tool_name: 工具名称
            tool: 工具实例
            tool_args: 工具参数
            
        Returns:
            工具执行结果
        """
        # 处理特殊参数
        if "state" in tool_args and isinstance(tool_args["state"], dict):
            tool_args["state"] = self.state

        # 处理写作工具的参数转换
        if tool_name in (
            "write_article",
            "review_article",
            "boost_write_article",
            "boost_review_article",
        ):
            tool_args = self.arg_converter.convert_writing_tool_args(
                tool_name, tool_args
            )

        # 处理 find_keywords 的参数转换
        if tool_name == "find_keywords" and "articles" in tool_args:
            tool_args["articles"] = self.arg_converter.convert_articles_arg(
                tool_args["articles"]
            )

        # 交给具体工具执行（工具内部有统一异常封装为 ToolResult）
        return await tool.execute(**tool_args)

    def serialize_tool_result(self, result: Any) -> str:
        """序列化工具结果，对大型结果进行优化
        
        Args:
            result: 工具执行结果
            
        Returns:
            序列化后的字符串
        """
        if not result.success:
            return json.dumps({"error": result.error}, ensure_ascii=False)

        try:
            data = result.data
            cfg = get_config().context

            # 对大型结果进行优化
            if isinstance(data, (list, tuple)):
                # 如果是文章列表，使用优化器截断
                if data and isinstance(data[0], dict) and "title" in data[0]:
                    # 可能是文章列表，进行优化
                    max_items = int(getattr(cfg, "tool_result_max_items", 20))
                    if len(data) > max_items:
                        log_step(
                            self.state,
                            f"📦 工具结果优化：将 {len(data)} 篇文章截断为 {max_items} 篇",
                        )
                        data = data[:max_items]

            # 序列化（支持带 to_dict 的自定义类）
            def _json_default(obj):
                if hasattr(obj, "to_dict"):
                    return obj.to_dict()
                if hasattr(obj, "__dict__"):
                    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
                return str(obj)

            serialized = json.dumps(data, default=_json_default, ensure_ascii=False)

            # 如果结果仍然很大，进一步截断
            max_length = int(getattr(cfg, "tool_result_max_chars", 5000))
            if len(serialized) > max_length:
                log_step(
                    self.state,
                    f"📦 工具结果优化：截断大型结果 ({len(serialized)} -> {max_length} 字符)",
                )
                # 尝试保持JSON格式
                try:
                    parsed = json.loads(serialized)
                    if isinstance(parsed, dict):
                        # 只保留关键字段
                        essential_keys = ["id", "title", "url", "summary", "error", "data"]
                        truncated = {k: v for k, v in parsed.items() if k in essential_keys}
                        serialized = json.dumps(truncated, default=str, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    # 如果不是JSON，直接截断
                    serialized = serialized[:max_length] + "..."

            return serialized
        except (TypeError, ValueError):
            return json.dumps({"data": str(result.data)}, ensure_ascii=False)

    def create_error_message(self, tool_id: str, tool_name: str, error: str) -> dict:
        """创建错误消息
        
        Args:
            tool_id: 工具调用ID
            tool_name: 工具名称
            error: 错误信息
            
        Returns:
            错误消息字典
        """
        return {
            "role": "tool",
            "tool_call_id": tool_id,
            "name": tool_name,
            "content": json.dumps({"error": error}),
        }

    def parse_tool_arguments(
        self, tool_call: dict, tool_id: str, tool_name: str, tool_messages: list
    ) -> dict | None:
        """解析工具参数
        
        Args:
            tool_call: 工具调用字典
            tool_id: 工具调用ID
            tool_name: 工具名称
            tool_messages: 工具消息列表（用于添加错误消息）
            
        Returns:
            解析后的参数字典，如果解析失败返回 None
        """
        try:
            tool_args_str = tool_call["function"]["arguments"]
            return json.loads(tool_args_str)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse tool arguments: %s, args: %s",
                e,
                tool_call["function"].get("arguments", ""),
            )
            tool_messages.append(
                self.create_error_message(tool_id, tool_name, f"参数解析失败: {str(e)}")
            )
            return None

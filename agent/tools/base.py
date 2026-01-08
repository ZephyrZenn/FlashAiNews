from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Optional
import traceback

T = TypeVar("T")


@dataclass
class ToolResult(Generic[T]):
    """统一的工具返回结果结构

    Attributes:
        success: 工具是否执行成功
        data: 执行成功时返回的数据，失败时为 None
        error: 执行失败时的错误信息，成功时为 None
        error_type: 错误类型名称（如 ValueError, ConnectionError 等）
        message: 可选的额外消息，用于提供执行状态说明
    """

    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = None

    @classmethod
    def ok(cls, data: T, message: Optional[str] = None) -> "ToolResult[T]":
        """创建成功的结果"""
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(
        cls,
        error: str,
        error_type: Optional[str] = None,
        message: Optional[str] = None,
    ) -> "ToolResult[T]":
        """创建失败的结果"""
        return cls(
            success=False, error=error, error_type=error_type, message=message
        )

    @classmethod
    def from_exception(cls, e: Exception, message: Optional[str] = None) -> "ToolResult[T]":
        """从异常创建失败结果"""
        return cls(
            success=False,
            error=str(e),
            error_type=type(e).__name__,
            message=message or f"工具执行时发生异常: {type(e).__name__}",
        )


@dataclass
class ToolParameter:
    """工具参数描述

    Attributes:
        name: 参数名称
        type: 参数类型
        description: 参数说明
        required: 是否必填
        default: 默认值（如果有）
    """

    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[str] = None


@dataclass
class ToolSchema:
    """工具的完整描述 Schema，供 LLM 理解和调用

    Attributes:
        name: 工具名称（唯一标识符）
        description: 工具功能的详细描述
        parameters: 参数列表
        returns: 返回值说明
        usage_examples: 使用示例
        when_to_use: 何时使用此工具的说明
        notes: 注意事项
    """

    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    returns: str = ""
    usage_examples: list[str] = field(default_factory=list)
    when_to_use: str = ""
    notes: list[str] = field(default_factory=list)

    def to_prompt(self) -> str:
        """将 Schema 转换为可供 LLM 阅读的提示文本"""
        lines = [
            f"## {self.name}",
            "",
            f"**功能**: {self.description}",
            "",
        ]

        if self.when_to_use:
            lines.extend([f"**使用时机**: {self.when_to_use}", ""])

        if self.parameters:
            lines.append("**参数**:")
            for p in self.parameters:
                required_mark = "(必填)" if p.required else "(可选)"
                default_info = f", 默认: {p.default}" if p.default else ""
                lines.append(
                    f"  - `{p.name}` ({p.type}) {required_mark}: {p.description}{default_info}"
                )
            lines.append("")

        if self.returns:
            lines.extend([f"**返回值**: {self.returns}", ""])

        if self.usage_examples:
            lines.append("**示例**:")
            for example in self.usage_examples:
                lines.append(f"  - {example}")
            lines.append("")

        if self.notes:
            lines.append("**注意事项**:")
            for note in self.notes:
                lines.append(f"  - {note}")
            lines.append("")

        return "\n".join(lines)


class BaseTool(ABC, Generic[T]):
    """异步工具抽象基类，定义统一的工具接口

    子类必须实现:
        - name: 工具名称
        - schema: 工具的完整 Schema 描述
        - _execute: 实际执行逻辑
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识名称"""
        raise NotImplementedError

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """工具的完整 Schema 描述，供 LLM 理解如何使用此工具"""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """工具描述（从 schema 获取）"""
        return self.schema.description

    @abstractmethod
    async def _execute(self, *args, **kwargs) -> T:
        """
        实际执行工具的异步方法（子类实现）

        子类应覆盖此方法并定义具体参数签名
        """
        raise NotImplementedError

    async def execute(self, *args, **kwargs) -> ToolResult[T]:
        """
        执行工具并返回统一的结果结构

        自动处理异常并封装为 ToolResult
        """
        try:
            result = await self._execute(*args, **kwargs)
            return ToolResult.ok(result)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return ToolResult.from_exception(e)

    def get_prompt(self) -> str:
        """获取供 LLM 阅读的工具说明"""
        return self.schema.to_prompt()

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"


class SyncTool(ABC, Generic[T]):
    """同步工具抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识名称"""
        raise NotImplementedError

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """工具的完整 Schema 描述，供 LLM 理解如何使用此工具"""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """工具描述（从 schema 获取）"""
        return self.schema.description

    @abstractmethod
    def _execute(self, *args, **kwargs) -> T:
        """
        实际执行工具的同步方法（子类实现）

        子类应覆盖此方法并定义具体参数签名
        """
        raise NotImplementedError

    def execute(self, *args, **kwargs) -> ToolResult[T]:
        """
        执行工具并返回统一的结果结构

        自动处理异常并封装为 ToolResult
        """
        try:
            result = self._execute(*args, **kwargs)
            return ToolResult.ok(result)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            return ToolResult.from_exception(e)

    def get_prompt(self) -> str:
        """获取供 LLM 阅读的工具说明"""
        return self.schema.to_prompt()

    def __repr__(self) -> str:
        return f"<SyncTool: {self.name}>"


def get_all_tools_prompt(tools: list[BaseTool | SyncTool]) -> str:
    """生成所有工具的 LLM 可读提示

    Args:
        tools: 工具列表

    Returns:
        格式化的工具说明文本
    """
    lines = ["# 可用工具列表", ""]
    for tool in tools:
        lines.append(tool.get_prompt())
    return "\n".join(lines)


# 工具类型别名
ToolType = BaseTool | SyncTool


class ToolBox:
    """工具箱，用于管理和组织可用工具

    提供工具的注册、查找、分类和提示生成功能。

    使用示例:
        # 创建工具箱并注册工具
        toolbox = ToolBox()
        toolbox.register(recent_group_update_tool, tags=["database", "query"])
        toolbox.register(search_memory_tool, tags=["database", "memory"])
        toolbox.register(web_search_tool, tags=["search", "web"])

        # 获取工具
        tool = toolbox.get("search_memory")

        # 按标签筛选
        db_tools = toolbox.filter_by_tag("database")

        # 生成 LLM 提示
        prompt = toolbox.get_prompt()
    """

    def __init__(self):
        self._tools: dict[str, ToolType] = {}
        self._tags: dict[str, set[str]] = {}  # tag -> set of tool names

    def register(
        self,
        tool: ToolType,
        tags: list[str] | None = None,
    ) -> "ToolBox":
        """注册工具到工具箱

        Args:
            tool: 工具实例
            tags: 工具标签列表，用于分类和筛选

        Returns:
            self，支持链式调用

        Raises:
            ValueError: 如果工具名称已存在
        """
        if tool.name in self._tools:
            raise ValueError(f"工具 '{tool.name}' 已存在，请勿重复注册")

        self._tools[tool.name] = tool

        # 注册标签
        if tags:
            for tag in tags:
                if tag not in self._tags:
                    self._tags[tag] = set()
                self._tags[tag].add(tool.name)

        return self

    def register_many(
        self,
        tools: list[ToolType],
        tags: list[str] | None = None,
    ) -> "ToolBox":
        """批量注册工具

        Args:
            tools: 工具实例列表
            tags: 应用于所有工具的标签列表

        Returns:
            self，支持链式调用
        """
        for tool in tools:
            self.register(tool, tags=tags)
        return self

    def unregister(self, name: str) -> "ToolBox":
        """从工具箱移除工具

        Args:
            name: 工具名称

        Returns:
            self，支持链式调用
        """
        if name in self._tools:
            del self._tools[name]
            # 从所有标签中移除
            for tag_tools in self._tags.values():
                tag_tools.discard(name)
        return self

    def get(self, name: str) -> ToolType | None:
        """根据名称获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，不存在时返回 None
        """
        return self._tools.get(name)

    def get_or_raise(self, name: str) -> ToolType:
        """根据名称获取工具，不存在时抛出异常

        Args:
            name: 工具名称

        Returns:
            工具实例

        Raises:
            KeyError: 工具不存在
        """
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise KeyError(f"工具 '{name}' 不存在。可用工具: {available}")
        return self._tools[name]

    def has(self, name: str) -> bool:
        """检查工具是否存在

        Args:
            name: 工具名称

        Returns:
            工具是否存在
        """
        return name in self._tools

    def all(self) -> list[ToolType]:
        """获取所有已注册的工具

        Returns:
            工具列表
        """
        return list(self._tools.values())

    def names(self) -> list[str]:
        """获取所有工具名称

        Returns:
            工具名称列表
        """
        return list(self._tools.keys())

    def filter_by_tag(self, tag: str) -> list[ToolType]:
        """根据标签筛选工具

        Args:
            tag: 标签名称

        Returns:
            匹配标签的工具列表
        """
        tool_names = self._tags.get(tag, set())
        return [self._tools[name] for name in tool_names if name in self._tools]

    def filter_by_tags(self, tags: list[str], match_all: bool = False) -> list[ToolType]:
        """根据多个标签筛选工具

        Args:
            tags: 标签列表
            match_all: True 表示必须匹配所有标签，False 表示匹配任一标签

        Returns:
            匹配的工具列表
        """
        if not tags:
            return self.all()

        if match_all:
            # 交集：必须包含所有标签
            result_names = None
            for tag in tags:
                tag_tools = self._tags.get(tag, set())
                if result_names is None:
                    result_names = tag_tools.copy()
                else:
                    result_names &= tag_tools
            result_names = result_names or set()
        else:
            # 并集：包含任一标签
            result_names = set()
            for tag in tags:
                result_names |= self._tags.get(tag, set())

        return [self._tools[name] for name in result_names if name in self._tools]

    def get_tags(self) -> list[str]:
        """获取所有已注册的标签

        Returns:
            标签列表
        """
        return list(self._tags.keys())

    def get_tool_tags(self, name: str) -> list[str]:
        """获取指定工具的所有标签

        Args:
            name: 工具名称

        Returns:
            标签列表
        """
        return [tag for tag, tools in self._tags.items() if name in tools]

    def get_prompt(self, tools: list[ToolType] | None = None) -> str:
        """生成工具的 LLM 可读提示

        Args:
            tools: 指定要生成提示的工具列表，None 表示所有工具

        Returns:
            格式化的工具说明文本
        """
        target_tools = tools if tools is not None else self.all()
        return get_all_tools_prompt(target_tools)

    def get_prompt_by_tag(self, tag: str) -> str:
        """生成指定标签下工具的 LLM 可读提示

        Args:
            tag: 标签名称

        Returns:
            格式化的工具说明文本
        """
        return self.get_prompt(self.filter_by_tag(tag))

    def get_schemas(self) -> list[ToolSchema]:
        """获取所有工具的 Schema

        Returns:
            ToolSchema 列表
        """
        return [tool.schema for tool in self._tools.values()]

    def __len__(self) -> int:
        """返回工具数量"""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """支持 in 操作符"""
        return name in self._tools

    def __iter__(self):
        """支持迭代"""
        return iter(self._tools.values())

    def __repr__(self) -> str:
        tool_count = len(self._tools)
        tag_count = len(self._tags)
        return f"<ToolBox: {tool_count} tools, {tag_count} tags>"

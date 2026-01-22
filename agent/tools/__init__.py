"""Agent 工具模块

提供统一的工具抽象和各种工具实现。

核心概念：
- BaseTool: 异步工具基类
- SyncTool: 同步工具基类
- ToolResult: 统一的返回结果结构
- ToolSchema: 工具描述 Schema，供 LLM 理解
- ToolBox: 工具管理器，用于注册、查找和组织工具

使用示例：
    # 使用工具实例（推荐，带错误处理）
    from agent.tools import recent_group_update_tool
    result = await recent_group_update_tool.execute(hour_gap=24, group_ids=[1, 2])
    if result.success:
        groups, articles = result.data
    else:
        print(f"错误: {result.error}")

    # 使用默认工具箱
    from agent.tools import default_toolbox
    tool = default_toolbox.get("search_memory")
    db_tools = default_toolbox.filter_by_tag("database")
    prompt = default_toolbox.get_prompt()

    # 创建自定义工具箱
    from agent.tools import ToolBox, web_search_tool, search_memory_tool
    my_toolbox = ToolBox()
    my_toolbox.register(web_search_tool, tags=["search"])
    my_toolbox.register(search_memory_tool, tags=["memory"])

    # 使用兼容函数（向后兼容）
    from agent.tools import db_tool
    groups, articles = await db_tool.get_recent_group_update(24, [1, 2], focus="")

    # 获取工具描述供 LLM 使用
    from agent.tools import get_all_tools_prompt, recent_group_update_tool
    prompt = recent_group_update_tool.get_prompt()
"""

# 基类和通用类型导出
import os
from agent.tools.base import (
    BaseTool,
    ToolResult,
    ToolParameter,
    ToolSchema,
    ToolBox,
    ToolType,
    get_all_tools_prompt,
)

# 工具类导出
from agent.tools.db_tool import (
    RecentGroupUpdateTool,
    GetAllFeedsTool,
    GetRecentFeedUpdateTool,
    GetArticleContentTool,
)
from agent.tools.memory_tool import (
    SaveExecutionRecordsTool,
    SearchMemoryTool,
    BackfillEmbeddingsTool,
)
from agent.tools.search_tool import (
    FetchWebContentsTool,
    WebSearchTool,
)
from agent.tools.filter_tool import KeywordExtractorTool
from agent.tools.writing_tool import WriteArticleTool, ReviewArticleTool
from agent.tools.boost_writing_tool import (
    BoostWriteArticleTool,
    BoostReviewArticleTool,
)

# 工具实例导出
from agent.tools.db_tool import (
    recent_group_update_tool,
    get_all_feeds_tool,
    get_recent_feed_update_tool,
    get_article_content_tool,
)
from agent.tools.memory_tool import (
    save_execution_records_tool,
    search_memory_tool,
    backfill_embeddings_tool,
)
from agent.tools.search_tool import (
    fetch_web_contents_tool,
    web_search_tool,
)

# 兼容函数导出（保持向后兼容）
from agent.tools.db_tool import get_recent_group_update, get_article_content
from agent.tools.memory_tool import (
    save_current_execution_records,
    search_memory,
    backfill_embeddings,
)
from agent.tools.search_tool import (
    fetch_web_contents,
    search_web,
    is_search_engine_available,
)
from agent.tools.filter_tool import find_keywords_with_llm


def create_default_toolbox() -> ToolBox:
    """创建预配置的默认工具箱，包含所有内置工具

    Returns:
        配置好的 ToolBox 实例
    """
    toolbox = ToolBox()

    # 数据库相关工具
    toolbox.register(
        recent_group_update_tool, tags=["database", "query", "feed", "group"]
    )
    toolbox.register(get_all_feeds_tool, tags=["database", "query", "feed"])
    toolbox.register(get_recent_feed_update_tool, tags=["database", "query", "feed"])
    toolbox.register(
        get_article_content_tool, tags=["database", "query", "feed", "content"]
    )

    # 记忆相关工具
    toolbox.register(save_execution_records_tool, tags=["database", "memory", "write"])
    toolbox.register(search_memory_tool, tags=["database", "memory", "query", "vector"])
    toolbox.register(
        backfill_embeddings_tool, tags=["database", "memory", "migration", "vector"]
    )

    # 搜索相关工具
    if os.getenv("TAVILY_API_KEY"):
        toolbox.register(fetch_web_contents_tool, tags=["web", "crawler"])
        toolbox.register(web_search_tool, tags=["web", "search"])

    return toolbox


# 默认工具箱实例（不包含需要 client 初始化的工具如 KeywordExtractorTool）
default_toolbox = create_default_toolbox()


__all__ = [
    # 基类和通用类型
    "BaseTool",
    "ToolResult",
    "ToolParameter",
    "ToolSchema",
    "ToolBox",
    "ToolType",
    "get_all_tools_prompt",
    "create_default_toolbox",
    "default_toolbox",
    # 工具类
    "RecentGroupUpdateTool",
    "GetAllFeedsTool",
    "GetRecentFeedUpdateTool",
    "SaveExecutionRecordsTool",
    "SearchMemoryTool",
    "BackfillEmbeddingsTool",
    "FetchWebContentsTool",
    "WebSearchTool",
    "KeywordExtractorTool",
    "WriteArticleTool",
    "ReviewArticleTool",
    "BoostWriteArticleTool",
    "BoostReviewArticleTool",
    # 工具实例
    "recent_group_update_tool",
    "get_all_feeds_tool",
    "get_recent_feed_update_tool",
    "save_execution_records_tool",
    "search_memory_tool",
    "backfill_embeddings_tool",
    "fetch_web_contents_tool",
    "web_search_tool",
    # 兼容函数
    "get_recent_group_update",
    "save_current_execution_records",
    "search_memory",
    "backfill_embeddings",
    "fetch_web_contents",
    "search_web",
    "find_keywords_with_llm",
    "is_search_engine_available",
    "get_article_content",
]

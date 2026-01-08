from typing import Sequence

from psycopg.rows import dict_row

from agent.tools.base import BaseTool, ToolSchema, ToolParameter
from agent.models import AgentState, SummaryMemory
from core.db.pool import execute_async_transaction, get_async_connection


class SaveExecutionRecordsTool(BaseTool[None]):
    """保存当前执行记录的工具"""

    @property
    def name(self) -> str:
        return "save_execution_records"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "将 Agent 的执行记录持久化到数据库。包括两部分数据：\n"
                "1. 已处理的文章ID列表 - 存入 excluded_feed_item_ids 表，防止后续重复处理\n"
                "2. 生成的摘要记忆 - 存入 summary_memories 表，作为历史知识供后续查询"
            ),
            parameters=[
                ToolParameter(
                    name="state",
                    type="AgentState",
                    description=(
                        "Agent 的完整状态对象，包含：\n"
                        "  - raw_articles: 本次处理的原始文章列表\n"
                        "  - plan.focal_points: 规划的焦点主题列表\n"
                        "  - summary_results: 生成的摘要结果列表"
                    ),
                    required=True,
                ),
            ],
            returns="无返回值。执行成功表示数据已持久化到数据库",
            when_to_use=(
                "在 Agent 完成一轮摘要生成后调用，用于：\n"
                "1. 记录已处理的文章，避免下次运行时重复处理相同内容\n"
                "2. 保存生成的摘要作为知识库，供后续查询相关历史信息"
            ),
            usage_examples=[
                "save_execution_records(state) - 在 Agent 执行完成后保存状态",
            ],
            notes=[
                "此操作使用数据库事务，确保两部分数据的原子性写入",
                "如果 raw_articles 或 summary_results 为空，对应部分会被跳过",
                "focal_points 和 summary_results 的数量必须一一对应",
            ],
        )

    async def _execute(self, state: AgentState) -> None:
        """
        保存执行记录

        Args:
            state: Agent状态对象
        """
        excluded_articles = [
            (article["id"], article["pub_date"]) for article in state["raw_articles"]
        ]

        # 安全检查：确保 focal_points 和 summary_results 长度匹配
        focal_points = state.get("plan", {}).get("focal_points", [])
        summary_results = state.get("summary_results", [])

        if len(focal_points) != len(summary_results):
            raise ValueError(
                f"focal_points 数量 ({len(focal_points)}) 与 summary_results 数量 ({len(summary_results)}) 不匹配"
            )

        summary_memories = [
            (point["topic"], point["reasoning"], result)
            for point, result in zip(focal_points, summary_results)
        ]

        async def save_to_db(cur):
            if excluded_articles:
                await cur.executemany(
                    """
                    INSERT INTO excluded_feed_item_ids (id, pub_date)
                    VALUES (%s, %s)
                    """,
                    excluded_articles,
                )
            if summary_memories:
                await cur.executemany(
                    """
                    INSERT INTO summary_memories (topic, reasoning, content)
                    VALUES (%s, %s, %s)
                    """,
                    summary_memories,
                )

        await execute_async_transaction(save_to_db)


class SearchMemoryTool(BaseTool[dict[int, SummaryMemory]]):
    """搜索历史记忆的工具"""

    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "在历史摘要记忆库中搜索相关内容。使用模糊匹配（ILIKE）在 topic 字段中搜索，"
                "返回匹配的历史摘要记录。这对于获取上下文背景、了解历史事件发展、"
                "或避免生成重复内容非常有用。"
            ),
            parameters=[
                ToolParameter(
                    name="queries",
                    type="Sequence[str]",
                    description=(
                        "搜索关键词列表。支持多个关键词同时搜索，使用 OR 逻辑匹配。"
                        "例如 ['OpenAI', 'GPT'] 会匹配包含任一关键词的记忆"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="days_ago",
                    type="int",
                    description="搜索时间范围，单位为天。只返回指定天数内的记忆",
                    required=False,
                    default="30",
                ),
                ToolParameter(
                    name="limit",
                    type="int",
                    description="返回结果的最大数量",
                    required=False,
                    default="10",
                ),
            ],
            returns=(
                "返回 dict[int, SummaryMemory]，键为记忆ID，值为 SummaryMemory 对象，包含：\n"
                "  - id: 记忆唯一标识\n"
                "  - topic: 主题\n"
                "  - reasoning: 生成时的推理过程\n"
                "  - content: 摘要内容"
            ),
            when_to_use=(
                "在以下场景使用此工具：\n"
                "1. 生成新摘要前，查询是否有相关历史内容，避免重复\n"
                "2. 需要了解某个话题的历史背景和发展脉络\n"
                "3. 为当前新闻提供历史上下文补充"
            ),
            usage_examples=[
                "search_memory(queries=['人工智能', 'AI']) - 搜索AI相关的历史记忆",
                "search_memory(queries=['苹果', 'iPhone'], days_ago=7) - 搜索最近7天内苹果相关记忆",
                "search_memory(queries=['特斯拉'], days_ago=90, limit=20) - 搜索90天内特斯拉相关的最多20条记忆",
            ],
            notes=[
                "搜索使用 ILIKE 模糊匹配，不区分大小写",
                "空的关键词会被自动过滤",
                "结果按创建时间降序排列，最新的在前",
                "如果所有关键词都为空，返回空字典",
            ],
        )

    async def _execute(
        self,
        queries: Sequence[str],
        days_ago: int = 30,
        limit: int = 10,
    ) -> dict[int, SummaryMemory]:
        """
        搜索记忆

        Args:
            queries: 搜索关键词序列
            days_ago: 搜索多少天前的记忆
            limit: 返回结果数量限制

        Returns:
            记忆ID到记忆对象的映射
        """
        patterns = [f"%{q}%" for q in queries if q and q.strip()]
        if not patterns:
            return {}

        if days_ago <= 0:
            raise ValueError("days_ago 必须大于 0")

        if limit <= 0:
            raise ValueError("limit 必须大于 0")

        async with get_async_connection() as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    SELECT id, topic, reasoning, content
                    FROM summary_memories
                    WHERE topic ILIKE ANY(%s)
                      AND created_at >= NOW() - (%s * INTERVAL '1 day')
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (patterns, days_ago, limit),
                )
                rows = await cur.fetchall()
                return {row["id"]: SummaryMemory(**row) for row in rows}


# 创建工具实例
save_execution_records_tool = SaveExecutionRecordsTool()
search_memory_tool = SearchMemoryTool()


# 保留原有函数接口以兼容现有代码
async def save_current_execution_records(state: AgentState) -> None:
    """保存当前执行记录（兼容函数）

    注意：此函数为兼容接口，不返回 ToolResult。
    新代码建议使用 save_execution_records_tool.execute() 获取带错误处理的结果。
    """
    result = await save_execution_records_tool.execute(state)
    if not result.success:
        raise RuntimeError(result.error)


async def search_memory(
    queries: Sequence[str],
    days_ago: int = 30,
    limit: int = 10,
) -> dict[int, SummaryMemory]:
    """搜索记忆（兼容函数）

    注意：此函数为兼容接口，直接返回数据而非 ToolResult。
    新代码建议使用 search_memory_tool.execute() 获取带错误处理的结果。
    """
    result = await search_memory_tool.execute(queries, days_ago, limit)
    if result.success:
        return result.data
    raise RuntimeError(result.error)

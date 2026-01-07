from typing import Sequence
from psycopg.rows import dict_row
from agent.models import AgentState, SummaryMemory
from core.db.pool import execute_async_transaction, get_async_connection


async def save_current_execution_records(state: AgentState):
    excluded_articles = [
        (article["id"], article["pub_date"]) for article in state["raw_articles"]
    ]
    summary_memories = [
        (point["topic"], point["reasoning"], result)
        for point, result in zip(
            state["plan"]["focal_points"], state["summary_results"]
        )
    ]
    async def save_to_db(cur):
        # 使用 executemany 批量插入多条记录
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


async def search_memory(
    queries: Sequence[str],
    days_ago: int = 30,
    limit: int = 10,
) -> dict[int, SummaryMemory]:
    patterns = [f"%{q}%" for q in queries if q and q.strip()]
    if not patterns:
        return {}

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

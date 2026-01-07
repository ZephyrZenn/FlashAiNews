from typing import Tuple, List

from core.db.pool import get_async_connection
from core.models.feed import FeedGroup
from agent.models import RawArticle


async def fetch_feed_item_contents(feed_item_ids: list[str]) -> dict[str, str]:
    """
    使用异步连接池获取 feed_item_contents 内容。
    """
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT feed_item_id, content
                FROM feed_item_contents
                WHERE feed_item_id = ANY(%s)
                """,
                (feed_item_ids,),
            )
            rows = await cur.fetchall()
            return {row[0]: row[1] for row in rows}


async def get_recent_group_update(
    hour_gap: int, group_ids: list[int]
) -> Tuple[List[FeedGroup], List[RawArticle]]:
    """
    使用异步连接池获取最近更新的分组及其文章。筛选掉已经使用过的文章
    """
    async with get_async_connection() as conn:
        async with conn.cursor() as cur:
            # 查询 1: 获取 groups（这个保留，因为需要单独返回）
            await cur.execute(
                """SELECT id, title, "desc" FROM feed_groups WHERE id = ANY(%s)""",
                (group_ids,),
            )
            group_rows = await cur.fetchall()
            groups = [
                FeedGroup(id=row[0], title=row[1], desc=row[2]) for row in group_rows
            ]

            if not groups:
                return [], []

            # 查询 2: 一次性获取所有数据，使用 JOIN 和 array_agg
            await cur.execute(
                """
                WITH group_map AS (
                    SELECT
                        fgi.feed_id,
                        array_agg(DISTINCT fg.title) AS group_titles
                    FROM feed_group_items fgi
                    JOIN feed_groups fg ON fg.id = fgi.feed_group_id
                    WHERE fgi.feed_group_id = ANY(%s)
                    GROUP BY fgi.feed_id
                )
                SELECT
                fi.id, fi.title, fi.link, fi.summary, fi.pub_date,
                fic.content,
                gm.group_titles
                FROM feed_items fi
                JOIN group_map gm ON gm.feed_id = fi.feed_id
                JOIN feed_item_contents fic ON fic.feed_item_id = fi.id
                WHERE fi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                AND NOT EXISTS (
                    SELECT 1
                    FROM excluded_feed_item_ids efi
                    WHERE efi.id = fi.id
                    AND efi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                );
                """,
                (group_ids, hour_gap, hour_gap),
            )

            item_rows = await cur.fetchall()
            items = [
                RawArticle(
                    id=row[0],
                    title=row[1],
                    url=row[2],
                    summary=row[3],
                    pub_date=row[4],
                    content=row[5],
                    group_title=row[6],  # 已经是 list[str]
                )
                for row in item_rows
            ]

            return groups, items

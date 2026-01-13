import asyncio
import datetime
import logging

from core.db.pool import get_connection
from core.models.feed import FeedBrief

logger = logging.getLogger(__name__)


def get_briefs(start_date: datetime.date, end_date: datetime.date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, content, created_at, group_ids
                   FROM feed_brief
                   WHERE created_at::date BETWEEN %s AND %s""",
                (start_date, end_date),
            )
            return [FeedBrief(
                id=row[0],
                content=row[1],
                pub_date=row[2],
                group_ids=row[3],
            ) for row in cur.fetchall()]


def generate_brief_for_groups(group_ids: list[int], focus: str = ""):
    """
    Generate brief for specific groups with optional focus.
    Synchronous version for scheduled tasks.
    """
    if not group_ids:
        raise ValueError("group_ids cannot be empty")

    # 延迟导入避免循环依赖
    from agent import get_agent

    logger.info(f"Generating brief for groups {group_ids} with focus: {focus}")
    brief = asyncio.run(get_agent().summarize(24, group_ids, focus))
    _insert_brief(group_ids, brief)
    logger.info("Brief generation completed for groups %s", group_ids)


async def generate_brief_for_groups_async(
    group_ids: list[int], 
    focus: str = "",
    on_step=None
):
    """
    Generate brief for specific groups asynchronously with optional step callback.
    Returns the generated brief content.
    """
    if not group_ids:
        raise ValueError("group_ids cannot be empty")

    # 延迟导入避免循环依赖
    from agent import get_agent

    logger.info(f"Generating brief for groups {group_ids} with focus: {focus}")
    brief = await get_agent().summarize(24, group_ids, focus, on_step=on_step)
    _insert_brief(group_ids, brief)
    logger.info("Brief generation completed for groups %s", group_ids)
    return brief

def _insert_brief(group_ids: list[int], brief: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO feed_brief (group_ids, content) VALUES (%s::integer[], %s)""",
                (group_ids, brief),
            )
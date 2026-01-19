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
    on_step=None,
    boost_mode: bool = False
):
    """
    Generate brief for specific groups asynchronously with optional step callback.
    Returns the generated brief content.
    
    Args:
        group_ids: 分组ID列表（boost_mode 时可以为空）
        focus: 用户关注点
        on_step: 步骤回调函数
        boost_mode: 是否使用 BoostAgent（True）或原 workflow（False）
    """
    # BoostMode 需要填写 focus
    if boost_mode and not focus.strip():
        raise ValueError("focus cannot be empty when boost_mode is true")
    
    # BoostMode 不需要 group_ids，原模式需要至少一个分组
    if not boost_mode and not group_ids:
        raise ValueError("group_ids cannot be empty when boost_mode is false")

    logger.info(f"Generating brief for groups {group_ids} with focus: {focus}, boost_mode: {boost_mode}")
    
    if boost_mode:
        # 使用 BoostAgent（BoostAgent 会自主选择所有可用的订阅源，不受 group_ids 限制）
        from agent import get_boost_agent
        agent = get_boost_agent()
        brief = await agent.run(focus=focus, hour_gap=24, on_step=on_step)
        # BoostMode 时使用空数组作为 group_ids 保存到数据库
        save_group_ids = []
    else:
        # 使用原 workflow
        from agent import get_agent
        brief = await get_agent().summarize(24, group_ids, focus, on_step=on_step)
        save_group_ids = group_ids
    
    _insert_brief(save_group_ids, brief)
    logger.info("Brief generation completed for groups %s", save_group_ids)
    return brief

def _insert_brief(group_ids: list[int], brief: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO feed_brief (group_ids, content) VALUES (%s::integer[], %s)""",
                (group_ids, brief),
            )
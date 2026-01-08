import asyncio
import datetime
import logging
from typing import List, Optional

from core.db.pool import get_connection
from core.models.feed import FeedBrief

logger = logging.getLogger(__name__)


def has_today_brief(group_id: Optional[int] = None) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            params = [datetime.date.today()]
            sql = """
                  SELECT 1
                  FROM feed_brief
                  WHERE created_at::date = %s
                  """
            if group_id is not None:
                sql += " AND group_id = %s"
                params.append(group_id)
            sql += " LIMIT 1"
            cur.execute(sql, tuple(params))
            return cur.fetchone() is not None


def get_today_brief() -> Optional[FeedBrief]:
    sql = """
          SELECT id, group_id, content, created_at
          FROM feed_brief
          WHERE group_id = (SELECT id
                            FROM feed_groups
                            WHERE is_default = TRUE)
            AND created_at::date = CURRENT_DATE
          ORDER BY created_at DESC
          LIMIT 1
          """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            res = cur.fetchone()
            if not res:
                return None
            brief = FeedBrief(
                id=res[0],
                group_id=res[1],
                content=res[2],
                pub_date=res[3],
            )
            return brief


def get_today_all_briefs() -> List[tuple[FeedBrief, str]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT fb.id, fb.content, fb.created_at, fb.group_id, fg.title
                   FROM feed_brief fb,
                        feed_groups fg
                   WHERE fb.group_id = fg.id
                     AND fb.created_at::date = CURRENT_DATE"""
            )
            rows = cur.fetchall()
            return [
                (FeedBrief(id=row[0], content=row[1], pub_date=row[2], group_id=row[3]), row[4])
                for row in rows
            ]


def get_group_brief(group_id: int, date: datetime.date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, content, created_at
                   FROM feed_brief
                   WHERE group_id = %s
                     AND created_at::date = %s""",
                (group_id, date),
            )
            res = cur.fetchone()
            if not res:
                return FeedBrief(
                    id=0,
                    group_id=group_id,
                    content="",
                    pub_date=datetime.datetime.now(),
                )
            return FeedBrief(
                id=res[0],
                group_id=group_id,
                content=res[1],
                pub_date=res[2],
            )


def get_history_brief(group_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, content, created_at
                   FROM feed_brief
                   WHERE group_id = %s
                   ORDER BY created_at DESC""",
                (group_id,),
            )
            rows = cur.fetchall()
            return [
                FeedBrief(
                    id=row[0],
                    group_id=group_id,
                    content=row[1],
                    pub_date=row[2],
                )
                for row in rows
            ]


def get_default_group_briefs() -> Optional[List[FeedBrief]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, content, group_id, created_at
                   FROM feed_brief
                   WHERE group_id = (SELECT id FROM feed_groups WHERE is_default = TRUE)
                   ORDER BY created_at DESC"""
            )
            rows = cur.fetchall()
            if not rows:
                return None
            briefs = [
                FeedBrief(
                    id=row[0],
                    content=row[2],
                    pub_date=row[4],
                    group_id=row[3],
                )
                for row in rows
            ]
            return briefs


def generate_brief_for_groups(group_ids: list[int], focus: str = ""):
    """
    Generate brief for specific groups with optional focus.
    """
    # 延迟导入避免循环依赖
    from agent import get_agent

    logger.info(f"Generating brief for groups {group_ids} with focus: {focus}")
    brief = asyncio.run(get_agent().summarize(24, group_ids, focus))
    # TODO: Do we still need the group?
    _insert_brief(group_ids[0], brief)
    logger.info("Brief generation completed for groups %s", group_ids)

def _insert_brief(group_id: int, brief: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO feed_brief (group_id, content) VALUES (%s, %s)""",
                (group_id, brief),
            )
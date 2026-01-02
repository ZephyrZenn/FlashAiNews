import asyncio
import datetime
import logging
from typing import List, Optional

from apps.backend.db.pool import execute_transaction, get_connection
from apps.backend.services.group_service import get_all_groups_without_today_brief
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


def generate_today_brief():
    # 延迟导入避免循环依赖
    from agent import get_agent

    logger.info("Generating today brief")
    groups = get_all_groups_without_today_brief()
    for group in groups:
        logger.info("Generating brief for group %s", group.id)
        # TODO: hour gap should be configurable
        brief = asyncio.run(get_agent().summarize(24, [group.id]))
        logger.info("Brief generated for group %s", group.id)
        execute_transaction(_insert_brief, group.id, brief)
    logger.info("Today brief generated")


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


def _insert_brief(cur, group_id, brief):
    sql = """
          INSERT INTO feed_brief (group_id, content)
          VALUES (%s, %s) \
          """
    cur.execute(sql, (group_id, brief))

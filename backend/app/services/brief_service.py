import datetime
import logging
from collections import defaultdict
from typing import List, Optional

from app.db.pool import execute_transaction, get_connection
from app.models.feed import FeedArticle, FeedBrief
from app.services.brief_generator import build_generator

logger = logging.getLogger(__name__)


def get_today_brief() -> Optional[FeedBrief]:
    sql = """
          SELECT id, group_id, title, content, created_at
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
                title=res[2],
                content=res[3],
                pub_date=res[4],
            )
            return brief


def get_today_all_briefs() -> List[tuple[FeedBrief, str]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT fb.id, fb.title, fb.content, fb.created_at, fb.group_id, fg.title
                   FROM feed_brief fb,
                        feed_groups fg
                   WHERE fb.group_id = fg.id
                     AND fb.created_at::date = CURRENT_DATE"""
            )
            rows = cur.fetchall()
            return [
                (FeedBrief(id=row[0], title=row[1], content=row[2], pub_date=row[3], group_id=row[4]), row[5])
                for row in rows
            ]


def get_group_brief(group_id: int, date: datetime.date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, content, created_at
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
                    title="There is no update in this group today",
                    content="",
                    pub_date=datetime.datetime.now(),
                )
            return FeedBrief(
                id=res[0],
                group_id=group_id,
                title=res[1],
                content=res[2],
                pub_date=res[3],
            )


def get_history_brief(group_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, content, created_at
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
                    title=row[1],
                    content=row[2],
                    pub_date=row[3],
                )
                for row in rows
            ]


def generate_today_brief():
    logger.info("Generating today brief")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT f.id, f.title, f.link, f.pub_date, f.summary, fic.content, fgi.feed_group_id
                           FROM feed_items f
                                    LEFT JOIN feed_item_contents fic ON f.id = fic.feed_item_id
                                    JOIN feed_group_items fgi ON f.feed_id = fgi.feed_id
                           WHERE fgi.feed_group_id NOT IN (SELECT group_id
                                                           FROM feed_brief
                                                           WHERE created_at::date = CURRENT_DATE)
                             AND f.pub_date::date = CURRENT_DATE;

                        """)
            rows = cur.fetchall()
            articles = defaultdict(list)
            for row in rows:
                group_id = row[6]
                articles[group_id].append(
                    FeedArticle(
                        id=row[0],
                        title=row[1],
                        url=row[2],
                        content=row[5],
                        pub_date=row[3],
                        summary=row[4],
                        has_full_content=True,
                    )
                )
        generator = build_generator()
        for group_id, arts in articles.items():
            if not arts:
                continue
            logger.info("Generating brief for group %s with %d articles", group_id, len(arts))
            brief = generator.sum_up(arts)
            execute_transaction(_insert_brief, group_id, brief)
    logger.info("Today brief generated")


def get_default_group_briefs() -> Optional[List[FeedBrief]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, content, group_id, created_at
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
                    title=row[1],
                    content=row[2],
                    pub_date=row[4],
                    group_id=row[3],
                )
                for row in rows
            ]
            return briefs


def _insert_brief(cur, group_id, brief):
    sql = """
          INSERT INTO feed_brief (group_id, title, content)
          VALUES (%s, %s, %s) \
          """
    cur.execute(sql, (group_id, brief["title"], brief["content"]))

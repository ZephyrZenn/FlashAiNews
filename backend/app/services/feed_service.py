import asyncio
import datetime
import logging
from collections import defaultdict
from typing import Optional

from app.constants import DEFAULT_PROMPT, SUMMARY_LENGTH
from app.crawler import fetch_all_contents
from app.db import execute_transaction, get_connection
from app.models.feed import Feed, FeedArticle, FeedBrief, FeedGroup
from app.parsers import parse_feed, parse_opml
from app.utils import submit_to_thread

from ..exception import BizException
from .brief_generator import build_deepseek_generator

logger = logging.getLogger(__name__)

# A flag to prevent multiple brief generation at the same time
# TODO: Use a more elegant way to handle this
is_generating_brief = False


def import_opml_config(file_url: Optional[str] = None, content: Optional[str] = None):
    if file_url:
        with open(file_url, "r") as f:
            file_text = f.read()
            feeds = parse_opml(file_text)
    elif content:
        feeds = parse_opml(content)
    else:
        raise BizException("No file URL or content provided")

    execute_transaction(_insert_feeds, feeds)


def retrieve_new_feeds(group_ids: list[int] = None):
    """
    Retrieves new feeds from websites and update the databases.
    Args:
      group_ids: The feed group that needs to be updated. If None, all groups will be updated.

    """
    feeds = []
    with get_connection() as conn:
        with conn.cursor() as cur:
            if not group_ids:
                cur.execute("""
                            SELECT id, title, url, last_updated, description, "limit"
                            from feeds
                            """)
                feeds = [
                    Feed(row[0], row[1], row[2], row[3], row[4], row[5])
                    for row in cur.fetchall()
                ]
            else:
                cur.execute(
                    """
                            SELECT id, title, url, last_updated, description, "limit"
                            from feeds
                            where id in (SELECT feed_id
                                         FROM feed_group_items
                                         WHERE id in (%s))
                            """,
                    (tuple(group_ids),),
                )
                feeds = [
                    Feed(row[0], row[1], row[2], row[3], row[4], row[5])
                    for row in cur.fetchall()
                ]
    if not feeds:
        return
    articles = parse_feed(feeds)
    urls = {
        a.url: a for arts in articles.values() for a in arts if not a.has_full_content
    }
    contents = asyncio.run(fetch_all_contents(list(urls.keys())))
    for url, content in contents.items():
        if not content:
            continue
        article = urls[url]
        article.content = content
        if not article.summary:
            article.summary = content[:SUMMARY_LENGTH]

    def insert_new_articles(cursor):
        for feed in feeds:
            if feed.title not in articles:
                continue
            feed_articles = articles[feed.title]
            item_sql = """
                       INSERT INTO feed_items (id, feed_id, title, link, pub_date, summary)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       ON CONFLICT (id) DO NOTHING \
                       """
            item_content_sql = """
                               INSERT INTO feed_item_contents (feed_item_id, content)
                               VALUES (%s, %s)
                               ON CONFLICT (feed_item_id) DO NOTHING \
                               """
            cursor.executemany(
                item_sql,
                [
                    (a.id, feed.id, a.title, a.url, a.pub_date, a.summary)
                    for a in feed_articles
                ],
            )
            cursor.executemany(
                item_content_sql, [(a.id, a.content) for a in feed_articles]
            )
        update_feed_sql = """
                          UPDATE feeds
                          SET last_updated = %s
                          WHERE id = %s \
                          """
        cursor.executemany(
            update_feed_sql, [(datetime.datetime.now(), feed.id) for feed in feeds]
        )

    execute_transaction(insert_new_articles)


def create_group(title: str, desc: str, feed_ids: list[int]):
    def insert_group(cur):
        cur.execute("SELECT EXISTS(SELECT 1 FROM feed_groups LIMIT 1)")
        res = cur.fetchone()
        if not res[0]:
            is_default = True
        else:
            is_default = False
        sql = """
              INSERT INTO feed_groups (title, "desc", is_default)
              VALUES (%s, %s, %s)
              ON CONFLICT (title) DO NOTHING
              RETURNING id \
              """
        cur.execute(sql, (title, desc, is_default))
        res = cur.fetchone()
        if not res:
            return
        gid = res[0]
        _add_feeds_to_group(cur, gid, feed_ids)
        return gid

    return execute_transaction(insert_group)


def join_group(group_id: int, feed_ids: list[str]):
    execute_transaction(_add_feeds_to_group, group_id, feed_ids)


def get_today_brief() -> Optional[FeedBrief]:
    def retrieve_and_generate():
        global is_generating_brief
        try:
            retrieve_new_feeds()
            generate_today_brief()
        except Exception as e:
            logger.error(f"Error retrieving and generating brief: {e}")
        finally:
            is_generating_brief = False

    global is_generating_brief
    sql = """
          SELECT id, group_id, title, content, created_at
          FROM feed_brief
          WHERE group_id = (
              SELECT id
              FROM feed_groups
              WHERE is_default = TRUE
          )
          AND created_at::date = CURRENT_DATE
          ORDER BY created_at DESC
          LIMIT 1
          """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            res = cur.fetchone()
            if not res:
                if is_generating_brief:
                    logger.info("Brief is being generated. Returning None")
                    return (None, None)
                logger.info(
                    "Today brief hasn't generated. Generating brief in background"
                )
                is_generating_brief = True
                submit_to_thread(retrieve_and_generate)
                return (None, None)
            brief = FeedBrief(
                id=res[0],
                group_id=res[1],
                title=res[2],
                content=res[3],
                pub_date=res[4],
            )
            group = get_group_detail(res[1])
            return (brief, group)


def get_group_brief(group_id: int, date: datetime.date):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, content, created_at FROM feed_brief WHERE group_id = %s AND created_at::date = %s""",
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
                """SELECT id, title, content, created_at FROM feed_brief WHERE group_id = %s ORDER BY created_at DESC""",
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
                           WHERE fgi.feed_group_id NOT IN (SELECT feed_group_id
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
        generator = build_deepseek_generator(DEFAULT_PROMPT, "deepseek-reasoner")
        for group_id, arts in articles.items():
            if not arts:
                continue
            brief = generator.sum_up(arts)
            execute_transaction(_insert_brief, group_id, brief)
    logger.info("Today brief generated")


def get_feed_groups():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, "desc" FROM feed_groups ORDER BY is_default DESC, id ASC"""
            )
            return [
                FeedGroup(id=row[0], title=row[1], desc=row[2])
                for row in cur.fetchall()
            ]


def get_group_detail(group_id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, "desc" FROM feed_groups WHERE id = %s""",
                (group_id,),
            )
            res = cur.fetchone()
            if not res:
                raise BizException(f"Group {group_id} not found")
            group = FeedGroup(id=res[0], title=res[1], desc=res[2])
            cur.execute(
                """SELECT id, title, url, last_updated, description, "limit" FROM feeds WHERE id IN (SELECT feed_id FROM feed_group_items WHERE feed_group_id = %s)""",
                (group_id,),
            )
            group.feeds = [
                Feed(
                    id=row[0],
                    title=row[1],
                    url=row[2],
                    last_updated=row[3],
                    desc=row[4],
                    limit=row[5],
                )
                for row in cur.fetchall()
            ]
            return group


def get_all_feeds():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, url, last_updated, description, "limit" FROM feeds"""
            )
            return [
                Feed(
                    id=row[0],
                    title=row[1],
                    url=row[2],
                    last_updated=row[3],
                    desc=row[4],
                    limit=row[5],
                )
                for row in cur.fetchall()
            ]


def update_group(group_id: int, title: str, desc: str, feed_ids: list[int]):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, "desc" FROM feed_groups WHERE id = %s""",
                (group_id,),
            )
            res = cur.fetchone()
            if not res:
                raise BizException(f"Group {group_id} not found")
            cur.execute(
                """SELECT feed_id FROM feed_group_items WHERE feed_group_id = %s""",
                (group_id,),
            )
            existing_feed_ids = [row[0] for row in cur.fetchall()]
            new_feed_ids = [
                feed_id for feed_id in feed_ids if feed_id not in existing_feed_ids
            ]
            removed_feed_ids = [
                feed_id for feed_id in existing_feed_ids if feed_id not in feed_ids
            ]
            logger.info(
                f"Removed feed ids: {removed_feed_ids}, new feed ids: {new_feed_ids}"
            )
            if removed_feed_ids:
                cur.execute(
                    """DELETE FROM feed_group_items WHERE feed_id IN (%s) AND feed_group_id = %s""",
                    (tuple(removed_feed_ids), group_id),
                )
            if new_feed_ids:
                logger.info(f"Adding new feed ids: {new_feed_ids}")
                _add_feeds_to_group(cur, group_id, new_feed_ids)
            cur.execute(
                """UPDATE feed_groups SET title = %s, "desc" = %s WHERE id = %s""",
                (title, desc, group_id),
            )


def get_default_group_briefs():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, title, content, created_at FROM feed_brief WHERE group_id = (SELECT id FROM feed_groups WHERE is_default = TRUE) ORDER BY created_at DESC"""
            )
            rows = cur.fetchall()
            if not rows:
                return None
            cur.execute(
                """
                SELECT id, title, "desc"
                FROM feed_groups
                WHERE is_default = TRUE
                """
            )
            res = cur.fetchone()
            if not res:
                raise BizException("Default group not found")
            group = FeedGroup(id=res[0], title=res[1], desc=res[2])

            briefs = [
                FeedBrief(
                    id=row[0],
                    title=row[1],
                    content=row[2],
                    pub_date=row[3],
                    group_id=group.id,
                )
                for row in rows
            ]
            return (briefs, group)


def _add_feeds_to_group(cur, group_id, feed_ids):
    sql = """
          INSERT INTO feed_group_items (feed_id, feed_group_id)
          VALUES (%s, %s)
          ON CONFLICT DO NOTHING \
          """
    data_to_insert = [(feed_id, group_id) for feed_id in feed_ids]
    cur.executemany(sql, data_to_insert)


def _insert_brief(cur, group_id, brief):
    sql = """
          INSERT INTO feed_brief (group_id, title, content)
          VALUES (%s, %s, %s) \
          """
    cur.execute(sql, (group_id, brief["title"], brief["content"]))


def _insert_feeds(cur, feeds):
    if not feeds:
        return
    insert_sql = """
                  INSERT INTO feeds (title, url, "limit", description, last_updated)
                  VALUES (%s, %s, %s, %s, %s)
                  ON CONFLICT(url) DO NOTHING
                  RETURNING id \
                  """
    data_to_insert = [
        (
            feed.title,
            feed.url,
            feed.limit,
            feed.desc,
            feed.last_updated,
        )
        for feed in feeds
    ]
    cur.executemany(insert_sql, data_to_insert)

import asyncio
import datetime
import logging
from typing import Optional

from core.constants import SUMMARY_LENGTH
from core.crawler import fetch_all_contents
from core.db.pool import execute_transaction, get_connection
from core.models.feed import Feed
from core.parsers import parse_feed, parse_opml

from apps.backend.exception import BizException

logger = logging.getLogger(__name__)


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
                # logger.info("Get feeds: {}", feeds)
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
    cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
    filtered_articles = {}
    for feed_title, feed_articles in articles.items():
        recent_articles = [a for a in feed_articles if a.pub_date >= cutoff]
        if recent_articles:
            filtered_articles[feed_title] = recent_articles
    articles = filtered_articles
    if articles:
        candidate_ids = {
            a.id for feed_articles in articles.values() for a in feed_articles if a.id
        }
        if candidate_ids:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT id FROM feed_items WHERE id = ANY(%s)""",
                        (list(candidate_ids),),
                    )
                    existing_ids = {row[0] for row in cur.fetchall()}
            if existing_ids:
                deduped_articles = {}
                for feed_title, feed_articles in articles.items():
                    unique_articles = [
                        a for a in feed_articles if a.id not in existing_ids
                    ]
                    if unique_articles:
                        deduped_articles[feed_title] = unique_articles
                articles = deduped_articles
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
            logger.info(
                "Retrieving %d articles for feed %s", len(feed_articles), feed.title
            )
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


def add_feed(title: str, description: str, url: str):
    execute_transaction(
        _insert_feeds, [Feed(id=0, title=title, url=url, desc=description)]
    )


def update_feed(id: int, title: str, description: str, url: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE feeds SET title = %s, url = %s, description = %s WHERE id = %s""",
                (title, url, description, id),
            )


def delete_feed(id: int):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""DELETE FROM feeds WHERE id = %s""", (id,))
            cur.execute("""DELETE FROM feed_group_items WHERE feed_id = %s""", (id,))


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

def get_feed_items(hour_gap: int, group_ids: Optional[list[int]]) -> list[dict]:
    """
    Get all feed_items from the last `hour_gap` hours, optionally filtering by feed group IDs.
    Args:
        hour_gap (int): Number of previous hours to look back.
        group_ids (Optional[list[int]]): If provided, only get items from feeds in these group_ids.
    Returns:
        List of feed_items as dicts.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            if group_ids is not None and len(group_ids) > 0:
                sql = """
                    SELECT DISTINCT fi.id, fi.feed_id, fi.title, fi.link, fi.summary, fi.pub_date
                    FROM feed_items fi
                    JOIN feed_group_items fgi ON fi.feed_id = fgi.feed_id
                    WHERE fgi.feed_group_id = ANY(%s)
                        AND fi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                    ORDER BY fi.pub_date DESC
                """
                cur.execute(sql, (group_ids, hour_gap))
            else:
                sql = """
                    SELECT fi.id, fi.feed_id, fi.title, fi.link, fi.summary, fi.pub_date
                    FROM feed_items fi
                    WHERE fi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                    ORDER BY fi.pub_date DESC
                """
                cur.execute(sql, (hour_gap,))
            rows = cur.fetchall()
            return [
                {
                    "id": row[0],
                    "feed_id": row[1],
                    "title": row[2],
                    "link": row[3],
                    "summary": row[4],
                    "pub_date": row[5],
                }
                for row in rows
            ]



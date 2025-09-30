import datetime
import logging
import html2text
from typing import Optional

from app.constants import SUMMARY_LENGTH
from app.crawler import fetch_all_contents
from app.db import execute_transaction, get_connection
from app.models.feed import Feed
from app.parsers import parse_feed, parse_opml

from ..exception import BizException

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
    urls = {
        a.url: a for arts in articles.values() for a in arts if not a.has_full_content
    }
    contents = fetch_all_contents(list(urls.keys()))
    for url, content in contents.items():
        if not content:
            continue
        article = urls[url]
        article.content = content
        if not article.summary:
            article.summary = content[:SUMMARY_LENGTH]

    for _, al in articles.items():
        for article in al:
            article.summary = _html2md(article.summary)
            if article.content:
                article.content = _html2md(article.content)

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


def _html2md(content: str):
    return html2text.html2text(content)

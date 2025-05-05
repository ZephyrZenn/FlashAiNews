import asyncio
import datetime
from typing import Optional

from app.models.feed import RSSFeed, FeedArticle, FeedBrief
from app.parsers import parse_opml, parse_feed
from app.db import get_pool, execute_transaction
from app.crawler import fetch_all_contents
from app.constants import SUMMARY_LENGTH, DEFAULT_PROMPT
from .brief_generator import GeminiGenerator
from ..exception import BizException


def import_opml_config(file_url: str):
    with open(file_url, "r") as f:
        file_text = f.read()
        feeds = parse_opml(file_text)

        def insert_feeds(cur):
            sql = """
                  INSERT INTO feeds (title, url, "limit", description, last_updated)
                  VALUES (%s, %s, %s, %s, %s)
                  ON CONFLICT(url) DO NOTHING
                  RETURNING id \
                  """
            data_to_insert = [
                (feed.title, feed.url, feed.limit, feed.desc, feed.last_updated) for
                feed in feeds]
            cur.executemany(sql, data_to_insert)

    execute_transaction(insert_feeds)


def retrieve_new_feeds(group_ids: list[int] = None):
    """
    Retrieves new feeds from websites and update the databases.
    Args:
      group_ids: The feed group that needs to be updated. If None, all groups will be updated.

    """
    feeds = []
    with get_pool().getconn() as conn:
        with conn.cursor() as cur:
            if not group_ids:
                cur.execute("""
                            SELECT id, title, url, last_updated, description, "limit"
                            from feeds
                            """)
                feeds = [RSSFeed(row[0], row[1], row[2], row[3], row[4], row[5])
                         for row in cur.fetchall()]
            else:
                cur.execute("""
                            SELECT id, title, url, last_updated, description, "limit"
                            from feeds
                            where id in (SELECT feed_id
                                         FROM feed_group_items
                                         WHERE id in (%s))
                            """, (tuple(group_ids),))
                feeds = [RSSFeed(row[0], row[1], row[2], row[3], row[4], row[5])
                         for row in cur.fetchall()]
    if not feeds:
        return
    articles = parse_feed(feeds)
    urls = {a.url: a for arts in articles.values() for a in arts if not a.has_full_content}
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
            cursor.executemany(item_sql, [
                (a.id, feed.id, a.title, a.url,
                 a.pub_date, a.summary) for a in feed_articles
            ])
            cursor.executemany(item_content_sql, [
                (a.id, a.content) for a in feed_articles
            ])
        update_feed_sql = """
                          UPDATE feeds
                          SET last_updated = %s
                          WHERE id = %s \
                          """
        cursor.executemany(update_feed_sql, [
            (datetime.datetime.now(), feed.id) for feed in feeds
        ])

    execute_transaction(insert_new_articles)


def create_group(title: str, desc: str, feed_ids: list[int]):
    def insert_group(cur):
        sql = """
              INSERT INTO feed_groups (title, "desc")
              VALUES (%s, %s)
              ON CONFLICT (title) DO NOTHING
              RETURNING id \
              """
        cur.execute(sql, (title, desc))
        res = cur.fetchone()
        if not res:
            return
        gid = res[0]
        _add_feeds_to_group(cur, gid, feed_ids)

    execute_transaction(insert_group)


def join_group(group_id: int, feed_ids: list[str]):
    execute_transaction(_add_feeds_to_group, group_id, feed_ids)


def generate_brief(group_id: int):
    query_sql = """
                SELECT f.id, f.feed_id, f.title, f.link, f.pub_date, f.summary, fc.content
                FROM feed_items f
                         LEFT JOIN
                     feed_item_contents fc
                     ON f.id = fc.feed_item_id
                         AND f.feed_id IN (SELECT feed_id
                                           FROM feed_group_items
                                           WHERE feed_group_id = %s)
                         AND f.pub_date::date = CURRENT_DATE \
                """
    articles = []
    with get_pool().getconn() as conn:
        with conn.cursor() as cur:
            cur.execute(query_sql, (group_id,))
            rows = cur.fetchall()
            if not rows:
                return
            articles = [
                FeedArticle(id=row[0], title=row[2], url=row[3], content=row[6], pub_date=row[4], summary=row[5],
                            has_full_content=True) for
                row in rows]
    brief = GeminiGenerator(prompt=DEFAULT_PROMPT).sum_up(articles)

    def insert_brief(cur):
        sql = """
              INSERT INTO feed_brief (group_id, title, content)
              VALUES (%s, %s, %s)
              """
        cur.execute(sql, (group_id, brief["title"], brief["content"]))

    execute_transaction(insert_brief)


def get_today_brief() -> Optional[FeedBrief]:
    sql = """
          SELECT id, group_id, title, content, created_at
          FROM feed_brief
          WHERE created_at::date = CURRENT_DATE
          LIMIT 1 \
          """
    with get_pool().getconn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            res = cur.fetchone()
            if not res:
                raise BizException("Brief hasn't been generated yet.")
            return FeedBrief(id=res[0], group_id=res[1], title=res[2], content=res[3], pub_date=res[4])


def _add_feeds_to_group(cur, group_id, feed_ids):
    sql = """
          INSERT INTO feed_group_items (feed_id, feed_group_id)
          VALUES (%s, %s)
          ON CONFLICT DO NOTHING \
          """
    data_to_insert = [
        (feed_id, group_id) for feed_id in feed_ids]
    cur.executemany(sql, data_to_insert)

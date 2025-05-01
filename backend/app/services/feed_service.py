import asyncio
import datetime

from app.models.feed import RSSFeed
from app.parsers import parse_opml, parse_feed
from app.db import get_pool, execute_transaction
from app.crawler import fetch_all_contents


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
        article.summary = content[:300]

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

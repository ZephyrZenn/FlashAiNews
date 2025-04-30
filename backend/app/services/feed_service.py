import datetime

from app.parsers import parse_opml, parse_feed
from app.db import get_pool


def import_opml_config(file_url: str):
  with open(file_url, "r") as f:
    file_text = f.read()
    feeds = parse_opml(file_text)
    with get_pool().getconn() as conn:
      with conn.cursor() as cur:
        cur.execute("""
                    SELECT id, url
                    from feeds
                    where url in (%s)
                    """, (tuple(feed.url for feed in feeds)))
        existing_feeds = {row[1]: row[0] for row in cur.fetchall()}
        sql = """
              INSERT INTO feeds (title, url, "limit", description, last_updated)
              VALUES (%s, %s, %s, %s, %s)
              RETURNING id 
              """
        new_feeds = [feed for feed in feeds if feed.url not in existing_feeds]
        if new_feeds:
          data_to_insert = [(feed.title, feed.url, feed.limit, feed.desc, feed.last_updated) for feed in new_feeds]
          cur.executemany(sql, data_to_insert)
  #   articles = parse_feed(feeds)
  #   for feed in feeds:
  #     feed.articles = articles[feed.title]
  #     feed.last_updated = datetime.datetime.now()
  # if not feeds:
  #   return
  # with get_pool().getconn() as conn:
  #   with conn.cursor() as cur:
  #     cur.execute("""
  #                 SELECT id, url
  #                 from feeds
  #                 where url in (%s)
  #                 """, (tuple(feed.url for feed in feeds)))
  #     existing_urls = {row[1]: row[0] for row in cur.fetchall()}
  #     for feed in feeds:
  #       feed_id = existing_urls.get(feed.url)
  #       if feed.url not in existing_urls:
  #         cur.execute(
  #             """
  #             INSERT INTO feeds (title, url, last_updated, limit, description)
  #             VALUES (%s, %s, %s, %s)
  #             RETURNING id
  #             """,
  #             (feed.title, feed.url, feed.last_updated, feed.limit, feed.desc))
  #         feed_id = cur.fetchone()[0]
  #       for article in feed.articles:
  #         cur.execute(
  #             """
  #             INSERT INTO feed_items (id, title, link, pub_date,
  #                                     feed_id)
  #             VALUES (%s, %s, %s, %s, %s)
  #             """,
  #             (article.id, article.title, article.url,
  #              article.content,
  #              article.pub_date,
  #              feed_id))
  #         cur.execute(
  #             """
  #             INSERT INTO feed_item_contents (feed_item_id, content)
  #             VALUES (%s, %s)
  #             """,
  #             (article.id, article.content)
  #         )

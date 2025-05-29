from app.db.pool import execute_transaction, get_connection
from app.exception import BizException
from app.models.feed import FeedGroup
import logging

from app.models.feed import Feed

logger = logging.getLogger(__name__)


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
                    """DELETE FROM feed_group_items WHERE feed_id IN %s AND feed_group_id = %s""",
                    (tuple(removed_feed_ids), group_id),
                )
            if new_feed_ids:
                logger.info(f"Adding new feed ids: {new_feed_ids}")
                _add_feeds_to_group(cur, group_id, new_feed_ids)
            cur.execute(
                """UPDATE feed_groups SET title = %s, "desc" = %s WHERE id = %s""",
                (title, desc, group_id),
            )


def _add_feeds_to_group(cur, group_id, feed_ids):
    sql = """
          INSERT INTO feed_group_items (feed_id, feed_group_id)
          VALUES (%s, %s)
          ON CONFLICT DO NOTHING \
          """
    data_to_insert = [(feed_id, group_id) for feed_id in feed_ids]
    cur.executemany(sql, data_to_insert)

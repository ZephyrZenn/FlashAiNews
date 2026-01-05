from datetime import datetime, timedelta

from core.crawler import fetch_all_contents
from core.db.pool import get_connection
from core.crawler.search_engine import get_search_client, search
from core.models.feed import FeedGroup
from agent.models import RawArticle
from core.models.search import SearchResult


async def fetch_web_contents(urls: list[str]) -> dict[str, str]:
    return await fetch_all_contents(urls)


def fetch_feed_item_contents(feed_item_ids: list[str]) -> dict[str, str]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT feed_item_id, content FROM feed_item_contents WHERE feed_item_id = ANY(%s)""",
                (feed_item_ids,),
            )
            return {row[0]: row[1] for row in cur.fetchall()}


def get_recent_group_update(
    hour_gap: int, group_ids: list[int]
) -> tuple[list[FeedGroup], list[dict]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 查询 1: 获取 groups（这个保留，因为需要单独返回）
            cur.execute(
                """SELECT id, title, "desc" FROM feed_groups WHERE id = ANY(%s)""",
                (group_ids,),
            )
            groups = [
                FeedGroup(id=row[0], title=row[1], desc=row[2])
                for row in cur.fetchall()
            ]

            if not groups:
                return [], []

            # 查询 2: 一次性获取所有数据，使用 JOIN 和 array_agg
            cur.execute(
                """
                SELECT 
                    fi.id,
                    fi.title,
                    fi.link,
                    fi.summary,
                    fi.pub_date,
                    fic.content,
                    array_agg(DISTINCT fg.title) AS group_titles
                FROM feed_items fi
                JOIN feed_item_contents fic ON fi.id = fic.feed_item_id
                JOIN feed_group_items fgi ON fi.feed_id = fgi.feed_id
                JOIN feed_groups fg ON fgi.feed_group_id = fg.id
                WHERE fgi.feed_group_id = ANY(%s)
                  AND fi.pub_date >= NOW() - INTERVAL '1 hour' * %s
                GROUP BY fi.id, fi.title, fi.link, fi.summary, fi.pub_date, fic.content
                """,
                (group_ids, hour_gap),
            )

            items = [
                RawArticle(
                    id=row[0],
                    title=row[1],
                    url=row[2],
                    summary=row[3],
                    pub_date=row[4],
                    content=row[5],
                    group_title=row[6],  # 已经是 list[str]
                )
                for row in cur.fetchall()
            ]

            return groups, items


def is_search_engine_available() -> bool:
    return get_search_client() is not None


async def search_web(
    query: str,
    recent_days: int = 90,
    max_results: int = 5,
) -> list[SearchResult]:
    start_date = (datetime.now() - timedelta(days=recent_days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    search_results = search(
        query,
        start_date=start_date,
        end_date=end_date,
        max_results=max_results,
    )
    url_map = {result["url"]: result for result in search_results}
    contents = await fetch_all_contents(list(url_map.keys()))

    # 统计抓取结果
    total = len(search_results)
    success = sum(1 for r in search_results if contents.get(r["url"]))
    failed = total - success
    if failed > 0:
        print(f"[SEARCH] 📊 抓取统计: 成功 {success}/{total}, 失败 {failed} 条")

    # 过滤掉获取内容失败的结果
    return [
        SearchResult(
            title=result["title"],
            url=result["url"],
            content=contents.get(result["url"], ""),
            score=result["score"],
        )
        for result in search_results
        if contents.get(result["url"])  # 只保留成功获取内容的结果
    ]

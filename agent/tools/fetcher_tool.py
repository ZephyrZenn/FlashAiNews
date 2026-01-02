from datetime import datetime, timedelta
from typing import Optional
from core.crawler import fetch_all_contents
from apps.backend.db import get_connection
from core.crawler.search_engine import get_search_client, search
from core.models.feed import FeedGroup
from core.models.search import SearchResult
from apps.backend.services import group_service, feed_service


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

def get_group_with_feeds(group_ids: list[int]) -> list[FeedGroup]:
    return group_service.get_group_with_feeds(group_ids)

def get_feed_items(hour_gap: int, group_ids: Optional[list[int]]) -> list[dict]:
    return feed_service.get_feed_items(hour_gap, group_ids)

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

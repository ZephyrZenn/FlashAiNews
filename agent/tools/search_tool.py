from typing import Literal

from core.crawler import fetch_all_contents
from core.crawler.search_engine import get_search_client, search
from core.models.search import SearchResult


async def fetch_web_contents(urls: list[str]) -> dict[str, str]:
    return await fetch_all_contents(urls)


def is_search_engine_available() -> bool:
    return get_search_client() is not None


async def search_web(
    query: str,
    time_range: Literal["day", "week", "month", "year"] = "week",
    max_results: int = 5,
) -> list[SearchResult]:
    search_results = search(
        query,
        time_range=time_range,
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

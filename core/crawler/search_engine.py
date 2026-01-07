import logging
import os
from typing import Literal, Optional
from tavily import TavilyClient

from core.models.search import SearchResult

logger = logging.getLogger(__name__)

class SearchClient:
    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    def search(self, query: str, time_range: Literal["day", "week", "month", "year"] = "week", max_results: int = 5) -> list[dict]:
        # 添加异常兜底策略
        try:
            return self.client.search(query, time_range=time_range, max_results=max_results)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


_search_client: Optional[SearchClient] = None

def get_search_client() -> SearchClient:
    global _search_client
    if not os.getenv("TAVILY_API_KEY"):
        logger.warning("TAVILY_API_KEY is not set. Search engine will not be available.")
        return None
    if _search_client is None:
        _search_client = SearchClient(api_key=os.getenv("TAVILY_API_KEY"))
    return _search_client

def search(query: str, time_range: Literal["day", "week", "month", "year"] = "week", max_results: int = 5) -> list[SearchResult]:
    search_results = get_search_client().search(query, time_range=time_range, max_results=max_results)
    return [SearchResult(title=result["title"], url=result["url"], content=result["content"], score=result["score"]) for result in search_results["results"]]
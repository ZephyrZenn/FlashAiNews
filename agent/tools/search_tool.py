import logging
from typing import Literal

from agent.tools.base import BaseTool, ToolSchema, ToolParameter
from core.crawler import fetch_all_contents
from core.crawler.search_engine import get_search_client, search
from core.models.search import SearchResult

logger = logging.getLogger(__name__)


class FetchWebContentsTool(BaseTool[dict[str, str]]):
    """批量获取网页内容的工具"""

    @property
    def name(self) -> str:
        return "fetch_web_contents"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "批量抓取指定 URL 列表的网页正文内容。使用异步并发请求提高效率，"
                "自动处理各种网页格式，提取主要文本内容并清理 HTML 标签。"
                "返回 dict[str, str]，键为 URL，值为抓取到的网页正文内容。"
                "如果某个 URL 抓取失败，该 URL 对应的值为空字符串。"
            ),
            parameters=[
                ToolParameter(
                    name="urls",
                    type="list[str]",
                    description="需要抓取内容的 URL 列表。支持 HTTP 和 HTTPS 协议",
                    required=True,
                ),
            ],
        )

    async def _execute(self, urls: list[str]) -> dict[str, str]:
        """
        获取网页内容

        Args:
            urls: URL列表

        Returns:
            URL到内容的映射
        """
        if not urls:
            return {}

        return await fetch_all_contents(urls)


class WebSearchTool(BaseTool[list[SearchResult]]):
    """网页搜索工具"""

    @property
    def name(self) -> str:
        return "search_web"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=(
                "使用搜索引擎搜索互联网内容，并自动抓取搜索结果页面的正文。"
                "该工具整合了搜索和内容抓取两个步骤："
                "1. 调用搜索引擎 API 获取搜索结果；"
                "2. 并发抓取所有结果页面的正文内容；"
                "3. 过滤掉抓取失败的结果，只返回有效内容。"
                "返回 list[SearchResult]，每个结果包含 title、url、content（已抓取）、score。"
            ),
            parameters=[
                ToolParameter(
                    name="query",
                    type="str",
                    description=(
                        "搜索查询语句。支持自然语言查询，也支持搜索引擎高级语法。"
                        "建议使用具体、明确的关键词组合以获得更精准的结果"
                    ),
                    required=True,
                ),
                ToolParameter(
                    name="time_range",
                    type="Literal['day', 'week', 'month', 'year']",
                    description=(
                        "搜索结果的时间范围限制："
                        "'day'（过去24小时）、'week'（过去一周）、"
                        "'month'（过去一个月）、'year'（过去一年）"
                    ),
                    required=False,
                    default="week",
                ),
                ToolParameter(
                    name="max_results",
                    type="int",
                    description="期望返回的最大结果数量。实际返回数量可能因抓取失败而减少",
                    required=False,
                    default="5",
                ),
            ],
        )

    async def _execute(
        self,
        query: str,
        time_range: Literal["day", "week", "month", "year"] = "week",
        max_results: int = 5,
    ) -> list[SearchResult]:
        """
        搜索网页

        Args:
            query: 搜索查询
            time_range: 时间范围
            max_results: 最大结果数

        Returns:
            搜索结果列表
        """
        if not query or not query.strip():
            raise ValueError("搜索查询不能为空")

        if max_results <= 0:
            raise ValueError("max_results 必须大于 0")

        # 检查搜索引擎是否可用
        if not get_search_client():
            raise RuntimeError("搜索引擎未配置或不可用，请先检查配置")

        search_results = search(
            query,
            time_range=time_range,
            max_results=max_results,
        )

        if not search_results:
            return []

        url_map = {result["url"]: result for result in search_results}
        contents = await fetch_all_contents(list(url_map.keys()))

        # 统计抓取结果
        total = len(search_results)
        success = sum(1 for r in search_results if contents.get(r["url"]))
        failed = total - success
        if failed > 0:
            logger.info("📊 抓取统计: 成功 %d/%d, 失败 %d 条", success, total, failed)

        # 过滤掉获取内容失败的结果
        return [
            SearchResult(
                title=result["title"],
                url=result["url"],
                content=contents.get(result["url"], ""),
                score=result["score"],
            )
            for result in search_results
            if contents.get(result["url"])
        ]


# 创建工具实例
fetch_web_contents_tool = FetchWebContentsTool()
web_search_tool = WebSearchTool()


# 保留原有函数接口以兼容现有代码
async def fetch_web_contents(urls: list[str]) -> dict[str, str]:
    """获取网页内容（兼容函数）

    注意：此函数为兼容接口，直接返回数据而非 ToolResult。
    新代码建议使用 fetch_web_contents_tool.execute() 获取带错误处理的结果。
    """
    result = await fetch_web_contents_tool.execute(urls)
    if result.success:
        return result.data
    raise RuntimeError(result.error)


async def search_web(
    query: str,
    time_range: Literal["day", "week", "month", "year"] = "week",
    max_results: int = 5,
) -> list[SearchResult]:
    """搜索网页（兼容函数）

    注意：此函数为兼容接口，直接返回数据而非 ToolResult。
    新代码建议使用 web_search_tool.execute() 获取带错误处理的结果。
    """
    result = await web_search_tool.execute(query, time_range, max_results)
    if result.success:
        return result.data
    raise RuntimeError(result.error)

def is_search_engine_available() -> bool:
    """检查搜索引擎是否可用"""
    return get_search_client() is not None
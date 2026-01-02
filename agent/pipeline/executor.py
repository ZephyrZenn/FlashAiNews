import asyncio
from agent.models import AgentState, FocalPoint, RawArticle, WritingMaterial, log_step
from agent.pipeline.writer import AgentWriter
from agent.tools import fetcher_tool


class AgentExecutor:

    def __init__(self, writer: AgentWriter):
        self.writer = writer

    async def execute(self, state: AgentState) -> list[str]:
        plan = state["plan"]
        tasks = []
        log_step(state, f"🔄 开始并行执行 {len(plan['focal_points'])} 个任务...")
        for point in plan["focal_points"]:
            if point["strategy"] == "SUMMARIZE":
                tasks.append(self.handle_summarize(point, state))
            elif point["strategy"] == "SEARCH_ENHANCE":
                tasks.append(self.handle_search_enhance(point, state))
            elif point["strategy"] == "FLASH_NEWS":
                tasks.append(self.handle_flash_news(point, state))
        results = await asyncio.gather(*tasks)
        log_step(state, "✨ 所有任务执行完成")
        return results

    async def handle_summarize(self, point: FocalPoint, state: AgentState) -> str:
        log_step(state, f"📰 [SUMMARIZE] 处理话题: {point['topic']}")
        raw_articles = [
            article
            for article in state["raw_articles"]
            if article["id"] in point["article_ids"]
        ]
        log_step(state, f"   ↳ 获取 {len(raw_articles)} 篇文章内容...")
        raw_articles = await self.fill_content(raw_articles)
        writing_material = WritingMaterial(
            topic=point["topic"],
            style="DEEP",
            writing_guide=point["writing_guide"],
            reasoning=point["reasoning"],
            articles=raw_articles,
        )
        log_step(state, "   ↳ 正在撰写深度内容...")
        result = self.writer.write(writing_material)
        log_step(state, f"   ↳ ✅ 话题 '{point['topic']}' 撰写完成")
        return result

    async def handle_search_enhance(self, point: FocalPoint, state: AgentState) -> str:
        log_step(state, f"🔍 [SEARCH_ENHANCE] 处理话题: {point['topic']}")
        raw_articles = [
            article
            for article in state["raw_articles"]
            if article["id"] in point["article_ids"]
        ]
        log_step(state, f"   ↳ 获取 {len(raw_articles)} 篇文章内容...")
        raw_articles = await self.fill_content(raw_articles)
        log_step(state, f"   ↳ 搜索扩展信息: '{point['search_query']}'")
        search_results = await fetcher_tool.search_web(point["search_query"])
        log_step(state, f"   ↳ 获取到 {len(search_results)} 条搜索结果，正在抓取内容...")
        urls = [result["url"] for result in search_results]
        contents = await fetcher_tool.fetch_web_contents(urls)
        for result in search_results:
            result["content"] = contents[result["url"]]

        writing_material = WritingMaterial(
            topic=point["topic"],
            style="DEEP",
            writing_guide=point["writing_guide"],
            reasoning=point["reasoning"],
            articles=raw_articles,
            ext_info=search_results,
        )
        log_step(state, "   ↳ 正在撰写深度内容...")
        result = self.writer.write(writing_material)
        log_step(state, f"   ↳ ✅ 话题 '{point['topic']}' 撰写完成")
        return result

    async def handle_flash_news(self, point: FocalPoint, state: AgentState) -> str:
        log_step(state, f"⚡ [FLASH_NEWS] 处理话题: {point['topic']}")
        raw_articles = [
            article
            for article in state["raw_articles"]
            if article["id"] in point["article_ids"]
        ]
        log_step(state, f"   ↳ 获取 {len(raw_articles)} 篇文章内容...")
        raw_articles = await self.fill_content(raw_articles)
        writing_material = WritingMaterial(
            topic=point["topic"],
            style="FLASH",
            writing_guide=point["writing_guide"],
            reasoning=point["reasoning"],
            articles=raw_articles,
        )
        log_step(state, "   ↳ 正在生成快讯...")
        result = self.writer.write(writing_material)
        log_step(state, f"   ↳ ✅ 快讯 '{point['topic']}' 生成完成")
        return result

    async def fill_content(self, raw_articles: list[RawArticle]) -> list[RawArticle]:
        contents = fetcher_tool.fetch_feed_item_contents(
            [article["id"] for article in raw_articles]
        )
        for article in raw_articles:
            article["content"] = contents[article["id"]]
        return raw_articles

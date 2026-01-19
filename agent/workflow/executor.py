import asyncio
from agent.models import (
    AgentState,
    FocalPoint,
    WritingMaterial,
    AgentCriticResult,
    log_step,
)
from agent.tools import search_tool, get_article_content
from agent.tools.writing_tool import WriteArticleTool, ReviewArticleTool
from core.brief_generator import AIGenerator


class AgentExecutor:

    def __init__(self, client: AIGenerator, max_retries: int = 3):
        self.client = client
        self.max_retries = max_retries
        self.write_tool = WriteArticleTool(client)
        self.review_tool = ReviewArticleTool(client)

    async def execute(self, state: AgentState) -> list[str]:
        plan = state["plan"]
        article_ids = [
            aid for point in plan["focal_points"] for aid in point["article_ids"]
        ]
        state["raw_articles"] = [
            article for article in state["raw_articles"] if article["id"] in article_ids
        ]

        db_articles = await get_article_content(article_ids)
        for article in state["raw_articles"]:
            if article["id"] in db_articles:
                article["content"] = db_articles[article["id"]]
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
        state["summary_results"] = results
        return results

    async def handle_summarize(self, point: FocalPoint, state: AgentState) -> str:
        log_step(state, f"📰 [SUMMARIZE] 处理话题: {point['topic']}")
        raw_articles = [
            article
            for article in state["raw_articles"]
            if article["id"] in point["article_ids"]
        ]
        log_step(state, f"   ↳ 获取 {len(raw_articles)} 篇文章内容...")
        history_memory = [
            state["history_memories"][hid] for hid in point["history_memory_id"]
        ]
        if history_memory:
            log_step(state, "   ↳ 获取到历史记忆，将历史记忆融入到文章中")
            for memory in history_memory:
                log_step(state, f"   ↳ 历史记忆: {memory['topic']}")
        writing_material = WritingMaterial(
            topic=point["topic"],
            style="DEEP",
            writing_guide=point["writing_guide"],
            reasoning=point["reasoning"],
            articles=raw_articles,
            history_memory=history_memory,
        )
        log_step(state, "   ↳ 正在撰写深度内容...")
        result = await self.write_with_review(writing_material, state, point)
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
        if search_tool.is_search_engine_available():
            log_step(state, f"   ↳ 搜索扩展信息: '{point['search_query']}'")
            search_results = await search_tool.search_web(point["search_query"])
            log_step(
                state, f"   ↳ 获取到 {len(search_results)} 条搜索结果，正在抓取内容..."
            )
            urls = [result["url"] for result in search_results]
            contents = await search_tool.fetch_web_contents(urls)
            for result in search_results:
                result["content"] = contents.get(result["url"], "")
            # 过滤掉抓取失败的结果
            search_results = [r for r in search_results if r.get("content")]
        else:
            log_step(state, "   ↳ 搜索引擎不可用，跳过搜索扩展")
            search_results = []
        history_memory = [
            state["history_memories"][hid] for hid in point["history_memory_id"]
        ]
        if history_memory:
            log_step(state, "   ↳ 获取到历史记忆，将历史记忆融入到文章中")
            for memory in history_memory:
                log_step(state, f"   ↳ 历史记忆: {memory['topic']}")
        writing_material = WritingMaterial(
            topic=point["topic"],
            style="DEEP",
            writing_guide=point["writing_guide"],
            reasoning=point["reasoning"],
            articles=raw_articles,
            ext_info=search_results,
            history_memory=history_memory,
        )
        log_step(state, "   ↳ 正在撰写深度内容...")
        result = await self.write_with_review(writing_material, state, point)
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
        writing_material = WritingMaterial(
            topic=point["topic"],
            style="FLASH",
            writing_guide=point["writing_guide"],
            reasoning=point["reasoning"],
            articles=raw_articles,
        )
        log_step(state, "   ↳ 正在生成快讯...")
        result = await self._write_article(writing_material)
        log_step(state, f"   ↳ ✅ 快讯 '{point['topic']}' 生成完成")
        return result

    async def write_with_review(
        self, writing_material: WritingMaterial, state: AgentState, point: FocalPoint
    ) -> str:
        count = 0
        review = None
        while count < self.max_retries:
            result = await self._write_article(writing_material, review)
            review = await self._review_article(result, writing_material)
            has_critical_error = any(
                finding["severity"] == "CRITICAL" for finding in review["findings"]
            )
            if review["status"] == "APPROVED":
                log_step(state, f"   ↳ ✅ 话题 '{point['topic']}' 通过审查")
                break
            if not has_critical_error and not review["status"] == "REJECTED":
                log_step(
                    state,
                    f"   ↳ ✅ 话题 '{point['topic']}' 通过审查,但有优化建议: {review['overall_comment']}",
                )
                break
            log_step(
                state,
                f"   ↳ ❌ 话题 '{point['topic']}' 未通过审查，原因: {review['decision_logic']}，重试 {count + 1} 次",
            )
            count += 1
        return result

    async def _write_article(
        self, writing_material: WritingMaterial, review: AgentCriticResult | None = None
    ) -> str:
        """使用 WriteArticleTool 撰写文章"""
        # history_memory 现在统一为列表
        history_memory = writing_material.get("history_memory")
        if history_memory and not isinstance(history_memory, list):
            history_memory = [history_memory]

        result = await self.write_tool.execute(
            topic=writing_material["topic"],
            style=writing_material["style"],
            writing_guide=writing_material["writing_guide"],
            reasoning=writing_material["reasoning"],
            articles=writing_material["articles"],
            ext_info=writing_material.get("ext_info"),
            history_memory=history_memory,
            review=review,
        )
        if result.success:
            return result.data
        raise RuntimeError(f"写作失败: {result.error}")

    async def _review_article(
        self, draft_content: str, material: WritingMaterial
    ) -> AgentCriticResult:
        """使用 ReviewArticleTool 审查文章"""
        # history_memory 现在统一为列表
        history_memory = material.get("history_memory")
        if history_memory and not isinstance(history_memory, list):
            history_memory = [history_memory]

        result = await self.review_tool.execute(
            draft_content=draft_content,
            topic=material["topic"],
            writing_guide=material["writing_guide"],
            articles=material["articles"],
            ext_info=material.get("ext_info"),
            history_memory=history_memory,
        )
        if result.success:
            return result.data
        raise RuntimeError(f"审查失败: {result.error}")

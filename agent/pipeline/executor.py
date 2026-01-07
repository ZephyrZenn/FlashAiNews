import asyncio
from agent.models import AgentState, FocalPoint, WritingMaterial, log_step
from agent.pipeline.critic import AgentCritic
from agent.pipeline.writer import AgentWriter
from agent.tools import search_tool
from core.brief_generator import AIGenerator


class AgentExecutor:

    def __init__(self, client: AIGenerator, max_retries: int = 2):
        self.writer = AgentWriter(client)
        self.critic = AgentCritic(client)
        self.max_retries = max_retries

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
        history_memory = [
            state["history_memories"][hid]
            for hid in point["history_memory_id"]
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
        result = self.write_with_review(writing_material, state, point)
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
                result["content"] = contents[result["url"]]
        else:
            log_step(state, "   ↳ 搜索引擎不可用，跳过搜索扩展")
            search_results = []
        history_memory = [
            state["history_memories"][hid]
            for hid in point["history_memory_id"]
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
        result = self.write_with_review(writing_material, state, point)
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
        result = self.writer.write(writing_material)
        log_step(state, f"   ↳ ✅ 快讯 '{point['topic']}' 生成完成")
        return result

    def write_with_review(
        self, writing_material: WritingMaterial, state: AgentState, point: FocalPoint
    ) -> str:
        count = 0
        review = None
        while count < self.max_retries:
            result = self.writer.write(writing_material, review)
            review = self.critic.critic(result, writing_material)
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
                f"   ↳ ❌ 话题 '{point['topic']}' 未通过审查，原因: {review}，重试 {count + 1} 次",
            )
            count += 1
        return result

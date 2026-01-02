from collections import defaultdict
from typing import Optional
from agent.pipeline.planner import AgentPlanner
from agent.pipeline.executor import AgentExecutor
from agent.pipeline.writer import AgentWriter
from agent.models import AgentState, RawArticle, StepCallback, log_step
from agent.tools import fetcher_tool
from core.pipeline.brief_generator import build_generator


class SummarizeAgent:
    def __init__(self):
        client = build_generator()
        self.planner = AgentPlanner(client)
        self.executor = AgentExecutor(AgentWriter(client))
        self.state = None

    async def summarize(
        self,
        hour_gap: int,
        group_ids: Optional[list[int]],
        on_step: Optional[StepCallback] = None,
    ):
        self.state = self._build_state(hour_gap, group_ids, on_step)
        log_step(self.state, f"🚀 Agent启动，获取到 {len(self.state['raw_articles'])} 篇文章")

        log_step(self.state, "📋 开始规划阶段...")
        self.planner.plan(self.state)

        log_step(self.state, "⚡ 开始执行阶段...")
        results = await self.executor.execute(self.state)

        log_step(self.state, f"✅ Agent执行完成，共生成 {len(results)} 篇内容")
        return "\n\n".join(results)

    def _build_state(
        self,
        hour_gap: int,
        group_ids: Optional[list[int]],
        on_step: Optional[StepCallback] = None,
    ) -> AgentState:
        groups = fetcher_tool.get_group_with_feeds(group_ids)
        feed_group_map: dict[int, list] = defaultdict(list)
        for group in groups:
            for feed in group.feeds:
                feed_group_map[feed.id].append(group.title)
        articles = fetcher_tool.get_feed_items(hour_gap, group_ids)
        raw_articles = [
            RawArticle(
                id=article["id"],
                title=article["title"],
                url=article["link"],
                group_title=feed_group_map.get(article["feed_id"]),
                summary=article["summary"],
            )
            for article in articles
        ]
        state = AgentState(groups=groups, raw_articles=raw_articles, history=[])
        if on_step:
            state["on_step"] = on_step
        return state
    
    def get_history(self) -> list[str]:
        return self.state["history"]

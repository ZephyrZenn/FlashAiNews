from collections import defaultdict
from typing import Optional
from agent.pipeline.planner import AgentPlanner
from agent.pipeline.executor import AgentExecutor
from agent.models import AgentState, StepCallback, log_step
from agent.tools import fetcher_tool
from core.brief_generator import build_generator


class SummarizeAgent:
    def __init__(self):
        client = build_generator()
        self.planner = AgentPlanner(client)
        self.executor = AgentExecutor(client)
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
        groups, articles = fetcher_tool.get_recent_group_update(hour_gap, group_ids)
        state = AgentState(groups=groups, raw_articles=articles, history=[])
        if on_step:
            state["on_step"] = on_step
        return state

    def get_history(self) -> list[str]:
        return self.state["history"]


# 单例实例
_agent_instance: Optional[SummarizeAgent] = None


def init_agent() -> SummarizeAgent:
    """应用启动时调用，初始化 Agent 单例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SummarizeAgent()
    return _agent_instance


def get_agent() -> SummarizeAgent:
    """获取 Agent 单例实例"""
    if _agent_instance is None:
        raise RuntimeError("Agent 未初始化，请先调用 init_agent()")
    return _agent_instance

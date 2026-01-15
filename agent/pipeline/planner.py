import logging
from datetime import datetime
import json
from agent.models import AgentPlanResult, AgentState, log_step
from agent.pipeline.prompt import (
    GLOBAL_PLANNER_PROMPT_TEMPLATE,
    GROUP_PLANNER_PROMPT_TEMPLATE,
)
from core.brief_generator import AIGenerator
from agent.utils import extract_json
from agent.tools import filter_tool, memory_tool

logger = logging.getLogger(__name__)


class AgentPlanner:
    def __init__(self, client: AIGenerator):
        self.client = client

    async def plan(self, state: AgentState) -> AgentPlanResult:
        result = None
        keywords = await filter_tool.find_keywords_with_llm(
            self.client, state["raw_articles"]
        )
        log_step(state, f"🔍 提取到 {len(keywords)} 个关键词: {keywords}")
        memories = await memory_tool.search_memory(keywords)
        memory_topics = [m["topic"] for m in memories.values()] if memories else []
        log_step(state, f"🔍 从记忆中找到 {len(memories)} 个相关记忆: {memory_topics}")
        state["history_memories"] = memories

        log_step(state, "🤖 正在调用LLM进行规划...")
        prompt = self._build_prompt(state)
        logger.info("Sending planner prompt to LLM: %s", prompt)
        response = await self.client.completion(prompt)
        logger.info("Received planner response from LLM: %s", response)
        try:
            result: AgentPlanResult = extract_json(response)
            logger.info("Parsed planner response: %s", result)
            for point in result["focal_points"]:
                point["article_ids"] = [str(aid) for aid in point["article_ids"]]
            state["plan"] = result
            focal_points = result.get("focal_points", [])
            discarded = result.get("discarded_items", [])
            log_step(
                state,
                f"📝 规划完成：识别出 {len(focal_points)} 个焦点话题，丢弃 {len(discarded)} 篇文章",
            )
            for i, point in enumerate(focal_points, 1):
                log_step(state, f"   {i}. [{point['strategy']}] {point['topic']}")
            return result
        except json.JSONDecodeError as e:
            log_step(state, "❌ 规划失败：无法解析LLM响应")
            logger.error("Failed to parse planner response: %s", response)
            raise ValueError(f"Failed to parse planner response: {response}") from e

    def _build_prompt(self, state: AgentState) -> str:
        history_memories = [
            {
                "id": memory["id"],
                "topic": memory["topic"],
                "reasoning": memory["reasoning"],
            }
            for memory in state["history_memories"].values()
        ]
        template = (
            GROUP_PLANNER_PROMPT_TEMPLATE
            if len(state["groups"]) == 1
            else GLOBAL_PLANNER_PROMPT_TEMPLATE
        )
        return template.format(
            current_date=datetime.now().strftime("%Y-%m-%d"),
            focus=state["focus"],
            raw_articles=state["raw_articles"],
            history_memories=history_memories,
        )

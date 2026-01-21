import logging
from datetime import datetime
import json
from agent.context import ContentOptimizer
from agent.models import AgentPlanResult, AgentState, log_step
from agent.prompts import PLANNER_PROMPT_TEMPLATE
from agent.utils import extract_json
from agent.tools import filter_tool, memory_tool
from core.brief_generator import AIGenerator
from core.config import get_config

logger = logging.getLogger(__name__)


class AgentPlanner:
    def __init__(self, client: AIGenerator):
        self.client = client
        # 初始化内容优化器（传入client以支持LLM关键词提取）
        config = get_config()
        context_cfg = config.context
        self.content_optimizer = ContentOptimizer(
            article_max_length=context_cfg.article_max_length,
            summary_max_length=context_cfg.summary_max_length,
            memory_max_length=context_cfg.memory_max_length,
            client=client,  # 传入client以支持LLM关键词提取
        )

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
        prompt = await self._build_prompt(state)
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

    async def _build_prompt(self, state: AgentState) -> str:
        # 优化文章内容：去重、优先级排序、截断（现在是异步）
        optimized_articles = await self.content_optimizer.optimize_articles_for_prompt(
            state["raw_articles"],
            focus=state.get("focus", ""),
            # 函数会自动检测文章是否有完整内容，无需手动指定
        )

        # 格式化文章为JSON字符串（只包含关键信息）
        articles_json = json.dumps(
            [
                {
                    "id": str(a.get("id", "")),
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "summary": self.content_optimizer.truncate_text(
                        a.get("summary", ""), self.content_optimizer.summary_max_length
                    ),
                    "pub_date": str(a.get("pub_date", "")),
                }
                for a in optimized_articles
            ],
            ensure_ascii=False,
            indent=2,
        )

        # 优化历史记忆
        history_memories_list = list(state["history_memories"].values())
        optimized_memories = self.content_optimizer.truncate_memories(
            history_memories_list
        )

        history_memories = [
            {
                "id": memory["id"],
                "topic": memory["topic"],
                "reasoning": self.content_optimizer.truncate_text(
                    memory.get("reasoning", ""), 200
                ),
            }
            for memory in optimized_memories
        ]

        return PLANNER_PROMPT_TEMPLATE.format(
            current_date=datetime.now().strftime("%Y-%m-%d"),
            focus=state["focus"],
            raw_articles=articles_json,
            history_memories=json.dumps(history_memories, ensure_ascii=False, indent=2),
        )

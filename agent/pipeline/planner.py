import logging
import re
from datetime import datetime
import json
from agent.models import AgentPlanResult, AgentState, log_step
from agent.pipeline.prompt import GLOBAL_PLANNER_PROMPT_TEMPLATE, GROUP_PLANNER_PROMPT_TEMPLATE
from core.brief_generator import AIGenerator

logger = logging.getLogger(__name__)


def extract_json(text: str) -> dict:
    """
    Extract JSON from LLM response, handling:
    - Pure JSON text
    - Markdown code blocks (```json ... ``` or ``` ... ```)
    """
    text = text.strip()

    # Try to extract from markdown code block
    # Pattern matches ```json, ```JSON, or just ```
    pattern = r"```(?:json|JSON)?\s*\n?([\s\S]*?)\n?```"
    match = re.search(pattern, text)
    if match:
        json_str = match.group(1).strip()
    else:
        # Assume it's pure JSON
        json_str = text

    return json.loads(json_str)


class AgentPlanner:
    def __init__(self, client: AIGenerator):
        self.client = client

    def plan(self, state: AgentState) -> None:
        log_step(state, "🤖 正在调用LLM进行规划...")
        prompt = self._build_prompt(state)
        # logger.info(f"Sending planner prompt to LLM: {prompt}")
        print(f"Sending planner prompt to LLM: {prompt}")
        response = self.client.completion(prompt)
        # logger.info(f"Received planner response from LLM: {response}")
        print(f"Received planner response from LLM: {response}")
        try:
            result: AgentPlanResult = extract_json(response)
            logger.info("Parsed planner response: %s", result)
            state["plan"] = result
            focal_points = result.get("focal_points", [])
            discarded = result.get("discarded_items", [])
            log_step(state, f"📝 规划完成：识别出 {len(focal_points)} 个焦点话题，丢弃 {len(discarded)} 篇文章")
            for i, point in enumerate(focal_points, 1):
                log_step(state, f"   {i}. [{point['strategy']}] {point['topic']}")
        except json.JSONDecodeError as e:
            log_step(state, "❌ 规划失败：无法解析LLM响应")
            logger.error("Failed to parse planner response: %s", response)
            raise ValueError(f"Failed to parse planner response: {response}") from e

    def _build_prompt(self, state: AgentState) -> str:
        raw_articles = "\n".join(
            [
                f"{article['id']} | {article['title']} | {article['group_title']} | {article['summary']}"
                for article in state["raw_articles"]
            ]
        )
        if len(state["groups"]) == 1:
            return GROUP_PLANNER_PROMPT_TEMPLATE.format(
                current_date=datetime.now().strftime("%Y-%m-%d"),
                group_title=state["groups"][0].title,
                group_desc=state["groups"][0].desc,
                raw_articles=raw_articles,
            )
        else:
            return GLOBAL_PLANNER_PROMPT_TEMPLATE.format(
                current_date=datetime.now().strftime("%Y-%m-%d"),
                user_groups=",".join([group.title for group in state["groups"]]),
                raw_articles=raw_articles,
            )

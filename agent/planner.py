import logging
import re
from datetime import datetime
import json
from agent.models import AgentPlanResult, AgentState
from agent.prompt import PLANNER_PROMPT_TEMPLATE
from core.pipeline.brief_generator import AIGenerator

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

    def plan(self, state: AgentState) -> AgentPlanResult:
        user_groups = ",".join([group.title for group in state['groups']])
        raw_articles = "\n".join(
            [f"{article['id']} | {article['title']} | {article['group_title']} | {article['summary']}" for article in state["raw_articles"]])
        prompt = PLANNER_PROMPT_TEMPLATE.format(
            current_date=datetime.now().strftime("%Y-%m-%d"),
            user_groups=user_groups,
            raw_articles=raw_articles,
        )
        # logger.info(f"Sending planner prompt to LLM: {prompt}")
        print(f"Sending planner prompt to LLM: {prompt}")
        response = self.client.completion(prompt)
        # logger.info(f"Received planner response from LLM: {response}")
        print(f"Received planner response from LLM: {response}")
        try:
            result: AgentPlanResult = extract_json(response)
            logger.info("Parsed planner response: %s", result)
            return result
        except json.JSONDecodeError as e:
            logger.error("Failed to parse planner response: %s", response)
            raise ValueError(f"Failed to parse planner response: {response}") from e

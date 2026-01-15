from agent.models import AgentCriticResult, WritingMaterial
from core.brief_generator import AIGenerator
from agent.pipeline.prompt import CRITIC_PROMPT_TEMPLATE
from agent.utils import extract_json
import logging

logger = logging.getLogger(__name__)


class AgentCritic:
    def __init__(self, client: AIGenerator):
        self.client = client

    async def critic(self, draft_content: str, material: WritingMaterial):
        source_material = {
            "articles": material["articles"],
            "ext_info": material.get("ext_info", []),
        }
        history_memories = material.get("history_memory", [])
        prompt = CRITIC_PROMPT_TEMPLATE.format(
            draft_content=draft_content,
            source_material=source_material,
            original_guide=material["writing_guide"],
            history_memories=history_memories,
        )
        response = await self.client.completion(prompt)
        try:
            result: AgentCriticResult = extract_json(response)
            logger.info(
                "Parsed critic response successfully, status: %s", result.get("status")
            )
            return result
        except Exception as e:
            # Log a truncated version to avoid huge log entries
            response_preview = (
                response[:500] + "..." if len(response) > 500 else response
            )
            logger.error(
                "Failed to parse critic response. Error: %s\nResponse preview: %s",
                str(e),
                response_preview,
                exc_info=True,
            )
            raise ValueError(f"Failed to parse critic response: {str(e)}") from e

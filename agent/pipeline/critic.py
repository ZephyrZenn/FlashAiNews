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
        source = "\n".join(f"{article}" for article in material["articles"])
        if "ext_info" in material and material["ext_info"]:
            source += "\n".join(f"{result}" for result in material["ext_info"])
        guide = material["writing_guide"]
        history_memory = "\n".join(
            f"{memory['id']} | {memory['topic']} | {memory['reasoning']} | {memory['content']}"
            for memory in material["history_memory"]
        )
        prompt = CRITIC_PROMPT_TEMPLATE.format(
            draft_content=draft_content,
            source_material=source,
            original_guide=guide,
            history_memories=history_memory,
        )
        response = await self.client.completion(prompt)
        try:
            result: AgentCriticResult = extract_json(response)
            logger.info("Parsed critic response: %s", result)
            return result
        except Exception as e:
            logger.error("Failed to parse critic response: %s", response, exc_info=True)
            raise ValueError(f"Failed to parse critic response: {response}") from e

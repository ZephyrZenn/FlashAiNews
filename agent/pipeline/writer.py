from core.brief_generator import AIGenerator
from agent.models import AgentCriticResult, WritingMaterial
from agent.pipeline.prompt import (
    WRITER_FLASH_NEWS_PROMPT,
    WRITER_DEEP_DIVE_PROMPT_TEMPLATE,
)


class AgentWriter:
    def __init__(self, client: AIGenerator):
        self.client = client

    async def write(
        self, writing_material: WritingMaterial, review: AgentCriticResult | None = None
    ):
        prompt = self._build_prompt(writing_material, review)
        response = await self.client.completion(prompt)
        return response

    def _build_prompt(
        self, writing_material: WritingMaterial, review: AgentCriticResult | None = None
    ) -> str:
        if writing_material["style"] == "FLASH":
            return WRITER_FLASH_NEWS_PROMPT.format(
                topic=writing_material["topic"],
                articles=writing_material["articles"],
            )

        ext_info = (
            writing_material["ext_info"]
            if "ext_info" in writing_material and writing_material["ext_info"]
            else []
        )
        history_memories = writing_material.get("history_memory", [])

        return WRITER_DEEP_DIVE_PROMPT_TEMPLATE.format(
            topic=writing_material["topic"],
            writing_guide=writing_material["writing_guide"],
            reasoning=writing_material["reasoning"],
            articles=writing_material["articles"],
            ext_info=ext_info,
            review=review if review else "",
            history_memories=history_memories,
        )

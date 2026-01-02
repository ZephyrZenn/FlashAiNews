from core.brief_generator import AIGenerator
from agent.models import WritingMaterial
from agent.pipeline.prompt import WRITER_FLASH_NEWS_PROMPT, WRITER_PROMPT_TEMPLATE


class AgentWriter:
    def __init__(self, client: AIGenerator):
        self.client = client

    def write(self, writing_material: WritingMaterial):
        prompt = self._build_prompt(writing_material)
        response = self.client.completion(prompt)
        return response

    def _build_prompt(self, writing_material: WritingMaterial) -> str:
        if writing_material["style"] == "FLASH":
            return WRITER_FLASH_NEWS_PROMPT.format(
                articles_content="\n\n".join(
                    f"{article['title']}\n{article['content']}"
                    for article in writing_material["articles"]
                ),
            )
        ext_info = (
            "\n\n".join(
                f"[{result['title']}]({result['url']}) - {result['content']}"
                for result in writing_material["ext_info"]
            )
            if "ext_info" in writing_material and writing_material["ext_info"]
            else ""
        )
        return WRITER_PROMPT_TEMPLATE.format(
            topic=writing_material["topic"],
            writing_guide=writing_material["writing_guide"],
            reasoning=writing_material["reasoning"],
            raw_content="\n\n".join(
                f"{article['title']}\n{article['content']}"
                for article in writing_material["articles"]
            ),
            ext_info=ext_info,
        )

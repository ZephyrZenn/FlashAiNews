import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

from google import genai
from google.genai import types
from openai import OpenAI

from app.config import llm
from app.models.feed import FeedArticle
from app.models.generator import GeneratorType

logger = logging.getLogger(__name__)

"""Brief generator for summarizing articles using AI models.
This module provides an abstract base class for AI generators and concrete implementations"""


class AIGenerator(ABC):
    def __init__(
        self, prompt: str, api_key: str, base_url: str, model: str, limit: int = 5
    ):
        """
        Initialize the AIGenerator with a prompt and limit.
        Args:
            prompt (str): The prompt to use for summarization.
            limit (int): The maximum number of articles to summarize.
            api_key (str): The API key for the AI service.
            base_url (str): The base URL for the AI service.
            model (str): The model to use for summarization.
        """
        self.prompt = prompt
        self.limit = limit
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    def sum_up(self, articles: list[FeedArticle]) -> dict[str, str]:
        """
        Summarize the articles using Gemini API.
        Args:
            articles (list[FeedArticle]): List of articles to summarize.
        Returns:
            dict[str, str]: A dictionary containing the title and content of the summary.
        """
        raise NotImplementedError()


class GeminiGenerator(AIGenerator):
    def __init__(self, prompt: str, api_key: str, model: str, limit: int = 5):
        super().__init__(prompt, api_key, base_url=None, model=model, limit=limit)

    def sum_up(self, articles: list[FeedArticle]) -> dict[str, str]:
        try:
            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(api_version="v1alpha"),
            )

            input_articles = _format_articles(articles, self.limit)
            inputs = f"{self.prompt}\n ----Input Articles---- \n{input_articles}"
            resp = client.models.generate_content(
                model="gemini-2.0-flash", contents=inputs
            )
            return _extract_json(resp.text)
        except Exception as e:
            logger.error(f"Error in GeminiGenerator: {e}")
            raise e


class OpenAIGenerator(AIGenerator):
    def __init__(self, prompt, base_url, model, api_key, limit=5):
        super().__init__(
            prompt=prompt, base_url=base_url, model=model, api_key=api_key, limit=limit
        )

    def sum_up(self, articles: list[FeedArticle]) -> dict[str, str]:
        try:
            input_articles = _format_articles(articles, self.limit)
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            logger.info("Generating summary for articles.")
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": input_articles},
                ],
                stream=False,
            )
            logger.info("Summary generated successfully.")
            return _extract_json(resp.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in OpenAIGenerator: {e}")
            raise e


def build_generator(model_name: str = None) -> AIGenerator:
    name, model = llm.get_model(model_name)
    prompt = llm.get_prompt()
    # TODO: Limit is not used
    return _build_generator(
        generator_type=GeneratorType(model["provider"]),
        prompt=prompt,
        api_key=model["api_key"],
        base_url=model["base_url"],
        model=model["model"],
        limit=5,
    )


def _build_generator(
    generator_type: GeneratorType,
    prompt: str,
    api_key: str,
    base_url: Optional[str],
    model: str,
    limit: int = 5,
) -> AIGenerator:
    """
    Build an AI generator based on the model type.
    Args:
        generator_type (GeneratorType): The type of generator to create
        prompt (str): The prompt to use for summarization.
        api_key (str): The API key for the AI service.
        base_url (str): The base URL for the AI service.
        model (str): The model to use for summarization.
        limit (int): The maximum number of articles to summarize.
    Returns:
        AIGenerator: An instance of the appropriate AIGenerator subclass.
    """
    if generator_type == GeneratorType.GEMINI:
        return GeminiGenerator(prompt=prompt, api_key=api_key, model=model, limit=limit)
    elif (
        generator_type == GeneratorType.DEEPSEEK
        or generator_type == GeneratorType.OPENAI
    ):
        return OpenAIGenerator(
            prompt=prompt, base_url=base_url, model=model, api_key=api_key, limit=limit
        )
    else:
        raise ValueError(f"Unsupported generator type: {generator_type}")


def _format_articles(articles: list[FeedArticle], limit: int) -> str:
    """
    Format the articles into a string for the AI model.
    Args:
        articles (list[FeedArticle]): List of articles to format.
    Returns:
        str: Formatted string of articles.
    """
    input_articles = json.dumps(
        list(
            map(
                lambda x: {
                    "title": x.title,
                    "content": x.content if x.content else x.summary,
                },
                articles[:limit],
            )
        )
    )

    return input_articles


def _extract_json(text: str) -> dict[str, str]:
    pattern = r"```json\s*(\{.*?\}|\[.*?\])\s*```"
    matches = re.findall(pattern, text, re.DOTALL)

    json_objects = []
    for match in matches:
        try:
            obj = json.loads(match)
            json_objects.append(obj)
        except json.JSONDecodeError as e:
            print(f"Failed to parse json: {e}, Text: {text}")
            continue
    if not json_objects or len(json_objects) == 0:
        raise ValueError(f"Failed to parse json {json_objects}. Text: {text}")
    ans = json_objects[0]
    return {
        "title": ans.get("title", ""),
        "content": ans.get("content", ""),
    }

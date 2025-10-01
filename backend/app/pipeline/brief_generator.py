import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

from google import genai
from google.genai import types
from openai import OpenAI

from app.config.loader import get_config
from app.models.feed import FeedArticle
from app.models.generator import ModelProvider

logger = logging.getLogger(__name__)

"""Brief generator for summarizing articles using AI models.
This module provides an abstract base class for AI generators and concrete implementations"""


class AIGenerator(ABC):
    def __init__(
        self, api_key: str, base_url: Optional[str], model: str
    ):
        """
        Initialize the AIGenerator with a prompt and limit.
        Args:
            api_key (str): The API key for the AI service.
            base_url (str): The base URL for the AI service.
            model (str): The model to use for summarization.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        
    @abstractmethod
    def completion(self, prompt, **kwargs) -> str:
        raise NotImplementedError() 


class GeminiGenerator(AIGenerator):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key=api_key, base_url=None, model=model)
        
    def completion(self, prompt, **kwargs) -> str:
        try:
            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(api_version="v1alpha"),
            )
            resp = client.models.generate_content(
                model=self.model, contents=prompt
            )
            return resp.text
        except Exception as e:
            logger.error(f"Error in GeminiGenerator: {e}")
            raise e


class OpenAIGenerator(AIGenerator):
    def __init__(self, base_url, model, api_key):
        super().__init__(
            base_url=base_url, model=model, api_key=api_key
        )
    
    def completion(self, prompt, **kwargs) -> str:
        try:
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in OpenAIGenerator: {e}")
            raise e


def build_generator() -> AIGenerator:
    config = get_config()
    model_cfg = config.models[config.global_.default_model]
    return _build_generator(
        generator_type=model_cfg.provider,
        api_key=model_cfg.api_key,
        base_url=model_cfg.base_url,
        model=model_cfg.model,
    )


def _build_generator(
    generator_type: ModelProvider,
    api_key: str,
    base_url: Optional[str],
    model: str,
) -> AIGenerator:
    """
    Build an AI generator based on the model type.
    Args:
        generator_type (GeneratorType): The type of generator to create
        api_key (str): The API key for the AI service.
        base_url (str): The base URL for the AI service.
        model (str): The model to use for summarization.
    Returns:
        AIGenerator: An instance of the appropriate AIGenerator subclass.
    """
    if generator_type == ModelProvider.GEMINI:
        return GeminiGenerator(api_key=api_key, model=model)
    elif (
        generator_type == ModelProvider.DEEPSEEK
        or generator_type == ModelProvider.OPENAI
    ):
        return OpenAIGenerator(
            base_url=base_url, model=model, api_key=api_key
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

    json_text = ""
    if matches:
        json_text = matches[0].strip()
    else:
        json_text = text.strip()

    try:
        obj = json.loads(json_text)
        return {
            "title": obj.get("title", ""),
            "content": obj.get("content", ""),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse json: {e}, Text: {text}")
        raise ValueError(f"Failed to parse json {json_text}. Text: {text}")


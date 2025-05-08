import json
import re
from abc import ABC, abstractmethod

from app.models.feed import FeedArticle
from google import genai
from google.genai import types

import os


class AIGenerator(ABC):
    def __init__(self, prompt: str, limit: int = 5):
        self.prompt = prompt
        self.limit = limit

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
    def __init__(self, prompt: str):
        super().__init__(prompt)

    def sum_up(self, articles: list[FeedArticle]) -> dict[str, str]:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Google API key is not set.")
        input_articles = json.dumps(
            list(
                map(
                    lambda x: {
                        "title": x.title,
                        "content": x.content if x.content else x.summary,
                    },
                    articles[: self.limit],
                )
            )
        )
        client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(api_version="v1alpha")
        )
        inputs = f"{self.prompt}\n ----Input Articles---- \n{input_articles}"
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=inputs)
        return _extract_json(resp.text)


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

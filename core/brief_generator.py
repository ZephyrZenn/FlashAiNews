import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

from google import genai
from google.genai import types
from openai import AsyncOpenAI

from core.config.loader import get_api_key_for_provider, get_config, get_api_key_env_var
from core.models.feed import FeedArticle
from core.models.generator import ModelProvider

logger = logging.getLogger(__name__)

"""Brief generator for summarizing articles using AI models.
This module provides an abstract base class for AI generators and concrete implementations"""


class APIKeyNotConfiguredError(Exception):
    """Raised when API key is not configured for the current provider."""
    
    def __init__(self, provider: ModelProvider):
        self.provider = provider
        self.env_var = get_api_key_env_var(provider)
        super().__init__(
            f"API key not configured. Please set {self.env_var} environment variable for provider '{provider.value}'"
        )


class AIGenerator(ABC):
    def __init__(self, api_key: str, base_url: Optional[str], model: str):
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
    async def completion(self, prompt, **kwargs) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def completion_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> dict:
        """支持 function calling 的 completion 方法
        
        Args:
            messages: 消息列表，格式为 [{"role": "user|assistant|system|tool", "content": "..."}, ...]
            tools: 工具定义列表，格式为 OpenAI function calling 格式
            tool_choice: 工具选择策略，"auto" | "none" | {"type": "function", "function": {"name": "..."}}
            **kwargs: 其他参数
        
        Returns:
            dict with keys:
                - 'content': str | None - LLM 的文本响应
                - 'tool_calls': list[dict] - 工具调用列表（如果有），格式为:
                    [{"id": "...", "function": {"name": "...", "arguments": "..."}}, ...]
                - 'finish_reason': str - 完成原因
        """
        raise NotImplementedError()


class GeminiGenerator(AIGenerator):
    def __init__(self, api_key: str, model: str):
        super().__init__(api_key=api_key, base_url=None, model=model)
        # 创建客户端实例，避免每次调用都创建
        self.client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(api_version="v1alpha"),
        )

    async def completion(self, prompt, **kwargs) -> str:
        try:
            resp = await self.client.aio.models.generate_content(
                model=self.model, contents=prompt
            )
            return resp.text
        except Exception as e:
            logger.error(f"Error in GeminiGenerator: {e}", exc_info=True)
            raise e

    async def completion_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> dict:
        """支持 function calling 的 completion 方法（Gemini 格式）"""
        try:
            # 转换 messages 格式为 Gemini 格式
            gemini_contents = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    # Gemini 使用 system_instruction 处理 system 消息
                    # 这里我们将其作为第一个 user 消息的一部分
                    if gemini_contents:
                        existing_text = ""
                        if gemini_contents[0].get("parts"):
                            existing_text = gemini_contents[0]["parts"][0].get("text", "")
                        gemini_contents[0] = {
                            "role": "user",
                            "parts": [{"text": f"System: {content}\n\n{existing_text}"}]
                        }
                    else:
                        gemini_contents.append({"role": "user", "parts": [{"text": f"System: {content}"}]})
                elif role == "user":
                    gemini_contents.append({"role": "user", "parts": [{"text": content}]})
                elif role == "assistant":
                    gemini_contents.append({"role": "model", "parts": [{"text": content}]})
                elif role == "tool":
                    # Gemini 使用 function_response 格式
                    tool_name = msg.get("name", "")
                    tool_content = msg.get("content", "")
                    gemini_contents.append({
                        "role": "function",
                        "parts": [{
                            "function_response": {
                                "name": tool_name,
                                "response": tool_content
                            }
                        }]
                    })

            # 转换 tools 格式为 Gemini 格式
            gemini_tools = None
            if tools:
                gemini_tools = []
                for tool in tools:
                    if tool.get("type") == "function":
                        func_def = tool.get("function", {})
                        gemini_tools.append({
                            "function_declarations": [{
                                "name": func_def.get("name", ""),
                                "description": func_def.get("description", ""),
                                "parameters": func_def.get("parameters", {})
                            }]
                        })

            # 构建请求
            request_params = {
                "model": self.model,
                "contents": gemini_contents,
            }

            if gemini_tools:
                request_params["tools"] = gemini_tools

            # 添加其他 kwargs
            request_params.update(kwargs)

            resp = await self.client.aio.models.generate_content(**request_params)

            # 解析响应
            content = resp.text if hasattr(resp, 'text') and resp.text else None
            tool_calls = []

            # 检查是否有 function_calls
            if hasattr(resp, 'candidates') and resp.candidates:
                candidate = resp.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'function_call'):
                                fc = part.function_call
                                tool_calls.append({
                                    "id": f"call_{len(tool_calls)}",  # Gemini 不提供 ID，我们生成一个
                                    "function": {
                                        "name": fc.name if hasattr(fc, 'name') else "",
                                        "arguments": json.dumps(fc.args) if hasattr(fc, 'args') else "{}"
                                    }
                                })

            return {
                "content": content,
                "tool_calls": tool_calls if tool_calls else None,
                "finish_reason": getattr(resp.candidates[0], 'finish_reason', None) if hasattr(resp, 'candidates') and resp.candidates else None,
            }
        except Exception as e:
            logger.error(f"Error in GeminiGenerator.completion_with_tools: {e}", exc_info=True)
            raise e


class OpenAIGenerator(AIGenerator):
    def __init__(self, base_url, model, api_key):
        super().__init__(base_url=base_url, model=model, api_key=api_key)
        # 创建异步客户端实例，避免每次调用都创建
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def completion(self, prompt, **kwargs) -> str:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in OpenAIGenerator: {e}", exc_info=True)
            raise e

    async def completion_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
        **kwargs
    ) -> dict:
        """支持 function calling 的 completion 方法"""
        try:
            # 转换 tool_choice 格式
            tool_choice_param = None
            if tool_choice == "none":
                tool_choice_param = "none"
            elif tool_choice == "auto":
                tool_choice_param = "auto"
            elif isinstance(tool_choice, dict):
                tool_choice_param = tool_choice

            # 准备请求参数
            request_params = {
                "model": self.model,
                "messages": messages,
                "stream": False,
            }

            # 如果有工具，添加 tools 和 tool_choice 参数
            if tools:
                request_params["tools"] = tools
                if tool_choice_param is not None:
                    request_params["tool_choice"] = tool_choice_param

            # 添加其他 kwargs
            request_params.update(kwargs)

            resp = await self.client.chat.completions.create(**request_params)

            message = resp.choices[0].message

            # 提取工具调用
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    })

            return {
                "content": message.content,
                "tool_calls": tool_calls if tool_calls else None,
                "finish_reason": resp.choices[0].finish_reason,
            }
        except Exception as e:
            logger.error(f"Error in OpenAIGenerator.completion_with_tools: {e}", exc_info=True)
            raise e


def build_generator() -> AIGenerator:
    """Build an AI generator based on current configuration.
    
    Raises:
        APIKeyNotConfiguredError: If the API key is not set for the current provider.
    """
    config = get_config()
    model_cfg = config.model
    
    # Get API key from environment variable based on provider
    api_key = get_api_key_for_provider(model_cfg.provider)
    
    if not api_key:
        raise APIKeyNotConfiguredError(model_cfg.provider)
    
    return _build_generator(
        generator_type=model_cfg.provider,
        api_key=api_key,
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
        generator_type (ModelProvider): The type of generator to create
        api_key (str): The API key for the AI service.
        base_url (str): The base URL for the AI service.
        model (str): The model to use for summarization.
    Returns:
        AIGenerator: An instance of the appropriate AIGenerator subclass.
    """
    if generator_type == ModelProvider.GEMINI:
        return GeminiGenerator(api_key=api_key, model=model)
    elif generator_type in (ModelProvider.OPENAI, ModelProvider.DEEPSEEK, ModelProvider.OTHER):
        # All OpenAI-compatible providers use OpenAIGenerator
        return OpenAIGenerator(base_url=base_url, model=model, api_key=api_key)
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
        logger.error(f"Failed to parse json: {e}, Text: {text}", exc_info=True)
        raise ValueError(f"Failed to parse json {json_text}. Text: {text}")

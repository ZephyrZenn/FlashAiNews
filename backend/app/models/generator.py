from enum import Enum


class ModelProvider(Enum):
    """Enum for model providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

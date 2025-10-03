from enum import Enum


class ModelProvider(Enum):
    """Enum for model providers."""

    GEMINI = "gemini"
    OPENAI = "openai"


def enum_factory(items):
    return {k: (v.value if isinstance(v, Enum) else v) for k, v in items}

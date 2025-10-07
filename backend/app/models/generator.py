from datetime import time
from enum import Enum


class ModelProvider(Enum):
    """Enum for model providers."""

    GEMINI = "gemini"
    OPENAI = "openai"


def enum_factory(items):
    result = {}
    for key, value in items:
        if isinstance(value, Enum):
            result[key] = value.value
        elif isinstance(value, time):
            result[key] = value.strftime("%H:%M")
        else:
            result[key] = value
    return result

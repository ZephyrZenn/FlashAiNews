from enum import Enum

class GeneratorType(Enum):
    """Enum for generator types."""
    GEMINI = "gemini"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
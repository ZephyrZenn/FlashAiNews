from dataclasses import dataclass

from app.models.config import ModelConfig

@dataclass
class Setting:
    model: ModelConfig
    prompt: str

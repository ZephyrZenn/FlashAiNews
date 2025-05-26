from dataclasses import dataclass

from app.models.generator import ModelProvider


@dataclass
class ModelConfig:
    name: str
    model: str
    provider: ModelProvider
    api_key: str
    base_url: str

@dataclass
class Setting:
    model: ModelConfig
    prompt: str

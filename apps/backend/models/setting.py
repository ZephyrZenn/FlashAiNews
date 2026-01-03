from dataclasses import dataclass

from core.models.config import ModelConfig

@dataclass
class Setting:
    model: ModelConfig

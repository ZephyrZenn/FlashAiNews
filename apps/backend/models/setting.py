from dataclasses import dataclass
from datetime import time

from core.models.config import ModelConfig

@dataclass
class Setting:
    model: ModelConfig
    prompt: str
    brief_time: time

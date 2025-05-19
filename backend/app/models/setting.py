from typing import Optional
from .generator import GeneratorType
from dataclasses import dataclass

@dataclass
class ModelSetting:
    name: str
    model: str
    provider: GeneratorType
    api_key: str
    base_url: Optional[str] = None

@dataclass
class Setting:
    model: ModelSetting
    prompt: str
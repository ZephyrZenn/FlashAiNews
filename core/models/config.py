from dataclasses import dataclass
from typing import Optional

from core.models.generator import ModelProvider


@dataclass
class GlobalConfig:
    """Global configuration dataclass"""

    model: "ModelConfig"


@dataclass
class ModelConfig:
    """Model configuration dataclass"""

    model: str
    provider: ModelProvider
    base_url: Optional[str] = None  # Only required for OTHER provider

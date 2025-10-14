import re
from dataclasses import dataclass
from datetime import time
from typing import Optional

from pydantic import BaseModel, Field, validator

from core.models.generator import ModelProvider


class ModelConfigModel(BaseModel):
    """Pydantic model for model configuration validation"""

    model: str = Field(..., description="Model name")
    provider: str = Field(..., description="Model provider (openai, deepseek, gemini)")
    api_key: str = Field(..., description="API key for the model provider")
    base_url: Optional[str] = Field(None, description="Base URL for the model provider")

    @validator("model", "provider", "api_key")
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @validator("provider")
    def validate_provider(cls, v):
        try:
            ModelProvider(v)
        except ValueError as e:
            raise ValueError(f"Invalid provider: {e}")
        return v


class GlobalConfigModel(BaseModel):
    """Pydantic model for global configuration validation"""

    model: ModelConfigModel = Field(..., description="Default model configuration")
    prompt: str = Field(..., description="Default prompt template")
    brief_time: time = Field(
        default_factory=lambda: time(hour=8),
        description="Daily brief generation time in HH:MM 24h format",
    )

    @validator("prompt")
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        return v.strip()

    @validator("brief_time")
    def validate_brief_time(cls, v):
        if isinstance(v, str):
            match = re.fullmatch(r"(\d{1,2}):(\d{2})", v.strip())
            if not match:
                raise ValueError("brief_time must be in HH:MM format")
            hour, minute = int(match.group(1)), int(match.group(2))
            if hour not in range(24) or minute not in range(60):
                raise ValueError("brief_time must represent a valid 24-hour time")
            return time(hour=hour, minute=minute)
        if isinstance(v, time):
            if v.second != 0 or v.microsecond != 0:
                return v.replace(second=0, microsecond=0)
            return v
        raise ValueError("brief_time must be a time or string value")


@dataclass
class GlobalConfig:
    """Global configuration dataclass"""

    model: "ModelConfig"
    prompt: str
    brief_time: time


@dataclass
class ModelConfig:
    """Model configuration dataclass"""

    model: str
    provider: ModelProvider
    api_key: str
    base_url: Optional[str] = None

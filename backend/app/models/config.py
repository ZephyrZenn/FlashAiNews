from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field, validator

from app.models.generator import ModelProvider


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

    @validator("prompt")
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        return v.strip()


@dataclass
class GlobalConfig:
    """Global configuration dataclass"""

    model: "ModelConfig"
    prompt: str


@dataclass
class ModelConfig:
    """Model configuration dataclass"""

    model: str
    provider: ModelProvider
    api_key: str
    base_url: Optional[str] = None
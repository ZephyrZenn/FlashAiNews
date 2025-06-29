from dataclasses import dataclass
from typing import Dict, Optional

from pydantic import BaseModel, Field, validator

from app.models.generator import ModelProvider


class GlobalConfigModel(BaseModel):
    """Pydantic model for global configuration validation"""

    email_enabled: bool = Field(
        ..., description="Whether email notifications are enabled"
    )
    default_model: str = Field(..., description="Default model name to use")
    prompt: str = Field(..., description="Default prompt template")

    @validator("default_model")
    def validate_default_model(cls, v):
        if not v or not v.strip():
            raise ValueError("default_model cannot be empty")
        return v.strip()

    @validator("prompt")
    def validate_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError("prompt cannot be empty")
        return v.strip()


class EmailConfigModel(BaseModel):
    """Pydantic model for email configuration validation"""

    sender: str = Field(..., description="Email sender address")
    receiver: str = Field(..., description="Email receiver address")
    api_key: str = Field(..., description="Email service API key")

    @validator("sender", "receiver")
    def validate_email_format(cls, v):
        if not v or not v.strip():
            raise ValueError("Email address cannot be empty")
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.strip()

    @validator("api_key")
    def validate_api_key(cls, v):
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        return v.strip()


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


@dataclass
class GlobalConfig:
    """Global configuration dataclass"""

    email_enabled: bool
    default_model: str
    prompt: str


@dataclass
class EmailConfig:
    """Email configuration dataclass"""

    sender: str
    receiver: str
    api_key: str


@dataclass
class ModelConfig:
    """Model configuration dataclass"""

    model: str
    provider: ModelProvider
    api_key: str
    base_url: Optional[str] = None


@dataclass
class AppConfig:
    """Application configuration dataclass"""

    global_: GlobalConfig
    email: Optional[EmailConfig]
    models: Dict[str, ModelConfig]

    def get_default_model_config(self) -> ModelConfig:
        """Get the default model configuration"""
        return self.models[self.global_.default_model]

    def is_email_enabled(self) -> bool:
        """Check if email is enabled and configured"""
        return self.global_.email_enabled and self.email is not None

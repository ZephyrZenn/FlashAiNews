from dataclasses import dataclass
from typing import Optional

from app.models.generator import ModelProvider


@dataclass
class GlobalConfig:
    email_enabled: bool
    default_model: str
    prompt: str


@dataclass
class EmailConfig:
    sender: str
    password: str
    receiver: str
    smtp_server: str


@dataclass
class ModelConfig:
    model: str
    provider: ModelProvider
    api_key: str
    base_url: Optional[str] = None


@dataclass
class AppConfig:
    global_: GlobalConfig
    email: EmailConfig
    models: dict[str, ModelConfig]

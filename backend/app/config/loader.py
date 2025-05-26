import logging
from typing import Optional

import toml

from app.models.config import AppConfig, EmailConfig, GlobalConfig, ModelConfig
from app.models.generator import ModelProvider

logger = logging.getLogger(__name__)

_config: Optional[AppConfig] = None


def _validate_llm_config(config: dict):
    if "api_key" not in config:
        raise ValueError("api_key is required")
    if "model" not in config:
        raise ValueError("model is required")
    if "provider" not in config:
        raise ValueError("provider is required")


def load_config() -> AppConfig:
    global _config
    if _config:
        return _config

    with open("config.toml", "r") as f:
        cfg_dict = toml.load(f)

    if "global" not in cfg_dict:
        raise ValueError("global section is required")
    if "models" not in cfg_dict:
        raise ValueError("models section is required")

    global_cfg = GlobalConfig(**cfg_dict["global"])
    if global_cfg.email_enabled and "email" not in cfg_dict:
        raise ValueError("email section is required when email is enabled")

    email_cfg = EmailConfig(**cfg_dict["email"]) if "email" in cfg_dict else None
    logger.info(f"Model Config: {cfg_dict['models']}")
    for name, cfg in cfg_dict["models"].items():
        _validate_llm_config(cfg)
    model_cfgs = {
        name: ModelConfig(
            model=cfg["model"],
            provider=ModelProvider(cfg["provider"]),
            api_key=cfg["api_key"],
            base_url=cfg["base_url"],
        )
        for name, cfg in cfg_dict["models"].items()
    }

    _config = AppConfig(global_cfg, email_cfg, model_cfgs)
    return _config

def get_config() -> AppConfig:
    return load_config()
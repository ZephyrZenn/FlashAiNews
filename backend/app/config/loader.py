import logging
import os
from dataclasses import dataclass
from typing import Optional

import toml

from app.models.config import (
    GlobalConfig,
    GlobalConfigModel,
    ModelConfig,
    ModelConfigModel,
)
from app.models.generator import ModelProvider

from .utils import (
    create_default_config,
    get_config_summary,
    validate_config_file_exists,
)

logger = logging.getLogger(__name__)

_config: Optional[GlobalConfig] = None


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""

    pass


@dataclass
class ConfigPaths:
    """Configuration file paths for different environments"""

    dev: str = "config.toml"
    prod: str = "/app/config.toml"
    test: str = "config.toml"


def get_config_path() -> str:
    """Get the appropriate config file path based on environment"""
    env = os.getenv("ENV", "dev").lower()
    paths = ConfigPaths()

    if env == "prod":
        return paths.prod
    elif env == "test":
        return paths.test
    else:
        return paths.dev


def _validate_global_config(config: dict) -> GlobalConfigModel:
    """Validate global configuration using Pydantic"""
    try:
        return GlobalConfigModel(**config)
    except Exception as e:
        raise ConfigValidationError(f"Global configuration validation failed: {e}")


def _to_model_config(config: ModelConfigModel) -> ModelConfig:
    """Convert pydantic model configuration to dataclass representation"""
    return ModelConfig(
        model=config.model,
        provider=ModelProvider(config.provider),
        api_key=config.api_key,
        base_url=config.base_url,
    )


def load_config(reload: bool = False, use_env_overrides: bool = True) -> GlobalConfig:
    """Load configuration with caching, validation, and environment overrides"""
    global _config

    if _config and not reload:
        return _config

    config_path = get_config_path()

    if not os.path.exists(config_path):
        try:
            default_config = create_default_config()
            directory = os.path.dirname(config_path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                toml.dump(default_config, f)
            logger.info("Created default configuration at %s", config_path)
        except Exception as e:
            raise ConfigValidationError(
                f"Failed to create default configuration at {config_path}: {e}"
            )

    if not validate_config_file_exists(config_path):
        raise ConfigValidationError(f"Configuration file not found: {config_path}")

    try:
        # Load file configuration
        with open(config_path, "r", encoding="utf-8") as f:
            file_config = toml.load(f)

        summary = get_config_summary(file_config)
        logger.info(f"Configuration summary: {summary}")

    except toml.TomlDecodeError as e:
        raise ConfigValidationError(f"Invalid TOML configuration: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Error reading configuration file: {e}")

    # Validate and build global config
    global_model = _validate_global_config(file_config)
    global_cfg = GlobalConfig(
        model=_to_model_config(global_model.model),
        prompt=global_model.prompt,
        brief_time=global_model.brief_time,
    )

    _config = global_cfg
    logger.info(
        "Configuration loaded successfully. Model: %s (%s)",
        global_cfg.model.model,
        global_cfg.model.provider.value,
    )

    return _config


def get_config() -> GlobalConfig:
    """Get the current configuration, loading it if necessary"""
    return load_config()


def reload_config() -> GlobalConfig:
    """Force reload the configuration"""
    return load_config(reload=True)


def get_model_config(model_name: Optional[str] = None) -> ModelConfig:
    """Get the configured model. Additional models are not supported."""
    config = get_config()
    default_model_name = config.model.model
    if model_name and model_name not in {"default", default_model_name}:
        raise ConfigValidationError(
            f"Model '{model_name}' not found. Only the default model is configured."
        )

    return config.model


def validate_config() -> bool:
    """Validate the current configuration without loading it"""
    try:
        load_config(reload=True)
        return True
    except ConfigValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during configuration validation: {e}")
        return False

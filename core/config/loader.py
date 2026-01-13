import logging
import os
from dataclasses import dataclass
from typing import Optional

import toml

from core.models.config import GlobalConfig, ModelConfig
from core.models.generator import ModelProvider

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


def _validate_model_config(config: dict) -> None:
    """Validate model configuration required fields."""
    required = ["model", "provider", "api_key"]
    for field in required:
        value = config.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            raise ConfigValidationError(f"Missing required field: model.{field}")
    
    provider = config["provider"]
    valid_providers = [p.value for p in ModelProvider]
    if provider not in valid_providers:
        raise ConfigValidationError(
            f"Invalid provider: {provider}. Must be one of: {valid_providers}"
        )


def _to_model_config(config: dict) -> ModelConfig:
    """Convert dict configuration to ModelConfig dataclass."""
    return ModelConfig(
        model=config["model"].strip(),
        provider=ModelProvider(config["provider"]),
        api_key=config["api_key"].strip(),
        base_url=config.get("base_url"),
    )


def load_config(reload: bool = False, use_env_overrides: bool = True, path: Optional[str] = None) -> GlobalConfig:
    """Load configuration with caching, validation, and environment overrides"""
    global _config

    if _config and not reload:
        return _config

    if not path:
        config_path = get_config_path()
    else:
        config_path = path

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

        # Apply environment variable overrides if enabled
        if use_env_overrides:
            file_config = _apply_env_overrides(file_config)

        summary = get_config_summary(file_config)
        logger.info(f"Configuration summary: {summary}")

    except toml.TomlDecodeError as e:
        raise ConfigValidationError(f"Invalid TOML configuration: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Error reading configuration file: {e}")

    # Validate and build global config
    model_config = file_config.get("model", {})
    _validate_model_config(model_config)
    
    global_cfg = GlobalConfig(
        model=_to_model_config(model_config),
    )

    _config = global_cfg
    logger.info(
        "Configuration loaded successfully. Model: %s (%s)",
        global_cfg.model.model,
        global_cfg.model.provider.value,
    )

    return _config


def _apply_env_overrides(config: dict) -> dict:
    """Apply environment variable overrides to configuration"""
    # Override model configuration from environment variables
    if "model" not in config:
        config["model"] = {}

    # Override API key from environment
    if api_key := os.getenv("MODEL_API_KEY"):
        config["model"]["api_key"] = api_key
        logger.debug("Overriding api_key from MODEL_API_KEY environment variable")

    # Override base URL from environment
    if base_url := os.getenv("MODEL_BASE_URL"):
        config["model"]["base_url"] = base_url
        logger.debug("Overriding base_url from MODEL_BASE_URL environment variable")

    # Override model name from environment
    if model_name := os.getenv("MODEL_NAME"):
        config["model"]["model"] = model_name
        logger.debug("Overriding model from MODEL_NAME environment variable")

    # Override provider from environment
    if provider := os.getenv("MODEL_PROVIDER"):
        config["model"]["provider"] = provider
        logger.debug("Overriding provider from MODEL_PROVIDER environment variable")


    return config


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

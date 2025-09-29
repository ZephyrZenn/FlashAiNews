import logging
import os
from dataclasses import dataclass
from typing import Optional

import toml

from app.models.config import (
    AppConfig,
    EmailConfig,
    EmailConfigModel,
    GlobalConfig,
    GlobalConfigModel,
    ModelConfig,
    ModelConfigModel,
)
from app.models.generator import ModelProvider

from .utils import (
    get_config_summary,
    get_environment_config,
    merge_configs,
    validate_config_file_exists,
    validate_model_configs,
)

logger = logging.getLogger(__name__)

_config: Optional[AppConfig] = None


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


def _validate_llm_config(config: dict, model_name: str) -> None:
    """Validate LLM configuration with detailed error messages"""
    try:
        # Use Pydantic model for validation
        ModelConfigModel(**config)
    except Exception as e:
        raise ConfigValidationError(f"Model '{model_name}' validation failed: {e}")


def _validate_global_config(config: dict) -> None:
    """Validate global configuration using Pydantic"""
    try:
        GlobalConfigModel(**config)
    except Exception as e:
        raise ConfigValidationError(f"Global configuration validation failed: {e}")


def _validate_email_config(config: dict) -> None:
    """Validate email configuration using Pydantic"""
    try:
        EmailConfigModel(**config)
    except Exception as e:
        raise ConfigValidationError(f"Email configuration validation failed: {e}")


def load_config(reload: bool = False, use_env_overrides: bool = True) -> AppConfig:
    """Load configuration with caching, validation, and environment overrides"""
    global _config

    if _config and not reload:
        return _config

    config_path = get_config_path()

    # Validate config file exists
    if not validate_config_file_exists(config_path):
        raise ConfigValidationError(f"Configuration file not found: {config_path}")

    try:
        # Load file configuration
        with open(config_path, "r", encoding="utf-8") as f:
            file_config = toml.load(f)

        # Apply environment overrides if enabled
        if use_env_overrides:
            env_config = get_environment_config()
            if env_config:
                file_config = merge_configs(file_config, env_config)
                logger.info("Applied environment configuration overrides")

        # Log configuration summary (without sensitive data)
        summary = get_config_summary(file_config)
        logger.info(f"Configuration summary: {summary}")

    except toml.TomlDecodeError as e:
        raise ConfigValidationError(f"Invalid TOML configuration: {e}")
    except Exception as e:
        raise ConfigValidationError(f"Error reading configuration file: {e}")

    # Validate required sections
    if "global" not in file_config:
        raise ConfigValidationError("'global' section is required in configuration")
    if "models" not in file_config:
        raise ConfigValidationError("'models' section is required in configuration")

    # Validate global config
    _validate_global_config(file_config["global"])

    # Create global config
    global_cfg = GlobalConfig(**file_config["global"])

    # Validate email config if enabled
    email_cfg = None
    if global_cfg.email_enabled:
        if "email" not in file_config:
            raise ConfigValidationError(
                "'email' section is required when email_enabled is true"
            )
        _validate_email_config(file_config["email"])
        email_cfg = EmailConfig(**file_config["email"])

    # Validate model configurations
    model_errors = validate_model_configs(file_config["models"])
    if model_errors:
        raise ConfigValidationError(
            f"Model configuration errors: {'; '.join(model_errors)}"
        )

    # Create model configs
    logger.info(f"Loading {len(file_config['models'])} model configurations")

    model_cfgs = {}
    for name, cfg in file_config["models"].items():
        try:
            _validate_llm_config(cfg, name)
            model_cfgs[name] = ModelConfig(
                model=cfg["model"],
                provider=ModelProvider(cfg["provider"]),
                api_key=cfg["api_key"],
                base_url=cfg.get("base_url"),
            )
        except Exception as e:
            raise ConfigValidationError(f"Error configuring model '{name}': {e}")

    # Validate default model exists
    if global_cfg.default_model not in model_cfgs:
        available_models = list(model_cfgs.keys())
        raise ConfigValidationError(
            f"Default model '{global_cfg.default_model}' not found. Available models: {available_models}"
        )

    _config = AppConfig(global_cfg, email_cfg, model_cfgs)
    logger.info(
        f"Configuration loaded successfully. Default model: {global_cfg.default_model}"
    )

    return _config


def get_config() -> AppConfig:
    """Get the current configuration, loading it if necessary"""
    return load_config()


def reload_config() -> AppConfig:
    """Force reload the configuration"""
    return load_config(reload=True)


def get_model_config(model_name: Optional[str] = None) -> ModelConfig:
    """Get a specific model configuration"""
    config = get_config()
    model_name = model_name or config.global_.default_model

    if model_name not in config.models:
        available_models = list(config.models.keys())
        raise ConfigValidationError(
            f"Model '{model_name}' not found. Available models: {available_models}"
        )

    return config.models[model_name]


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

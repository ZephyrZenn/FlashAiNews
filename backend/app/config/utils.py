"""
Configuration utilities for NewsCollector.

This module provides utility functions for common configuration operations,
including validation, transformation, and helper methods.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def validate_config_file_exists(config_path: str) -> bool:
    """Validate that the configuration file exists"""
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return False
    return True


def get_environment_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    config = {}

    # Global settings
    if os.getenv("EMAIL_ENABLED"):
        config["email_enabled"] = os.getenv("EMAIL_ENABLED").lower() == "true"

    if os.getenv("DEFAULT_MODEL"):
        config["default_model"] = os.getenv("DEFAULT_MODEL")

    if os.getenv("DEFAULT_PROMPT"):
        config["prompt"] = os.getenv("DEFAULT_PROMPT")

    # Email settings
    email_config = {}
    if os.getenv("EMAIL_SENDER"):
        email_config["sender"] = os.getenv("EMAIL_SENDER")
    if os.getenv("EMAIL_RECEIVER"):
        email_config["receiver"] = os.getenv("EMAIL_RECEIVER")
    if os.getenv("EMAIL_API_KEY"):
        email_config["api_key"] = os.getenv("EMAIL_API_KEY")

    if email_config:
        config["email"] = email_config

    return config


def merge_configs(
    file_config: Dict[str, Any], env_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge file configuration with environment configuration (env takes precedence)"""
    merged = file_config.copy()

    # Merge global settings
    if "global" in env_config:
        if "global" not in merged:
            merged["global"] = {}
        merged["global"].update(env_config["global"])

    # Merge email settings
    if "email" in env_config:
        if "email" not in merged:
            merged["email"] = {}
        merged["email"].update(env_config["email"])

    return merged


def validate_model_configs(models: Dict[str, Any]) -> List[str]:
    """Validate model configurations and return list of errors"""
    errors = []

    if not models:
        errors.append("No models configured")
        return errors

    for model_name, config in models.items():
        if not isinstance(config, dict):
            errors.append(f"Model '{model_name}' configuration must be a dictionary")
            continue

        required_fields = ["model", "provider", "api_key"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Model '{model_name}' missing required field: {field}")

        # Validate provider
        if "provider" in config:
            try:
                from app.models.generator import ModelProvider

                ModelProvider(config["provider"])
            except ValueError as e:
                errors.append(f"Model '{model_name}' has invalid provider: {e}")

    return errors


def get_config_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get a summary of the configuration (without sensitive data)"""
    summary = {
        "has_global": "global" in config,
        "has_models": "models" in config,
        "model_count": len(config.get("models", {})),
        "email_enabled": config.get("global", {}).get("email_enabled", False),
        "has_email_config": "email" in config,
    }

    if "global" in config:
        summary["default_model"] = config["global"].get("default_model")

    if "models" in config:
        summary["available_models"] = list(config["models"].keys())

    return summary


def create_default_config() -> Dict[str, Any]:
    """Create a default configuration template"""
    return {
        "global": {
            "email_enabled": False,
            "default_model": "default",
            "prompt": "Summarize the following articles:",
        },
        "email": {
            "sender": "your-email@example.com",
            "receiver": "recipient@example.com",
            "api_key": "your-api-key",
        },
        "models": {
            "default": {
                "model": "gpt-3.5-turbo",
                "provider": "openai",
                "api_key": "your-openai-api-key",
                "base_url": "https://api.openai.com/v1",
            }
        },
    }


def backup_config(config_path: str, backup_dir: str = "backups") -> Optional[str]:
    """Create a backup of the configuration file"""
    try:
        import shutil
        from datetime import datetime

        # Create backup directory if it doesn't exist
        Path(backup_dir).mkdir(exist_ok=True)

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"config_backup_{timestamp}.toml"
        backup_path = os.path.join(backup_dir, backup_filename)

        # Copy the file
        shutil.copy2(config_path, backup_path)

        logger.info(f"Configuration backed up to: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Failed to backup configuration: {e}")
        return None


def restore_config(backup_path: str, config_path: str) -> bool:
    """Restore configuration from backup"""
    try:
        import shutil

        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False

        # Create backup of current config before restoring
        current_backup = backup_config(config_path)

        # Restore from backup
        shutil.copy2(backup_path, config_path)

        logger.info(f"Configuration restored from: {backup_path}")
        if current_backup:
            logger.info(f"Previous configuration backed up to: {current_backup}")

        return True

    except Exception as e:
        logger.error(f"Failed to restore configuration: {e}")
        return False

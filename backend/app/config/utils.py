"""
Configuration utilities for NewsCollector.

This module provides utility functions for common configuration operations,
including validation, transformation, and helper methods.
"""

import logging
import os
from dataclasses import asdict
from typing import Any, Dict

import toml

from app.models.config import GlobalConfig

from app.models.generator import enum_factory

logger = logging.getLogger(__name__)


def validate_config_file_exists(config_path: str) -> bool:
    """Validate that the configuration file exists"""
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        return False
    return True


def get_config_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get a summary of the configuration (without sensitive data)"""
    summary = {
        "has_global": "global" in config,
        "has_model": isinstance(config.get("global", {}).get("model"), dict),
        "has_prompt": "prompt" in config.get("global", {}),
    }

    model_section = config.get("global", {}).get("model")
    if isinstance(model_section, dict):
        summary["model_name"] = model_section.get("model")
        summary["model_provider"] = model_section.get("provider")

    return summary


def create_default_config() -> Dict[str, Any]:
    """Create a default configuration template"""
    return {
        "prompt": (
            "Summarize the following articles and highlight the most relevant insights."
        ),
        "brief_time": "08:00",
        "model": {
            "model": "gpt-4o-mini",
            "provider": "openai",
            "api_key": "replace-with-your-api-key",
        },
    }


def write_config(cfg: GlobalConfig):
    from app.config.loader import get_config_path

    path = get_config_path()
    with open(path, "w", encoding="utf-8") as f:
        toml.dump(asdict(cfg, dict_factory=enum_factory), f)

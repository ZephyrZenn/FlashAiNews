"""
Configuration management module for NewsCollector.

This module provides a unified interface for managing application configuration,
including loading, validation, and access to various configuration components.
"""

from .loader import (
    ConfigValidationError,
    get_config,
    get_config_path,
    get_model_config,
    load_config,
    reload_config,
    validate_config,
)
from .thread import (
    get_thread_pool,
    get_thread_pool_config,
    get_thread_pool_stats,
    init_thread_pool,
    is_thread_pool_initialized,
    shutdown_thread_pool,
)
from .utils import (
    create_default_config,
    get_config_summary,
    validate_config_file_exists,
)

__all__ = [
    # Configuration loading and management
    "get_config",
    "load_config",
    "reload_config",
    "get_model_config",
    "ConfigValidationError",
    "get_config_path",
    "validate_config",
    # Thread pool configuration
    "init_thread_pool",
    "get_thread_pool",
    "shutdown_thread_pool",
    "is_thread_pool_initialized",
    "get_thread_pool_stats",
    "get_thread_pool_config",
    # Configuration utilities
    "validate_config_file_exists",
    "get_config_summary",
    "create_default_config",
]

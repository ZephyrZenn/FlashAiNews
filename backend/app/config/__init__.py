"""
Configuration management module for NewsCollector.

This module provides a unified interface for managing application configuration,
including loading, validation, and access to various configuration components.
"""

from .email import (
    get_email_config_from_env,
    init_email,
    is_email_initialized,
    reset_email_service,
    validate_email_config,
)
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
    backup_config,
    create_default_config,
    get_config_summary,
    get_environment_config,
    merge_configs,
    restore_config,
    validate_config_file_exists,
    validate_model_configs,
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
    # Email configuration
    "init_email",
    "validate_email_config",
    "is_email_initialized",
    "get_email_config_from_env",
    "reset_email_service",
    # Thread pool configuration
    "init_thread_pool",
    "get_thread_pool",
    "shutdown_thread_pool",
    "is_thread_pool_initialized",
    "get_thread_pool_stats",
    "get_thread_pool_config",
    # Configuration utilities
    "validate_config_file_exists",
    "get_environment_config",
    "merge_configs",
    "validate_model_configs",
    "get_config_summary",
    "create_default_config",
    "backup_config",
    "restore_config",
]

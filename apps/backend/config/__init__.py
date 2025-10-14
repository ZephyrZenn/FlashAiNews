"""
Configuration management module for NewsCollector.

This module provides a unified interface for managing application configuration,
including loading, validation, and access to various configuration components.
"""


from .thread import (
    get_thread_pool,
    get_thread_pool_config,
    get_thread_pool_stats,
    init_thread_pool,
    is_thread_pool_initialized,
    shutdown_thread_pool,
)


__all__ = [
    
    # Thread pool configuration
    "init_thread_pool",
    "get_thread_pool",
    "shutdown_thread_pool",
    "is_thread_pool_initialized",
    "get_thread_pool_stats",
    "get_thread_pool_config",

]

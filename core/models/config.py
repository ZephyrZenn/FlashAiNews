from dataclasses import dataclass, field
from typing import Optional

from core.models.llm import ModelProvider


@dataclass
class RateLimitConfig:
    """Rate limiting and retry configuration dataclass"""

    # Rate limiting settings
    requests_per_minute: float = 60.0
    burst_size: int = 10
    enable_rate_limit: bool = True

    # Retry settings
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    enable_retry: bool = True


@dataclass
class ContextConfig:
    """Context management configuration dataclass"""

    # Context window settings
    max_tokens: int = 128000
    compress_threshold: float = 0.8
    compress_strategy: str = "truncate"  # summary, truncate, priority

    # Content optimization settings
    article_max_length: int = 500
    summary_max_length: int = 200
    memory_max_length: int = 300

    # Message compression settings
    history_max_messages: int = 50
    compression_strategy: str = "sliding_window"  # sliding_window, summary, selective
    keep_system: bool = True
    keep_recent_tool_calls: int = 5

    # Tool result limits (to protect context window and logs)
    tool_result_max_chars: int = 5000
    tool_result_max_items: int = 20


@dataclass
class GlobalConfig:
    """Global configuration dataclass"""

    model: "ModelConfig"
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    context: ContextConfig = field(default_factory=ContextConfig)


@dataclass
class ModelConfig:
    """Model configuration dataclass"""

    model: str
    provider: ModelProvider
    base_url: Optional[str] = None  # Only required for OTHER provider


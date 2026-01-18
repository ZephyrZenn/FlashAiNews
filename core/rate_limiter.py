"""Rate limiter and retry utilities for LLM API calls.

Provides token bucket rate limiting and exponential backoff retry mechanism
to avoid hitting API rate limits and handle transient errors gracefully.
"""

import asyncio
import logging
import random
import time
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RateLimiter:
    """Token bucket rate limiter for API requests.
    
    Implements a token bucket algorithm that allows bursting while
    maintaining a long-term average rate limit.
    
    Args:
        requests_per_minute: Maximum number of requests per minute (default: 60)
        burst_size: Maximum burst size (default: 10)
    """
    
    def __init__(
        self,
        requests_per_minute: float = 60,
        burst_size: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
        
        # Calculate refill rate (tokens per second)
        self.refill_rate = requests_per_minute / 60.0
    
    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary.
        
        This method will block until a token is available.
        """
        async with self._lock:
            await self._wait_for_token()
            self.tokens -= 1
    
    async def _wait_for_token(self) -> None:
        """Wait until at least one token is available."""
        while True:
            self._refill_tokens()
            
            if self.tokens >= 1:
                return
            
            # Calculate wait time for next token
            tokens_needed = 1 - self.tokens
            wait_time = tokens_needed / self.refill_rate
            
            # Add small jitter to prevent thundering herd
            wait_time += random.uniform(0, 0.1)
            
            logger.debug(f"Rate limiter waiting {wait_time:.2f}s for token")
            await asyncio.sleep(wait_time)
    
    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_update
        self.last_update = now
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.burst_size,
            self.tokens + elapsed * self.refill_rate
        )


class RetryConfig:
    """Configuration for retry behavior.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Whether to add random jitter (default: True)
        retryable_exceptions: Tuple of exception types that should trigger retry
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (
            Exception,  # Default: retry on any exception
        )


# Common retryable error patterns for LLM APIs
RATE_LIMIT_PATTERNS = [
    "rate limit",
    "rate_limit",
    "too many requests",
    "quota exceeded",
    "resource exhausted",
    "429",
    "503",
    "overloaded",
]


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable based on common patterns.
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is likely transient and retryable
    """
    error_str = str(error).lower()
    
    # Check OpenAI/Gemini specific exception types
    if hasattr(error, "__class__"):
        class_name = error.__class__.__name__
        # OpenAI SDK exceptions
        if "RateLimit" in class_name or "rate_limit" in class_name:
            return True
        if "APIConnectionError" in class_name or "APITimeoutError" in class_name:
            return True
        if "InternalServerError" in class_name or "ServiceUnavailable" in class_name:
            return True
        # Check for common retryable exception base classes
        if "ConnectionError" in class_name or "TimeoutError" in class_name:
            return True
    
    # Check error message for rate limit patterns
    for pattern in RATE_LIMIT_PATTERNS:
        if pattern in error_str:
            return True
    
    # Check for specific HTTP status codes in error
    if hasattr(error, "status_code"):
        if error.status_code in (429, 500, 502, 503, 504):
            return True
    
    # Check for response attribute (common in API libraries)
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        if error.response.status_code in (429, 500, 502, 503, 504):
            return True
    
    # Check OpenAI SDK error code attribute
    if hasattr(error, "code"):
        error_code = str(error.code).lower()
        retryable_codes = [
            "rate_limit_exceeded",
            "server_error",
            "timeout",
            "internal_error",
            "service_unavailable",
        ]
        if any(code in error_code for code in retryable_codes):
            return True
    
    # Check for error body/response content
    if hasattr(error, "body"):
        body_str = str(error.body).lower()
        for pattern in RATE_LIMIT_PATTERNS:
            if pattern in body_str:
                return True
    
    return False


async def retry_with_backoff(
    func: Callable[..., T],
    config: RetryConfig = None,
    *args,
    **kwargs,
) -> T:
    """Execute a function with exponential backoff retry.
    
    Args:
        func: Async function to execute
        config: Retry configuration
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        The result of the function
        
    Raises:
        The last exception if all retries are exhausted
    """
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:  # 捕获所有异常
            last_exception = e
            
            # 检查是否是可重试的错误
            if not is_retryable_error(e):
                logger.warning(f"Non-retryable error: {e}")
                raise
            
            # 如果配置了特定的异常类型，检查异常是否匹配
            if config.retryable_exceptions and config.retryable_exceptions != (Exception,):
                # 如果配置了特定异常类型，检查是否匹配
                if not isinstance(e, config.retryable_exceptions):
                    # 即使 is_retryable_error 返回 True，如果配置了特定类型且不匹配，也不重试
                    logger.warning(
                        f"Error type {type(e).__name__} not in retryable_exceptions, not retrying"
                    )
                    raise
            
            if attempt == config.max_retries:
                logger.error(f"Max retries ({config.max_retries}) exceeded: {e}")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay,
            )
            
            # Add jitter if configured
            if config.jitter:
                delay *= (0.5 + random.random())  # Jitter: 50%-150% of delay
            
            logger.warning(
                f"Retry {attempt + 1}/{config.max_retries} after {delay:.2f}s "
                f"due to: {e}"
            )
            await asyncio.sleep(delay)
    
    # 如果所有重试都失败，抛出最后一个异常
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry loop completed without result or exception")


def with_rate_limit_and_retry(
    rate_limiter: RateLimiter = None,
    retry_config: RetryConfig = None,
):
    """Decorator to add rate limiting and retry to async functions.
    
    Args:
        rate_limiter: RateLimiter instance (optional)
        retry_config: RetryConfig instance (optional)
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Apply rate limiting if configured
            if rate_limiter:
                await rate_limiter.acquire()
            
            # Apply retry if configured
            if retry_config:
                return await retry_with_backoff(func, retry_config, *args, **kwargs)
            
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Default shared instances for common use cases
_default_rate_limiter: RateLimiter | None = None
_default_retry_config: RetryConfig | None = None


def get_default_rate_limiter() -> RateLimiter:
    """Get or create the default rate limiter.
    
    Default: 60 requests per minute with burst size of 10.
    """
    global _default_rate_limiter
    if _default_rate_limiter is None:
        _default_rate_limiter = RateLimiter(
            requests_per_minute=60,
            burst_size=10,
        )
    return _default_rate_limiter


def get_default_retry_config() -> RetryConfig:
    """Get or create the default retry configuration.
    
    Default: 3 retries with exponential backoff starting at 1s.
    """
    global _default_retry_config
    if _default_retry_config is None:
        _default_retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=True,
        )
    return _default_retry_config


def configure_rate_limiter(
    requests_per_minute: float = 60,
    burst_size: int = 10,
) -> RateLimiter:
    """Configure and set the default rate limiter.
    
    Args:
        requests_per_minute: Maximum requests per minute
        burst_size: Maximum burst size
        
    Returns:
        The configured RateLimiter instance
    """
    global _default_rate_limiter
    _default_rate_limiter = RateLimiter(
        requests_per_minute=requests_per_minute,
        burst_size=burst_size,
    )
    return _default_rate_limiter


def configure_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> RetryConfig:
    """Configure and set the default retry configuration.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
        max_delay: Maximum delay between retries
        
    Returns:
        The configured RetryConfig instance
    """
    global _default_retry_config
    _default_retry_config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
    )
    return _default_retry_config

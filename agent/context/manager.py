"""Context manager for tracking and managing token usage.

Provides token counting, context size detection, and compression triggers.
"""

import logging
from typing import Literal

from core.models.llm import Message

logger = logging.getLogger(__name__)


class ContextManager:
    """Manages context window size and token counting.
    
    Provides token estimation, context size tracking, and compression triggers.
    """

    def __init__(
        self,
        max_tokens: int = 128000,
        compress_threshold: float = 0.8,
        compress_strategy: Literal["summary", "truncate", "priority"] = "truncate",
    ):
        """Initialize the context manager.
        
        Args:
            max_tokens: Maximum token count for the context window
            compress_threshold: Threshold (0-1) at which to trigger compression
            compress_strategy: Strategy for compression (summary, truncate, priority)
        """
        self.max_tokens = max_tokens
        self.compress_threshold = compress_threshold
        self.compress_strategy = compress_strategy
        self.current_tokens = 0
        
        # 监控统计
        self.stats = {
            "total_compressions": 0,
            "total_llm_calls": 0,
            "max_tokens_used": 0,
            "avg_tokens_per_call": 0.0,
            "compression_events": [],
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a given text.
        
        Uses a simple character-based estimation (1 token ≈ 4 characters for English/Chinese).
        For more accurate counting, consider using tiktoken or transformers tokenizers.
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        
        # Simple estimation: 1 token ≈ 4 characters for mixed English/Chinese text
        # This is a conservative estimate that works reasonably well for most cases
        char_count = len(text)
        
        # For Chinese characters, use a different ratio (1 token ≈ 1.5 characters)
        # Count Chinese characters (CJK Unified Ideographs)
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = char_count - chinese_chars
        
        # Estimate: English ~4 chars/token, Chinese ~1.5 chars/token
        estimated_tokens = int(english_chars / 4 + chinese_chars / 1.5)
        
        # Add overhead for JSON formatting, special tokens, etc.
        estimated_tokens = int(estimated_tokens * 1.1)
        
        return max(estimated_tokens, 1)  # At least 1 token

    def estimate_messages_tokens(self, messages: list[Message]) -> int:
        """Estimate total token count for a list of messages.
        
        Args:
            messages: List of Message objects
            
        Returns:
            Total estimated token count
        """
        total_tokens = 0
        
        for msg in messages:
            # System message overhead
            if msg.role == "system":
                total_tokens += 10  # System message overhead
            
            # Content tokens
            if msg.content:
                total_tokens += self.estimate_tokens(str(msg.content))
            
            # Tool calls overhead
            if msg.tool_calls:
                total_tokens += 50  # Tool call overhead
                for tool_call in msg.tool_calls:
                    total_tokens += self.estimate_tokens(tool_call.name)
                    total_tokens += self.estimate_tokens(tool_call.arguments)
            
            # Tool response overhead
            if msg.role == "tool":
                total_tokens += 20  # Tool response overhead
                if msg.content:
                    total_tokens += self.estimate_tokens(str(msg.content))
        
        return total_tokens

    def update_tokens(self, messages: list[Message]) -> int:
        """Update current token count based on messages.
        
        Args:
            messages: List of Message objects
            
        Returns:
            Current token count
        """
        self.current_tokens = self.estimate_messages_tokens(messages)
        return self.current_tokens

    def should_compress(self, messages: list[Message] | None = None) -> bool:
        """Check if compression should be triggered.
        
        Args:
            messages: Optional list of messages to check. If None, uses current_tokens.
            
        Returns:
            True if compression should be triggered
        """
        if messages is not None:
            current = self.estimate_messages_tokens(messages)
        else:
            current = self.current_tokens
        
        threshold_tokens = int(self.max_tokens * self.compress_threshold)
        should_compress = current >= threshold_tokens
        
        if should_compress:
            logger.debug(
                f"Context compression triggered: {current}/{self.max_tokens} tokens "
                f"({current/self.max_tokens*100:.1f}%)"
            )
        
        return should_compress

    def get_usage_ratio(self, messages: list[Message] | None = None) -> float:
        """Get current context usage ratio.
        
        Args:
            messages: Optional list of messages to check. If None, uses current_tokens.
            
        Returns:
            Usage ratio (0.0 to 1.0)
        """
        if messages is not None:
            current = self.estimate_messages_tokens(messages)
        else:
            current = self.current_tokens
        
        return min(current / self.max_tokens, 1.0)

    def reset(self) -> None:
        """Reset token counter."""
        self.current_tokens = 0
        logger.debug("Context manager token counter reset")

    def record_compression(self, before_tokens: int, after_tokens: int) -> None:
        """Record a compression event.
        
        Args:
            before_tokens: Token count before compression
            after_tokens: Token count after compression
        """
        self.stats["total_compressions"] += 1
        self.stats["compression_events"].append({
            "before": before_tokens,
            "after": after_tokens,
            "saved": before_tokens - after_tokens,
            "ratio": after_tokens / before_tokens if before_tokens > 0 else 0.0,
        })
        # 只保留最近100次压缩记录
        if len(self.stats["compression_events"]) > 100:
            self.stats["compression_events"] = self.stats["compression_events"][-100:]

    def record_llm_call(self, tokens: int) -> None:
        """Record an LLM call with token usage.
        
        Args:
            tokens: Token count used in this call
        """
        self.stats["total_llm_calls"] += 1
        self.stats["max_tokens_used"] = max(self.stats["max_tokens_used"], tokens)
        
        # 更新平均token数
        total_tokens = (
            self.stats["avg_tokens_per_call"] * (self.stats["total_llm_calls"] - 1) + tokens
        )
        self.stats["avg_tokens_per_call"] = total_tokens / self.stats["total_llm_calls"]

    def get_stats(self) -> dict:
        """Get current statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        usage_ratio = self.get_usage_ratio()
        
        # 计算压缩统计
        compression_stats = {}
        if self.stats["compression_events"]:
            total_saved = sum(e["saved"] for e in self.stats["compression_events"])
            avg_compression_ratio = sum(e["ratio"] for e in self.stats["compression_events"]) / len(
                self.stats["compression_events"]
            )
            compression_stats = {
                "total_compressions": self.stats["total_compressions"],
                "total_tokens_saved": total_saved,
                "avg_compression_ratio": avg_compression_ratio,
            }
        
        return {
            "current_tokens": self.current_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": usage_ratio,
            "remaining_tokens": max(0, self.max_tokens - self.current_tokens),
            "compress_threshold": self.compress_threshold,
            "compress_strategy": self.compress_strategy,
            "llm_calls": {
                "total": self.stats["total_llm_calls"],
                "max_tokens": self.stats["max_tokens_used"],
                "avg_tokens": self.stats["avg_tokens_per_call"],
            },
            "compression": compression_stats,
        }

    def log_stats(self) -> None:
        """Log current statistics."""
        stats = self.get_stats()
        logger.info(
            f"Context Manager Stats: "
            f"Current: {stats['current_tokens']}/{stats['max_tokens']} tokens "
            f"({stats['usage_ratio']*100:.1f}%), "
            f"LLM Calls: {stats['llm_calls']['total']}, "
            f"Compressions: {stats.get('compression', {}).get('total_compressions', 0)}"
        )

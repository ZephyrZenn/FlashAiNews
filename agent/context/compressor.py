"""Message compressor for compressing message history.

Provides message history compression using sliding window, summarization, and selective retention.
"""

import json
import logging
from typing import Literal

from agent.context.manager import ContextManager
from core.models.llm import Message

logger = logging.getLogger(__name__)


class MessageCompressor:
    """Compresses message history to fit within context limits.
    
    Provides various compression strategies: sliding window, summarization, and selective retention.
    """

    def __init__(
        self,
        context_manager: ContextManager,
        strategy: Literal["sliding_window", "summary", "selective"] = "sliding_window",
        max_messages: int = 50,
        keep_system: bool = True,
        keep_recent_tool_calls: int = 5,
    ):
        """Initialize the message compressor.
        
        Args:
            context_manager: ContextManager instance for token counting
            strategy: Compression strategy to use
            max_messages: Maximum number of messages to keep (for sliding_window)
            keep_system: Whether to always keep system messages
            keep_recent_tool_calls: Number of recent tool call results to keep
        """
        self.context_manager = context_manager
        self.strategy = strategy
        self.max_messages = max_messages
        self.keep_system = keep_system
        self.keep_recent_tool_calls = keep_recent_tool_calls

    def compress_messages(
        self, messages: list[Message], target_tokens: int | None = None
    ) -> list[Message]:
        """Compress messages using the configured strategy.
        
        Args:
            messages: List of Message objects to compress
            target_tokens: Target token count (None to use threshold)
            
        Returns:
            Compressed list of messages
        """
        if not messages:
            return messages
        
        # 标记受保护的消息（system和第一条user消息）
        self._mark_protected_messages(messages)
        
        current_tokens = self.context_manager.estimate_messages_tokens(messages)
        
        if target_tokens is None:
            target_tokens = int(
                self.context_manager.max_tokens * self.context_manager.compress_threshold
            )
        
        if current_tokens <= target_tokens:
            logger.debug(f"No compression needed: {current_tokens} <= {target_tokens} tokens")
            return messages
        logger.info(
            f"Compressing messages: {current_tokens} -> {target_tokens} tokens "
            f"(strategy: {self.strategy})"
        )
        
        # 记录压缩前的token数
        before_tokens = current_tokens
        
        compressed = None
        if self.strategy == "sliding_window":
            compressed = self._compress_sliding_window(messages, target_tokens)
        elif self.strategy == "summary":
            compressed = self._compress_summary(messages, target_tokens)
        elif self.strategy == "selective":
            compressed = self._compress_selective(messages, target_tokens)
        else:
            logger.warning(f"Unknown compression strategy: {self.strategy}, using sliding_window")
            compressed = self._compress_sliding_window(messages, target_tokens)
        
        # 记录压缩统计
        after_tokens = self.context_manager.estimate_messages_tokens(compressed)
        self.context_manager.record_compression(before_tokens, after_tokens)
        
        logger.info(
            f"Compression completed: {before_tokens} -> {after_tokens} tokens "
            f"(saved {before_tokens - after_tokens} tokens, "
            f"{((before_tokens - after_tokens) / before_tokens * 100):.1f}% reduction)"
        )
        
        return compressed

    def _mark_protected_messages(self, messages: list[Message]) -> None:
        """标记受保护的消息：system消息和第一条user消息（priority=0）
        
        Args:
            messages: 消息列表（会被修改）
        """
        first_user_found = False
        for msg in messages:
            # 所有system消息设置为最高优先级
            if msg.role == "system":
                msg.set_priority(0)
            # 第一条user消息（在system之后）设置为最高优先级
            elif msg.role == "user" and not first_user_found:
                msg.set_priority(0)
                first_user_found = True

    def _compress_sliding_window(
        self, messages: list[Message], target_tokens: int
    ) -> list[Message]:
        """Compress using sliding window: keep most recent messages.
        
        Args:
            messages: Messages to compress
            target_tokens: Target token count
            
        Returns:
            Compressed messages
        """
        # 分离受保护消息和普通消息
        protected_messages = [msg for msg in messages if msg.is_protected()]
        non_protected = [msg for msg in messages if not msg.is_protected()]

        # Build "atomic" units so tool-call chain stays consistent:
        # never keep tool result without its initiating assistant/tool_calls message.
        units = self._build_atomic_units(non_protected)

        kept_units: list[list[Message]] = []
        base_tokens = self.context_manager.estimate_messages_tokens(protected_messages)
        current_tokens = base_tokens

        # Start from the end and work backwards by unit.
        for unit in reversed(units):
            unit_tokens = self.context_manager.estimate_messages_tokens(unit)
            if current_tokens + unit_tokens <= target_tokens:
                kept_units.insert(0, unit)
                current_tokens += unit_tokens
                continue

            # If unit contains tool results, try truncating tool contents to fit.
            truncated_unit = self._truncate_tool_unit_to_fit(
                unit, max_tokens=target_tokens - current_tokens
            )
            if truncated_unit is not None:
                kept_units.insert(0, truncated_unit)
                current_tokens += self.context_manager.estimate_messages_tokens(truncated_unit)
                continue

            break

        compressed = protected_messages + [m for unit in kept_units for m in unit]

        logger.debug(
            "Sliding window compression: kept %s/%s messages, %s tokens",
            len(compressed),
            len(messages),
            current_tokens,
        )

        return compressed

    def _compress_summary(self, messages: list[Message], target_tokens: int) -> list[Message]:
        """Compress using summarization (placeholder - would use LLM in production).
        
        For now, falls back to sliding window. In production, this would:
        1. Group old messages
        2. Use LLM to generate summary
        3. Replace old messages with summary
        
        Args:
            messages: Messages to compress
            target_tokens: Target token count
            
        Returns:
            Compressed messages
        """
        # For now, use sliding window as a fallback
        # In production, this would use LLM to generate summaries
        logger.debug("Summary compression not yet implemented, using sliding window")
        return self._compress_sliding_window(messages, target_tokens)

    def _compress_selective(
        self, messages: list[Message], target_tokens: int
    ) -> list[Message]:
        """Compress using selective retention: keep important messages.
        
        Args:
            messages: Messages to compress
            target_tokens: Target token count
            
        Returns:
            Compressed messages
        """
        compressed: list[Message] = []

        # 分离受保护消息和普通消息
        protected_messages = [msg for msg in messages if msg.is_protected()]
        non_protected = [msg for msg in messages if not msg.is_protected()]

        # 始终保留受保护消息
        compressed.extend(protected_messages)

        units = self._build_atomic_units(non_protected)

        # Keep most recent N tool-call units (assistant tool_calls + their tool results).
        tool_units = [u for u in units if self._unit_has_tool_chain(u)]
        recent_tool_units = tool_units[-self.keep_recent_tool_calls :]

        current_tokens = self.context_manager.estimate_messages_tokens(compressed)
        for unit in recent_tool_units:
            unit_tokens = self.context_manager.estimate_messages_tokens(unit)
            if current_tokens + unit_tokens <= target_tokens:
                compressed.extend(unit)
                current_tokens += unit_tokens
            else:
                truncated_unit = self._truncate_tool_unit_to_fit(
                    unit, max_tokens=target_tokens - current_tokens
                )
                if truncated_unit is not None:
                    compressed.extend(truncated_unit)
                    current_tokens += self.context_manager.estimate_messages_tokens(
                        truncated_unit
                    )

        # Add other units from the end if space allows (avoid duplicating tool units already kept)
        kept_unit_ids = {id(u) for u in recent_tool_units}
        other_units = [u for u in units if id(u) not in kept_unit_ids]
        for unit in reversed(other_units):
            unit_tokens = self.context_manager.estimate_messages_tokens(unit)
            if current_tokens + unit_tokens <= target_tokens:
                compressed.extend(unit)
                current_tokens += unit_tokens
            else:
                # Only consider truncation for tool units; otherwise stop.
                if self._unit_has_tool_chain(unit):
                    truncated_unit = self._truncate_tool_unit_to_fit(
                        unit, max_tokens=target_tokens - current_tokens
                    )
                    if truncated_unit is not None:
                        compressed.extend(truncated_unit)
                        current_tokens += self.context_manager.estimate_messages_tokens(
                            truncated_unit
                        )
                break

        logger.debug(
            "Selective compression: kept %s/%s messages, %s tokens",
            len(compressed),
            len(messages),
            current_tokens,
        )

        return compressed

    def _build_atomic_units(self, messages: list[Message]) -> list[list[Message]]:
        """Group messages into atomic units.

        The key guarantee: tool messages are only kept together with the assistant
        message that initiated them (tool_calls). This prevents "tool result exists
        but initiating assistant message disappeared" after compression.
        """
        units: list[list[Message]] = []
        i = 0
        n = len(messages)

        while i < n:
            msg = messages[i]

            # Tool results should be attached to the nearest preceding assistant tool_calls.
            if msg.role == "tool":
                # Orphan tool message; keep as its own unit (we will avoid selecting it).
                units.append([msg])
                i += 1
                continue

            if msg.role == "assistant" and msg.tool_calls:
                tool_call_ids = {tc.id for tc in msg.tool_calls if tc.id}
                unit = [msg]
                j = i + 1

                # Collect subsequent tool results matching this assistant's tool_call ids.
                while j < n and messages[j].role == "tool":
                    tool_call_id = messages[j].tool_call_id
                    if not tool_call_ids or tool_call_id in tool_call_ids:
                        unit.append(messages[j])
                    j += 1

                units.append(unit)
                i = j
                continue

            units.append([msg])
            i += 1

        return units

    def _unit_has_tool_chain(self, unit: list[Message]) -> bool:
        if not unit:
            return False
        first = unit[0]
        if first.role != "assistant" or not first.tool_calls:
            return False
        return any(m.role == "tool" for m in unit[1:])

    def _truncate_tool_unit_to_fit(
        self, unit: list[Message], max_tokens: int
    ) -> list[Message] | None:
        """Try to truncate tool results within a unit to fit max_tokens.

        Returns a new unit if it can be made to fit, otherwise None.
        """
        if max_tokens <= 0 or not unit:
            return None

        # Only truncate units that include an initiating assistant message.
        if unit[0].role != "assistant":
            return None

        # 如果assistant消息是受保护的，不能截断整个unit
        if unit[0].is_protected():
            return None

        # If even the assistant message doesn't fit, give up.
        assistant_tokens = self.context_manager.estimate_messages_tokens([unit[0]])
        if assistant_tokens > max_tokens:
            return None

        remaining = max_tokens - assistant_tokens
        new_unit = [unit[0]]

        # Truncate tool results one by one to fit; keep order.
        for msg in unit[1:]:
            # 受保护的消息不能截断
            if msg.is_protected():
                msg_tokens = self.context_manager.estimate_messages_tokens([msg])
                if msg_tokens <= remaining:
                    new_unit.append(msg)
                    remaining -= msg_tokens
                else:
                    # 受保护消息必须保留，即使超过限制
                    new_unit.append(msg)
                    remaining = 0
                continue
            
            if msg.role != "tool":
                # Non-tool follow-ups are rare here; include only if fits.
                msg_tokens = self.context_manager.estimate_messages_tokens([msg])
                if msg_tokens <= remaining:
                    new_unit.append(msg)
                    remaining -= msg_tokens
                continue

            truncated_msg = self._truncate_tool_result(msg, remaining)
            if not truncated_msg:
                continue
            msg_tokens = self.context_manager.estimate_messages_tokens([truncated_msg])
            if msg_tokens <= remaining:
                new_unit.append(truncated_msg)
                remaining -= msg_tokens
            else:
                # Can't fit even after truncation.
                continue

        # Ensure we didn't create a unit with assistant tool_calls but zero results
        # when the original had tool results; that breaks the chain semantics.
        if self._unit_has_tool_chain(unit) and not self._unit_has_tool_chain(new_unit):
            return None

        if self.context_manager.estimate_messages_tokens(new_unit) <= max_tokens:
            return new_unit
        return None

    def _truncate_tool_result(self, msg: Message, max_tokens: int) -> Message | None:
        """Truncate a tool result message to fit within token limit.
        
        Args:
            msg: Tool result message
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated message or None if too large
        """
        # 受保护的消息不能截断
        if msg.is_protected():
            return msg
        
        if msg.role != "tool":
            return msg
        
        content = msg.content
        if not content:
            return msg
        
        # Try to parse as JSON and truncate
        try:
            data = json.loads(content)
            
            # If it's a list, truncate the list
            if isinstance(data, list):
                # Estimate tokens per item
                if not data:
                    return msg
                
                estimated_per_item = self.context_manager.estimate_tokens(
                    json.dumps(data[0], ensure_ascii=False)
                )
                max_items = max(1, max_tokens // estimated_per_item)
                
                if len(data) > max_items:
                    truncated_data = data[:max_items]
                    truncated_content = json.dumps(
                        truncated_data, ensure_ascii=False, default=str
                    )
                    truncated_msg = Message(
                        role=msg.role,
                        content=truncated_content,
                        name=msg.name,
                        tool_call_id=msg.tool_call_id,
                        tool_calls=msg.tool_calls,
                        priority=msg.priority,
                    )
                    return truncated_msg
            
            # If it's a dict, try to keep only essential fields
            elif isinstance(data, dict):
                # Keep only essential fields
                essential_fields = ["id", "title", "url", "summary", "error"]
                truncated_data = {
                    k: v for k, v in data.items() if k in essential_fields
                }
                
                truncated_content = json.dumps(
                    truncated_data, ensure_ascii=False, default=str
                )
                truncated_msg = Message(
                    role=msg.role,
                    content=truncated_content,
                    name=msg.name,
                    tool_call_id=msg.tool_call_id,
                    tool_calls=msg.tool_calls,
                    priority=msg.priority,
                )
                
                # Check if it fits
                if (
                    self.context_manager.estimate_messages_tokens([truncated_msg])
                    <= max_tokens
                ):
                    return truncated_msg
            
        except (json.JSONDecodeError, TypeError):
            # Not JSON, truncate as text
            pass
        
        # Fall back to text truncation
        estimated_chars = max_tokens * 4  # Rough estimate
        if len(content) > estimated_chars:
            truncated_content = content[:estimated_chars] + "..."
            truncated_msg = Message(
                role=msg.role,
                content=truncated_content,
                name=msg.name,
                tool_call_id=msg.tool_call_id,
                tool_calls=msg.tool_calls,
                priority=msg.priority,
            )
            return truncated_msg
        
        return msg

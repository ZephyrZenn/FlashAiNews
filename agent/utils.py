import re
import json
import logging

logger = logging.getLogger(__name__)


def _clean_control_characters(text: str) -> str:
    """Remove or replace invalid control characters in JSON string.
    
    JSON spec only allows these control characters when escaped:
    - Newline, carriage return, tab are allowed in JSON structure (between values)
    - Inside string values, they must be escaped as \\n, \\r, \\t
    
    LLMs sometimes output raw control characters that break parsing.
    """
    # Replace common problematic control characters with their escaped versions
    # or remove them entirely
    result = []
    for char in text:
        code = ord(char)
        if code < 32:  # Control character range
            if char == '\n':
                result.append('\n')  # Keep newlines for JSON formatting
            elif char == '\r':
                result.append('')    # Remove carriage returns
            elif char == '\t':
                result.append(' ')   # Replace tabs with spaces
            else:
                result.append('')    # Remove other control characters
        else:
            result.append(char)
    return ''.join(result)


def  extract_json(text: str) -> dict:
    """
    Extract JSON from LLM response, handling:
    - Pure JSON text
    - Markdown code blocks (```json ... ``` or ``` ... ```)
    - Invalid control characters from LLM output
    - Extra whitespace and newlines
    """
    if not text:
        raise ValueError("Empty text provided")
    
    text = text.strip()

    # Try multiple patterns for markdown code blocks
    patterns = [
        r"```(?:json|JSON)?\s*\n([\s\S]*?)\n```",  # Standard code block
        r"```(?:json|JSON)?\s*([\s\S]*?)```",       # Code block without newlines
    ]
    
    json_str = None
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            json_str = match.group(1).strip()
            break
    
    if json_str is None:
        # Try to find JSON object directly (starts with { and ends with })
        brace_match = re.search(r'\{[\s\S]*\}', text)
        if brace_match:
            json_str = brace_match.group(0).strip()
        else:
            json_str = text

    # Clean control characters BEFORE parsing (this is the key fix)
    json_str = _clean_control_characters(json_str)
    
    # Try parsing with strict=False first (allows control chars in strings)
    try:
        return json.loads(json_str, strict=False)
    except json.JSONDecodeError as e:
        logger.warning(
            "First JSON parse attempt failed at position %d: %s",
            e.pos, e.msg
        )
    
    # Second attempt: replace fancy quotes with standard JSON quotes
    sanitized = (
        json_str.replace(""", '"')
        .replace(""", '"')
        .replace("'", "'")
        .replace("'", "'")
    )
    try:
        return json.loads(sanitized, strict=False)
    except json.JSONDecodeError as e:
        logger.warning(
            "Second JSON parse attempt (after sanitizing quotes) failed at position %d: %s",
            e.pos, e.msg
        )
    
    # If that fails, try additional cleanup
    # Remove any remaining problematic characters more aggressively
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)
    
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError as e:
        logger.error(
            "JSON parse error at position %d: %s\nContext: %s",
            e.pos,
            e.msg,
            repr(cleaned[max(0, e.pos - 50):e.pos + 50])
        )
        raise ValueError(
            f"Failed to parse JSON. Error at position {e.pos}: {e.msg}\n"
            f"Near: {repr(cleaned[max(0, e.pos - 30):e.pos + 30])}"
        ) from e

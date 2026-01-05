import re
import json

def extract_json(text: str) -> dict:
    """
    Extract JSON from LLM response, handling:
    - Pure JSON text
    - Markdown code blocks (```json ... ``` or ``` ... ```)
    """
    text = text.strip()

    # Try to extract from markdown code block
    # Pattern matches ```json, ```JSON, or just ```
    pattern = r"```(?:json|JSON)?\s*\n?([\s\S]*?)\n?```"
    match = re.search(pattern, text)
    if match:
        json_str = match.group(1).strip()
    else:
        # Assume it's pure JSON
        json_str = text

    return json.loads(json_str)
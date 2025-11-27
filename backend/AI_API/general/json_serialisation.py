"""
JSON serialization utilities for consistent formatting across the application.

This module provides standardized JSON serialization functions to ensure:
- ASCII rare symbols support (ensure_ascii=False)
- Proper handling of non-JSON types like datetime (default=str)
- Appropriate formatting for different contexts (logging vs LLM prompts)
"""

import json
from typing import Any


def dumps_for_logging(obj: Any) -> str:
    """
    Serialize object to JSON string optimized for human-readable logging.

    Uses indentation for readability in log files and debugging.
    Supports unicode characters and converts non-JSON types to strings.

    Args:
        obj: Python object to serialize

    Returns:
        JSON string with indentation=2
    """
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def dumps_for_llm_prompt(obj: Any) -> str:
    """
    Serialize object to compact JSON string for LLM system prompts.

    Uses minimal whitespace to reduce token count and LLM API costs.
    Supports unicode characters and converts non-JSON types to strings.

    Args:
        obj: Python object to serialize

    Returns:
        Compact JSON string without indentation
    """
    return json.dumps(obj, ensure_ascii=False, default=str)

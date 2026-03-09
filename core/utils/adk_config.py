from __future__ import annotations

import os


def get_max_llm_calls(default: int = 6) -> int:
    raw = os.getenv("ADK_MAX_LLM_CALLS")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            return default
        return max(0, value)
    return default


def get_max_tool_calls(default: int = 1) -> int:
    raw = os.getenv("ADK_MAX_TOOL_CALLS")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            return default
        return max(0, value)
    return default

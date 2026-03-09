from __future__ import annotations

import os


def get_max_llm_calls(default: int = 0) -> int:
    raw = os.getenv("ADK_MAX_LLM_CALLS")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            return default
        return max(0, value)
    return default


def get_env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def get_max_tool_calls(default: int = 1) -> int:
    raw = os.getenv("ADK_MAX_TOOL_CALLS")
    if raw:
        try:
            value = int(raw)
        except ValueError:
            return default
        return max(0, value)
    return default

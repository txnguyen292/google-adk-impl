from __future__ import annotations

from typing import Any, Callable

from core.utils.adk_config import get_max_tool_calls

TOOL_CALL_COUNT_KEY = "__tool_calls"
TOOL_CALL_INVOCATION_KEY = "__tool_calls_invocation_id"


def _get_count(state: Any, invocation_id: str | None = None) -> int:
    try:
        if invocation_id:
            stored_invocation = state.get(TOOL_CALL_INVOCATION_KEY)
            if stored_invocation != invocation_id:
                return 0
        value = state.get(TOOL_CALL_COUNT_KEY, 0)
    except Exception:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def make_tool_call_guard(max_calls: int | None = None) -> tuple[Callable, Callable]:
    """Return (before_model, after_tool) callbacks to cap tool calls per invocation."""
    if max_calls is None:
        max_calls = get_max_tool_calls()

    def before_model(callback_context, llm_request):  # type: ignore[no-untyped-def]
        if max_calls <= 0:
            return None
        count = _get_count(callback_context.state, callback_context.invocation_id)
        if count < max_calls:
            return None
        try:
            from google.genai import types
        except Exception:
            return None
        cfg = llm_request.config or types.GenerateContentConfig()
        tool_cfg = cfg.tool_config or types.ToolConfig()
        fcc = tool_cfg.function_calling_config or types.FunctionCallingConfig()
        fcc.mode = types.FunctionCallingConfigMode.NONE
        tool_cfg.function_calling_config = fcc
        cfg.tool_config = tool_cfg
        llm_request.config = cfg
        return None

    def after_tool(tool, args, tool_context, tool_response):  # type: ignore[no-untyped-def]
        count = _get_count(tool_context.state, tool_context.invocation_id)
        tool_context.state[TOOL_CALL_INVOCATION_KEY] = tool_context.invocation_id
        tool_context.state[TOOL_CALL_COUNT_KEY] = count + 1
        return None

    return before_model, after_tool

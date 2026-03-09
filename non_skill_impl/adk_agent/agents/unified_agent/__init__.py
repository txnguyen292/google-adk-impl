from __future__ import annotations

from typing import Any, Awaitable, Callable

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool

from core.utils.adk_tool_guard import make_tool_call_guard
from adk_agent.skills.math.tools.alt_math_tools import (
    add,
    divide,
    format_math_response,
    multiply,
    subtract,
)
from adk_agent.skills.math.tools.differential_tools import solve_differential_equation
from adk_agent.skills.web_search.tools.web_search import (
    WebSearchClient,
    build_web_search_tool,
)


def build_unified_agent(
    session_id: str,
    lite_llm: Any,
    normalize_callback: Callable[..., Awaitable[None]] | None,
    search_client: WebSearchClient,
) -> Agent:
    del session_id
    web_tool = build_web_search_tool(search_client)
    guard_before, guard_after = make_tool_call_guard()
    before_callbacks = [cb for cb in (normalize_callback, guard_before) if cb]
    return Agent(
        name="unified_agent",
        description=(
            "Handles web search and math directly with one tool-enabled agent."
        ),
        model=lite_llm,
        instruction=(
            "You are a single direct-tools agent with two capabilities: web search and math.\n"
            "- Use the web_search tool for current, live, or lookup-based questions.\n"
            "- Use math tools for arithmetic, multi-step calculations, and supported differential equations.\n"
            "- If a request needs both, use web_search first and then math tools.\n"
            "- Do not do math in your head when a math tool can be used.\n"
            "- After any math computation, call format_math_response with the original expression or equation and the computed result before you present the final answer.\n"
            "- When web_search is used, include concise citations from the tool result in the final answer.\n"
            "- Stay within those capabilities only."
        ),
        tools=[
            FunctionTool(func=add),
            FunctionTool(func=subtract),
            FunctionTool(func=multiply),
            FunctionTool(func=divide),
            FunctionTool(func=solve_differential_equation),
            FunctionTool(func=format_math_response),
            FunctionTool(func=web_tool),
        ],
        before_model_callback=before_callbacks,
        after_tool_callback=[guard_after],
    )


from . import agent as agent  # noqa: E402,F401

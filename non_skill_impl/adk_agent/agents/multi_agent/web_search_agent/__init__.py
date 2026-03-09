from __future__ import annotations

from typing import Any, Awaitable, Callable

from google.adk.agents import Agent

from core.utils.skill_loader import load_skill_prompt
from core.utils.adk_tool_guard import make_tool_call_guard
from adk_agent.skills.web_search.tools.web_search import (
    WebSearchClient,
    build_web_search_tool,
)


def build_web_search_agent(
    session_id: str,
    lite_llm: Any,
    normalize_callback: Callable[..., Awaitable[None]] | None,
    search_client: WebSearchClient,
) -> Agent:
    web_tool = build_web_search_tool(search_client)
    guard_before, guard_after = make_tool_call_guard()
    before_callbacks = [cb for cb in (normalize_callback, guard_before) if cb]
    return Agent(
        name="web_search_agent",
        model=lite_llm,
        instruction=load_skill_prompt("web_search"),
        tools=[web_tool],
        before_model_callback=before_callbacks,
        after_tool_callback=[guard_after],
    )


# Expose agent module for ADK eval loader (expects agent.root_agent)
from . import agent as agent  # noqa: E402,F401

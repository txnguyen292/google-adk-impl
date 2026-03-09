from __future__ import annotations

from typing import Any, Awaitable, Callable

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool

from core.utils.skill_loader import load_skill_prompt
from adk_agent.skills.math.tools.alt_math_tools import (
    add,
    divide,
    format_math_response,
    multiply,
    subtract,
)
from adk_agent.skills.math.tools.differential_tools import solve_differential_equation


def build_math_agent(
    session_id: str,
    lite_llm: Any,
    normalize_callback: Callable[..., Awaitable[None]] | None,
) -> Agent:
    tools = [
        FunctionTool(func=add),
        FunctionTool(func=subtract),
        FunctionTool(func=multiply),
        FunctionTool(func=divide),
        FunctionTool(func=solve_differential_equation),
        FunctionTool(func=format_math_response),
    ]
    return Agent(
        name="math_agent",
        description=(
            "Solves arithmetic expressions and supported differential equations "
            "by delegating computation and final answer formatting to deterministic tools."
        ),
        model=lite_llm,
        instruction=load_skill_prompt("math"),
        tools=tools,
        before_model_callback=normalize_callback,
        disallow_transfer_to_parent=False,
        disallow_transfer_to_peers=True,
    )


# Expose agent module for ADK eval loader (expects agent.root_agent)
from . import agent as agent  # noqa: E402,F401

from __future__ import annotations

from typing import Any

from google.adk.tools.function_tool import FunctionTool

from adk_agent.skills.math.tools.alt_math_tools import (
    add,
    divide,
    format_math_response,
    multiply,
    subtract,
)
from adk_agent.skills.math.tools.differential_tools import solve_differential_equation


def build_tools(**_: Any) -> list[Any]:
    return [
        FunctionTool(func=add),
        FunctionTool(func=subtract),
        FunctionTool(func=multiply),
        FunctionTool(func=divide),
        FunctionTool(func=solve_differential_equation),
        FunctionTool(func=format_math_response),
    ]

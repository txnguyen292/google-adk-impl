from __future__ import annotations

from typing import Any

from google.adk.tools.function_tool import FunctionTool

from adk_agent.skills.web_search.tools.web_search import build_web_search_tool


def build_tools(*, search_client: Any, **_: Any) -> list[Any]:
    return [FunctionTool(func=build_web_search_tool(search_client))]

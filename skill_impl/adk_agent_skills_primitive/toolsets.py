from __future__ import annotations

import importlib.util
from typing import Any

from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.skills import Skill
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.skill_toolset import (
    ListSkillsTool,
    LoadSkillResourceTool,
    LoadSkillTool,
    SkillToolset,
)
from adk_agent_skills_primitive.paths import get_native_skill_dir

_ACTIVE_SKILL_KEY = "active_skill"


def _load_runtime_builder(skill_name: str):
    skill_key = {
        "web-search": "web_search",
    }.get(skill_name, skill_name)
    script_path = get_native_skill_dir(skill_key) / "scripts" / "runtime_tools.py"
    module_name = f"adk_native_skill_runtime_{skill_name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load runtime tools from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    builder = getattr(module, "build_tools", None)
    if not callable(builder):
        raise AttributeError(f"{script_path} is missing a callable build_tools")
    return builder


class ActivatingLoadSkillTool(LoadSkillTool):
    async def run_async(self, *, args: dict[str, Any], tool_context) -> Any:
        result = await super().run_async(args=args, tool_context=tool_context)
        if isinstance(result, dict) and "error" not in result and args.get("name"):
            tool_context.state[_ACTIVE_SKILL_KEY] = args["name"]
        return result


class ActivatingSkillToolset(SkillToolset):
    def __init__(self, skills: list[Skill]):
        super().__init__(skills=skills)
        self._tools = [
            ListSkillsTool(self),
            ActivatingLoadSkillTool(self),
            LoadSkillResourceTool(self),
        ]


class SkillScopedRuntimeToolset(BaseToolset):
    def __init__(self, search_client: Any):
        super().__init__()
        self._math_tools = _load_runtime_builder("math")()
        self._web_search_tools = _load_runtime_builder("web-search")(
            search_client=search_client
        )

    async def get_tools(
        self,
        readonly_context: ReadonlyContext | None = None,
    ) -> list[Any]:
        if readonly_context is None:
            return []

        active_skill = readonly_context.state.get(_ACTIVE_SKILL_KEY)
        if active_skill == "math":
            return self._math_tools
        if active_skill == "web-search":
            return self._web_search_tools
        return []


__all__ = [
    "ActivatingSkillToolset",
    "SkillScopedRuntimeToolset",
]

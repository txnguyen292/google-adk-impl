from __future__ import annotations

import importlib.util
from typing import Any
import yaml

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
_ACTIVE_ALLOWED_TOOL_NAMES_KEY = "active_allowed_tool_names"


def _parse_allowed_tool_names(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [tool.strip() for tool in raw.split(",") if tool.strip()]


def _extract_allowed_tool_names_from_markdown(content: str) -> list[str]:
    if not content.startswith("---"):
        return []
    parts = content.split("---", 2)
    if len(parts) < 3:
        return []
    try:
        parsed = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return []
    if not isinstance(parsed, dict):
        return []
    raw = parsed.get("allowed-tools") or parsed.get("allowed_tools")
    if not isinstance(raw, str):
        return []
    return _parse_allowed_tool_names(raw)


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
            skill_name = args["name"]
            tool_context.state[_ACTIVE_SKILL_KEY] = skill_name
            skill = self._toolset._get_skill(skill_name)
            if skill is not None:
                tool_context.state[_ACTIVE_ALLOWED_TOOL_NAMES_KEY] = (
                    _parse_allowed_tool_names(skill.frontmatter.allowed_tools)
                )
        return result


class ActivatingLoadSkillResourceTool(LoadSkillResourceTool):
    async def run_async(self, *, args: dict[str, Any], tool_context) -> Any:
        result = await super().run_async(args=args, tool_context=tool_context)
        if not isinstance(result, dict) or "error" in result:
            return result

        skill_name = args.get("skill_name")
        if not skill_name or tool_context.state.get(_ACTIVE_SKILL_KEY) != skill_name:
            return result

        unlocked_tools = _extract_allowed_tool_names_from_markdown(
            str(result.get("content") or "")
        )
        if not unlocked_tools:
            return result

        current = tool_context.state.get(_ACTIVE_ALLOWED_TOOL_NAMES_KEY, [])
        current_names = list(current) if isinstance(current, list) else []
        merged = current_names[:]
        for tool_name in unlocked_tools:
            if tool_name not in merged:
                merged.append(tool_name)
        tool_context.state[_ACTIVE_ALLOWED_TOOL_NAMES_KEY] = merged
        return result


class ActivatingSkillToolset(SkillToolset):
    def __init__(self, skills: list[Skill]):
        super().__init__(skills=skills)
        self._tools = [
            ListSkillsTool(self),
            ActivatingLoadSkillTool(self),
            ActivatingLoadSkillResourceTool(self),
        ]


class SkillScopedRuntimeToolset(BaseToolset):
    def __init__(self, search_client: Any):
        super().__init__()
        self._math_tools = _load_runtime_builder("math")()
        self._web_search_tools = _load_runtime_builder("web-search")(
            search_client=search_client
        )
        self._skill_tools = {
            "math": self._math_tools,
            "web-search": self._web_search_tools,
        }

    async def get_tools(
        self,
        readonly_context: ReadonlyContext | None = None,
    ) -> list[Any]:
        if readonly_context is None:
            return []

        active_skill = readonly_context.state.get(_ACTIVE_SKILL_KEY)
        if active_skill not in self._skill_tools:
            return []

        tools = self._skill_tools[active_skill]
        allowed_tool_names = readonly_context.state.get(_ACTIVE_ALLOWED_TOOL_NAMES_KEY)
        if not isinstance(allowed_tool_names, list) or not allowed_tool_names:
            return tools
        return [tool for tool in tools if tool.name in allowed_tool_names]
        return []


__all__ = [
    "ActivatingSkillToolset",
    "SkillScopedRuntimeToolset",
]

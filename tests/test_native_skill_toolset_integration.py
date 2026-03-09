from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

from google.adk.skills import load_skill_from_dir

from adk_agent.skills.web_search.tools.web_search import WebSearchResult
from adk_agent_skills_primitive.toolsets import (
    ActivatingSkillToolset,
    SkillScopedRuntimeToolset,
)


class DummySearchClient:
    def search(self, query: str, max_results: int = 5) -> WebSearchResult:
        return WebSearchResult(
            answer_text=f"result for {query}",
            citations=[{"title": "example", "url": "https://example.com"}],
            snippets=["latest update"],
            numbers=[1.0, 2.0],
        )


def _native_skill_root() -> Path:
    return (
        Path(__file__).resolve().parents[1]
        / "skill_impl"
        / "adk_agent_skills_primitive"
        / "native_skills"
    )


async def _visible_math_tools(skill_root: Path) -> tuple[list[str], list[str]]:
    skill_toolset = ActivatingSkillToolset(
        skills=[
            load_skill_from_dir(skill_root / "math"),
            load_skill_from_dir(skill_root / "web-search"),
        ]
    )
    runtime_toolset = SkillScopedRuntimeToolset(DummySearchClient())
    tool_context = SimpleNamespace(state={})
    readonly = SimpleNamespace(state=tool_context.state)

    load_skill = skill_toolset._tools[1]
    load_resource = skill_toolset._tools[2]

    await load_skill.run_async(args={"name": "math"}, tool_context=tool_context)
    before = [tool.name for tool in await runtime_toolset.get_tools(readonly)]

    await load_resource.run_async(
        args={
            "skill_name": "math",
            "path": "references/differential-equations.md",
        },
        tool_context=tool_context,
    )
    after = [tool.name for tool in await runtime_toolset.get_tools(readonly)]
    return before, after


def test_math_reference_unlocks_solver_from_live_skill_files():
    before, after = asyncio.run(_visible_math_tools(_native_skill_root()))

    assert before == [
        "add",
        "subtract",
        "multiply",
        "divide",
        "format_math_response",
    ]
    assert after == [
        "add",
        "subtract",
        "multiply",
        "divide",
        "solve_differential_equation",
        "format_math_response",
    ]


def test_math_reference_without_allowed_tools_does_not_unlock_solver(tmp_path: Path):
    skill_root = tmp_path / "native_skills"
    shutil.copytree(_native_skill_root(), skill_root)

    reference_path = (
        skill_root / "math" / "references" / "differential-equations.md"
    )
    content = reference_path.read_text()
    content = re.sub(
        r"^---\nallowed-tools:\s*solve_differential_equation\n---\n\n",
        "",
        content,
        count=1,
    )
    reference_path.write_text(content)

    before, after = asyncio.run(_visible_math_tools(skill_root))

    assert before == [
        "add",
        "subtract",
        "multiply",
        "divide",
        "format_math_response",
    ]
    assert after == before

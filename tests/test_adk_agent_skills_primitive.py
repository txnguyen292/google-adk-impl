from __future__ import annotations

import asyncio
from types import SimpleNamespace

from google.adk.tools.skill_toolset import SkillToolset

from adk_agent import adk_fix
from adk_agent.agents.multi_agent.math_agent import build_math_agent
from adk_agent.agents.unified_agent import build_unified_agent
from adk_agent_skills_primitive.agents.orchestrator.builder import build_root_agent
from adk_agent_skills_primitive.native_skills import load_native_skills
from adk_agent_skills_primitive.toolsets import SkillScopedRuntimeToolset
from core.utils.litellm_config import LiteLLMConfig
from adk_agent.skills.math.tools.alt_math_tools import format_math_response
from adk_agent.skills.math.tools.differential_tools import solve_differential_equation
from adk_agent.skills.web_search.tools.web_search import WebSearchResult

adk_fix.silence_pydantic_pedantry()


class DummySearchClient:
    def search(self, query: str, max_results: int = 5) -> WebSearchResult:
        return WebSearchResult(
            answer_text=f"result for {query}",
            citations=[{"title": "example", "url": "https://example.com"}],
            snippets=["latest update"],
            numbers=[1.0, 2.0],
        )


def test_native_adk_skills_load_expected_names():
    skills = load_native_skills()

    assert [skill.name for skill in skills] == ["math", "web-search"]
    assert all(skill.instructions for skill in skills)


def test_build_root_agent_uses_skill_toolset_and_runtime_tools():
    agent = build_root_agent(
        session_id="test",
        search_client=DummySearchClient(),
        config=LiteLLMConfig(),
    )

    assert agent.name == "orchestrator"
    assert isinstance(agent.tools[0], SkillToolset)
    assert isinstance(agent.tools[1], SkillScopedRuntimeToolset)
    assert len(agent.tools) == 2
    assert "Stay strictly within the capabilities you discover from the available native skills." in agent.instruction
    assert "Start by calling list_skills before you decide which skill to load." in agent.instruction
    assert "Never perform work yourself when an available skill can perform it." in agent.instruction
    assert "Do not present yourself as a general-purpose assistant." in agent.instruction
    assert "Execution tools for a skill become available only after that skill is loaded." in agent.instruction
    assert "Available skills\n- math" not in agent.instruction


def test_runtime_toolset_only_exposes_tools_for_active_skill():
    toolset = SkillScopedRuntimeToolset(DummySearchClient())

    no_skill_tools = asyncio.run(toolset.get_tools(SimpleNamespace(state={})))
    math_tools = asyncio.run(toolset.get_tools(SimpleNamespace(state={"active_skill": "math"})))
    web_tools = asyncio.run(
        toolset.get_tools(SimpleNamespace(state={"active_skill": "web-search"}))
    )

    assert no_skill_tools == []
    assert [tool.name for tool in math_tools] == [
        "add",
        "subtract",
        "multiply",
        "divide",
        "solve_differential_equation",
        "format_math_response",
    ]
    assert [tool.name for tool in web_tools] == ["web_search"]


def test_non_skill_math_agent_exposes_solver_and_formatter_tools():
    agent = build_math_agent(
        session_id="test",
        lite_llm="test-model",
        normalize_callback=None,
    )

    assert [tool.name for tool in agent.tools] == [
        "add",
        "subtract",
        "multiply",
        "divide",
        "solve_differential_equation",
        "format_math_response",
    ]


def test_unified_agent_exposes_web_and_math_tools():
    agent = build_unified_agent(
        session_id="test",
        lite_llm="test-model",
        normalize_callback=None,
        search_client=DummySearchClient(),
    )

    assert [tool.name for tool in agent.tools] == [
        "add",
        "subtract",
        "multiply",
        "divide",
        "solve_differential_equation",
        "format_math_response",
        "web_search",
    ]


def test_format_math_response_returns_equation():
    formatted = format_math_response("19.75*84", 1659.0)

    assert formatted["status"] == "success"
    assert formatted["equation"] == "19.75 × 84 = 1659.0"


def test_solve_differential_equation_tool():
    result = solve_differential_equation("dy/dx = y")

    assert result["status"] == "success"
    assert result["solution"] == "y(x) = C1*exp(x)"
    assert result["pretty_solution"]
    assert result["latex_solution"] == "y{\\left(x \\right)} = C_{1} e^{x}"


def test_format_math_response_preserves_differential_rendering():
    result = solve_differential_equation("dy/dx = x*y")
    formatted = format_math_response("dy/dx = x*y", result)

    assert formatted["status"] == "success"
    assert formatted["equation"] == "y(x) = C1*exp(x**2/2)"
    assert formatted["pretty_equation"] == "y(x) = C₁·exp(x²/2)"
    assert "Differential equation:\n" in formatted["final_answer"]
    assert "dy/dx = x·y" in formatted["final_answer"]
    assert "y(x) = C₁·exp(x²/2)" in formatted["final_answer"]
    assert "y{\\left(x \\right)} = C_{1} e^{\\frac{x^{2}}{2}}" == formatted["latex_equation"]

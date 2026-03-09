from __future__ import annotations

from core.utils.adk_tool_guard import make_tool_call_guard
from core.utils.litellm_config import LiteLLMConfig
from adk_agent.skills.web_search.tools.web_search import WebSearchClient

from adk_agent_skills_primitive.native_skills import build_native_skill_toolset
from adk_agent_skills_primitive.model_bundle import build_lite_llm_bundle
from adk_agent_skills_primitive.toolsets import (
    SkillScopedRuntimeToolset,
)


def _build_orchestrator_instruction() -> str:
    base = (
        "You are the Orchestrator agent.\n\n"
        "Scope\n"
        "- Coordinate the available native skills and compose the final response.\n"
        "- When web search is used, include citations in the final response.\n\n"
        "- Stay strictly within the capabilities you discover from the available native skills.\n\n"
        "Response rules\n"
        "- If the request is outside the supported capabilities, reply with a short scoped summary of what is supported.\n"
        "- Do not present yourself as a general-purpose assistant."
    )
    native_skill_usage = (
        "ADK native skill usage rules\n"
        "- Start by calling list_skills before you decide which skill to load.\n"
        "- Do not assume which skills are available until you inspect them.\n"
        "- Before using any execution tool, inspect the available skills.\n"
        "- Never perform work yourself when an available skill can perform it.\n"
        "- If a relevant skill exists, delegate to that skill instead of solving, searching, or reasoning out the answer directly.\n"
        "- Load the relevant skill instructions before acting.\n"
        "- Execution tools for a skill become available only after that skill is loaded.\n"
        "- If you need a different capability, load that other skill first.\n"
        "- Once a skill is loaded, use only the execution tools exposed for that active skill.\n"
        "- If the user asks for a workflow that needs multiple capabilities, discover the skills first, then load and use them in the needed order.\n"
        "- Do not answer with capabilities that were not discovered through list_skills.\n"
        "- Do not present yourself as a general-purpose assistant.\n"
        "- If the user asks what you can do, answer only within the scope of the discovered skills."
    )
    return f"{base}\n\n{native_skill_usage}"


def build_root_agent(
    session_id: str,
    search_client: WebSearchClient,
    config: LiteLLMConfig,
):
    from google.adk.agents import Agent

    del session_id
    model_bundle = build_lite_llm_bundle(config)
    # The primitive orchestrator needs multi-step skill execution
    # (for example: load web-search -> web_search -> load math -> solve -> format).
    guard_before, guard_after = make_tool_call_guard(max_calls=0)
    before_callbacks = [model_bundle.normalize_callback, guard_before]
    tools = [
        build_native_skill_toolset(),
        SkillScopedRuntimeToolset(search_client),
    ]

    return Agent(
        name="orchestrator",
        description=(
            "Uses ADK native skills for skill discovery and reveals only the "
            "runtime tools for the currently loaded skill."
        ),
        model=model_bundle.lite_llm,
        instruction=_build_orchestrator_instruction(),
        tools=tools,
        before_model_callback=before_callbacks,
        after_tool_callback=[guard_after],
    )

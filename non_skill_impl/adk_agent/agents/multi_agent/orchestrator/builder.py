from __future__ import annotations

from core.utils.litellm_config import LiteLLMConfig
from core.utils.skill_loader import load_orchestrator_prompt
from core.utils.adk_tool_guard import make_tool_call_guard
from adk_agent.skills.web_search.tools.web_search import WebSearchClient

from adk_agent.agents.multi_agent.math_agent import build_math_agent
from adk_agent.agents.multi_agent.web_search_agent import build_web_search_agent


def build_root_agent(
    session_id: str,
    search_client: WebSearchClient,
    config: LiteLLMConfig,
):
    from google.adk.agents import Agent
    from google.adk.models.lite_llm import LiteLlm
    from google.adk.tools.agent_tool import AgentTool

    config.apply()
    expected_model = config.litellm_model()

    async def _normalize_model(callback_context, llm_request) -> None:
        if llm_request.model != expected_model:
            llm_request.model = expected_model
        return None

    lite_llm_kwargs = {
        "model": expected_model,
        "temperature": config.temperature,
        "drop_params": config.drop_params,
    }
    provider = config.llm_provider()
    if provider:
        lite_llm_kwargs["custom_llm_provider"] = provider
    lite_llm = LiteLlm(**lite_llm_kwargs)

    math_agent = build_math_agent(session_id, lite_llm, _normalize_model)
    web_agent = build_web_search_agent(
        session_id,
        lite_llm,
        _normalize_model,
        search_client,
    )

    guard_before, guard_after = make_tool_call_guard()
    before_callbacks = [_normalize_model, guard_before]
    root_agent = Agent(
        name="orchestrator",
        model=lite_llm,
        instruction=load_orchestrator_prompt(),
        tools=[AgentTool(agent=math_agent), AgentTool(agent=web_agent)],
        before_model_callback=before_callbacks,
        after_tool_callback=[guard_after],
    )
    return root_agent


__all__ = ["build_root_agent"]

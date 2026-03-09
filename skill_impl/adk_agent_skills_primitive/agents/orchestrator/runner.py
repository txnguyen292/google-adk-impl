from __future__ import annotations

import os

from adk_agent.utils.runner_utils import collect_final_response
from core.utils.litellm_config import LiteLLMConfig
from adk_agent.skills.web_search.tools.web_search import DuckDuckGoSearchClient, WebSearchClient

_session_service = None
_session_cache: set[str] = set()


async def _ensure_session(app_name: str, session_id: str, user_id: str):
    global _session_service
    from google.adk.sessions import InMemorySessionService

    if _session_service is None:
        _session_service = InMemorySessionService()
    if session_id in _session_cache:
        return _session_service
    await _session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    _session_cache.add(session_id)
    return _session_service


async def run_adk_skills_primitive_orchestrator(
    message: str,
    session_id: str,
    search_client: WebSearchClient | None = None,
    config: LiteLLMConfig | None = None,
) -> str:
    from google.adk.agents.run_config import RunConfig
    from google.adk.apps.app import App
    from google.adk.artifacts.in_memory_artifact_service import (
        InMemoryArtifactService,
    )
    from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
    from google.adk.runners import Runner

    from adk_agent_skills_primitive.agents.orchestrator.builder import build_root_agent
    from adk_agent_skills_primitive.agents.orchestrator.constants import (
        ADK_APP_NAME,
        ADK_USER_ID,
    )
    from core.utils.adk_config import get_max_llm_calls

    client = search_client or DuckDuckGoSearchClient()
    config = config or LiteLLMConfig.from_env()
    root_agent = build_root_agent(session_id, client, config=config)
    session_service = await _ensure_session(
        ADK_APP_NAME,
        session_id,
        ADK_USER_ID,
    )
    app = App(name=ADK_APP_NAME, root_agent=root_agent)
    runner = Runner(
        app=app,
        app_name=ADK_APP_NAME,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )
    run_config = RunConfig(max_llm_calls=get_max_llm_calls())
    debug = os.getenv("ADK_DEBUG", "").strip().lower() in {"1", "true", "yes", "y"}
    try:
        final_text = await collect_final_response(
            runner=runner,
            user_id=ADK_USER_ID,
            session_id=session_id,
            message=message,
            run_config=run_config,
            final_author="orchestrator",
            debug=debug,
        )
    finally:
        await runner.close()
    return final_text


__all__ = ["run_adk_skills_primitive_orchestrator"]

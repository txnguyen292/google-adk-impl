from __future__ import annotations

from adk_agent import adk_fix

adk_fix.silence_pydantic_pedantry()

from google.adk.apps.app import App  # noqa: E402

from core.utils.litellm_config import LiteLLMConfig  # noqa: E402
from adk_agent.skills.web_search.tools.web_search import DuckDuckGoSearchClient  # noqa: E402

from adk_agent_skills_primitive.agents.orchestrator.builder import (  # noqa: E402
    build_root_agent,
)


_APP_NAME = "orchestrator"

config = LiteLLMConfig.from_env()
root_agent = build_root_agent(
    _APP_NAME,
    DuckDuckGoSearchClient(),
    config=config,
)

app = App(name=_APP_NAME, root_agent=root_agent)
agent = app

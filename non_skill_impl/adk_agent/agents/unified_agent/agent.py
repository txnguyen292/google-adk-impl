from __future__ import annotations

from adk_agent import adk_fix

adk_fix.silence_pydantic_pedantry()

from google.adk.apps.app import App  # noqa: E402
from google.adk.models.lite_llm import LiteLlm  # noqa: E402

from core.utils.litellm_config import LiteLLMConfig  # noqa: E402
from adk_agent.agents.unified_agent import build_unified_agent  # noqa: E402
from adk_agent.skills.web_search.tools.web_search import DuckDuckGoSearchClient  # noqa: E402


_APP_NAME = "unified_agent"

config = LiteLLMConfig.from_env()
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

root_agent = build_unified_agent(
    _APP_NAME,
    lite_llm,
    _normalize_model,
    DuckDuckGoSearchClient(),
)

app = App(name=_APP_NAME, root_agent=root_agent)
agent = app

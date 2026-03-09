from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.utils.litellm_config import LiteLLMConfig


@dataclass(frozen=True)
class AdkModelBundle:
    lite_llm: Any
    normalize_callback: Any


def build_lite_llm_bundle(config: LiteLLMConfig) -> AdkModelBundle:
    from google.adk.models.lite_llm import LiteLlm

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

    return AdkModelBundle(
        lite_llm=LiteLlm(**lite_llm_kwargs),
        normalize_callback=_normalize_model,
    )

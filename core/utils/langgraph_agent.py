from __future__ import annotations

from typing import Any

from core.utils.litellm_config import LiteLLMConfig


def build_langgraph_model(config: LiteLLMConfig):
    try:
        from langchain_litellm import ChatLiteLLM
    except Exception:
        try:
            from langchain_community.chat_models import ChatLiteLLM
        except Exception:
            model_id = config.litellm_model()
            if "/" in model_id and ":" not in model_id:
                provider, name = model_id.split("/", 1)
                return f"{provider}:{name}"
            return model_id
    return ChatLiteLLM(
        model=config.litellm_model(),
        temperature=config.temperature,
    )


def last_message_content(messages: list[Any]) -> str:
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, dict):
        return str(last.get("content", "")).strip()
    return str(getattr(last, "content", "")).strip()

from __future__ import annotations

import json
from typing import Any

import litellm

from core.utils.litellm_config import LiteLLMConfig


def _extract_json(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(stripped[start : end + 1])
            except json.JSONDecodeError:
                return None
    return None


def call_llm_for_json(
    config: LiteLLMConfig,
    system_prompt: str,
    user_message: str,
    temperature: float = 0,
) -> dict[str, Any]:
    response = litellm.completion(
        model=config.litellm_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
    )
    content = (
        response.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    payload = _extract_json(content)
    if not payload:
        raise ValueError("LLM did not return JSON.")
    return payload

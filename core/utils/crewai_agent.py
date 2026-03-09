from __future__ import annotations

import json
from typing import Any

from crewai import LLM

from core.utils.litellm_config import LiteLLMConfig


def build_crewai_llm(
    config: LiteLLMConfig,
    model: str | None = None,
) -> LLM:
    config.apply()
    return LLM(
        model=model or config.litellm_model(),
        temperature=config.temperature,
    )


def extract_crewai_text(result: Any) -> str:
    if result is None:
        return ""
    if isinstance(result, str):
        return result.strip()

    raw = getattr(result, "raw", None)
    if isinstance(raw, str) and raw.strip():
        return raw.strip()

    json_dict = getattr(result, "json_dict", None)
    if json_dict is not None:
        try:
            return json.dumps(json_dict, ensure_ascii=True)
        except Exception:
            pass

    output = getattr(result, "output", None)
    if isinstance(output, str) and output.strip():
        return output.strip()

    return str(result).strip()


__all__ = ["build_crewai_llm", "extract_crewai_text"]

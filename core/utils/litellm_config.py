from __future__ import annotations

import os
from dataclasses import dataclass
import litellm

DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_gpt5_model(model: str) -> bool:
    value = model.strip().lower()
    return value.startswith("gpt-5") or "/gpt-5" in value


@dataclass(slots=True)
class LiteLLMConfig:
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    drop_params: bool = False
    provider: str | None = None
    ssl_verify: bool = False

    @classmethod
    def from_env(cls) -> "LiteLLMConfig":
        model = os.getenv("LITELLM_MODEL", DEFAULT_MODEL)
        provider = os.getenv("LITELLM_PROVIDER")
        temperature_raw = os.getenv("LITELLM_TEMPERATURE", str(DEFAULT_TEMPERATURE))
        try:
            temperature = float(temperature_raw)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"LITELLM_TEMPERATURE must be numeric, got '{temperature_raw}'."
            ) from exc
        drop_params = _parse_bool(os.getenv("LITELLM_DROP_PARAMS")) or False
        ssl_verify = _parse_bool(os.getenv("LITELLM_SSL_VERIFY"))
        if ssl_verify is None:
            ssl_verify = False
        if _is_gpt5_model(model):
            temperature = 1.0
            drop_params = True
        return cls(
            model=model,
            temperature=temperature,
            drop_params=drop_params,
            provider=provider,
            ssl_verify=ssl_verify,
        )

    def apply(self) -> None:
        litellm.ssl_verify = self.ssl_verify
        if self.drop_params:
            litellm.drop_params = True

    def litellm_model(self) -> str:
        model = (self.model or "").strip()
        if not model:
            return model
        if "/" in model:
            return model
        if self.provider:
            return f"{self.provider}/{model}"
        return model

    def llm_provider(self) -> str | None:
        if self.provider:
            return self.provider
        model = (self.model or "").strip()
        if "/" in model:
            return model.split("/", 1)[0]
        return None

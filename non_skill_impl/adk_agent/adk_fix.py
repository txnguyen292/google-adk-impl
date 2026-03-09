from __future__ import annotations

from pydantic.json_schema import GenerateJsonSchema
from pydantic_core import core_schema
from pydantic._internal import _generate_schema


def _patch_mcp_client_session() -> None:
    try:
        from mcp.client.session import ClientSession  # type: ignore
    except Exception:
        return

    if hasattr(ClientSession, "__get_pydantic_core_schema__"):
        return

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):  # type: ignore[no-untyped-def]
        return core_schema.any_schema()

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):  # type: ignore[no-untyped-def]
        return {"type": "object", "title": "MCP ClientSession"}

    ClientSession.__get_pydantic_core_schema__ = __get_pydantic_core_schema__  # type: ignore[attr-defined]
    ClientSession.__get_pydantic_json_schema__ = __get_pydantic_json_schema__  # type: ignore[attr-defined]


def _patch_fastapi_openapi() -> None:
    try:
        import fastapi.openapi.utils as fastapi_utils
    except Exception:
        return

    if getattr(fastapi_utils.get_openapi, "__adk_fix__", False):
        return

    original = fastapi_utils.get_openapi

    def safe_get_openapi(*args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return original(*args, **kwargs)
        except Exception:
            return {
                "openapi": "3.1.0",
                "info": {
                    "title": kwargs.get("title", "API"),
                    "version": kwargs.get("version", "0.0.0"),
                },
                "paths": {},
            }

    safe_get_openapi.__adk_fix__ = True  # type: ignore[attr-defined]
    fastapi_utils.get_openapi = safe_get_openapi  # type: ignore[assignment]


def _patch_run_config_defaults() -> None:
    try:
        from core.utils.adk_config import get_max_llm_calls
    except Exception:
        return
    max_calls = get_max_llm_calls()
    try:
        from google.adk.agents.run_config import RunConfig
    except Exception:
        return

    field = RunConfig.model_fields.get("max_llm_calls")
    if not field:
        return
    field.default = max_calls
    field.default_factory = None

def silence_pydantic_pedantry() -> None:
    """Force Pydantic to tolerate non-JSON-serializable types in OpenAPI."""
    try:
        from pathlib import Path
        from core.utils.dotenv import load_dotenv

        repo_root = Path(__file__).resolve().parents[1]
        load_dotenv(path=str(repo_root / ".env"))
    except Exception:
        pass
    original_handler = GenerateJsonSchema.handle_invalid_for_json_schema

    def patched_handler(self, schema, error_info):  # type: ignore[no-untyped-def]
        return {"type": "object", "title": f"Internal Object ({error_info})"}

    if GenerateJsonSchema.handle_invalid_for_json_schema is not patched_handler:
        GenerateJsonSchema.handle_invalid_for_json_schema = patched_handler
        GenerateJsonSchema._original_handle_invalid_for_json_schema = original_handler  # type: ignore[attr-defined]

    _patch_mcp_client_session()

    def _unknown_type_schema(self, obj):  # type: ignore[no-untyped-def]
        return core_schema.any_schema()

    if _generate_schema.GenerateSchema._unknown_type_schema is not _unknown_type_schema:
        _generate_schema.GenerateSchema._unknown_type_schema = _unknown_type_schema

    _patch_fastapi_openapi()
    _patch_run_config_defaults()

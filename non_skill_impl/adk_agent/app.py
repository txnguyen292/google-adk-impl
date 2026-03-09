from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from pydantic.errors import PydanticSchemaGenerationError

from adk_agent.agents.multi_agent.orchestrator import run_adk_orchestrator
from adk_agent.adk_fix import silence_pydantic_pedantry
from core.utils.observability import log_event
from adk_agent.skills.web_search.tools.web_search import DuckDuckGoSearchClient


class ChatRequest(BaseModel):
    session_id: str
    message: str


class HealthResponse(BaseModel):
    status: str


silence_pydantic_pedantry()
app = FastAPI(title="ADK Bakeoff")
search_client = DuckDuckGoSearchClient()


def _safe_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    try:
        app.openapi_schema = get_openapi(
            title=app.title,
            version="0.1.0",
            routes=app.routes,
        )
    except PydanticSchemaGenerationError:
        app.openapi_schema = {
            "openapi": "3.1.0",
            "info": {"title": app.title, "version": "0.1.0"},
            "paths": {},
        }
    return app.openapi_schema


app.openapi = _safe_openapi


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/chat")
async def chat(request: ChatRequest):
    run_id = str(uuid.uuid4())

    log_event(run_id, request.session_id, "request_received", message=request.message)

    final_answer = await run_adk_orchestrator(
        request.message,
        request.session_id,
        search_client=search_client,
    )

    log_event(run_id, request.session_id, "response_ready", framework="adk")
    return {
        "run_id": run_id,
        "session_id": request.session_id,
        "final_answer": final_answer,
        "agents_used": [],
        "tools_used": [],
        "citations": [],
        "errors": [],
    }

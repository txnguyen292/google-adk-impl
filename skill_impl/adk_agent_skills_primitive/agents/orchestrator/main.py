from __future__ import annotations

import asyncio
import os

import typer
from loguru import logger
from rich.console import Console

from core.utils.dotenv import load_dotenv
from adk_agent_skills_primitive.agents.orchestrator.agent import (
    app as adk_primitive_app,
)
from adk_agent.utils.runner_utils import collect_final_response

console = Console()
app = typer.Typer(add_completion=False)


async def _run_local(message: str) -> str:
    from google.adk.runners import Runner
    from google.adk.agents.run_config import RunConfig
    from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
    from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from core.utils.adk_config import get_max_llm_calls

    session_service = InMemorySessionService()
    session_id = "local-session"
    user_id = "local-user"
    await session_service.create_session(
        app_name=adk_primitive_app.name,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(
        app=adk_primitive_app,
        app_name=adk_primitive_app.name,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )
    max_llm_calls = get_max_llm_calls()
    run_config = RunConfig(max_llm_calls=max_llm_calls)
    debug = os.getenv("ADK_DEBUG", "").strip().lower() in {"1", "true", "yes", "y"}
    trace = os.getenv("ADK_TRACE", "").strip().lower() in {"1", "true", "yes", "y"}
    logger.info("ADK primitive local run config: max_llm_calls={}", max_llm_calls)
    try:
        return await collect_final_response(
            runner=runner,
            user_id=user_id,
            session_id=session_id,
            message=message,
            run_config=run_config,
            final_author=adk_primitive_app.name,
            debug=debug or trace,
            trace=trace,
        )
    finally:
        await runner.close()


def _read_message(message: str | None) -> str:
    if message:
        return message
    return console.input("message: ")


@app.command()
def run(message: str | None = typer.Argument(None, help="Message to send.")) -> None:
    load_dotenv()
    logger.info("Running ADK primitive skills orchestrator locally")
    try:
        output = asyncio.run(_run_local(_read_message(message)))
    except Exception:
        logger.exception("ADK primitive skills orchestrator run failed")
        raise typer.Exit(1)
    console.print(output)


if __name__ == "__main__":
    app()

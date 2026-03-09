from __future__ import annotations

import asyncio

import typer
from loguru import logger
from rich.console import Console

from core.utils.dotenv import load_dotenv
from adk_agent.agents.multi_agent.math_agent.agent import app as adk_app

console = Console()
app = typer.Typer(add_completion=False)


async def _run_local(message: str) -> str:
    from google.adk.runners import Runner
    from google.adk.agents.run_config import RunConfig
    from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
    from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.genai import types
    from core.utils.adk_config import get_max_llm_calls

    session_service = InMemorySessionService()
    session_id = "local-session"
    user_id = "local-user"
    await session_service.create_session(
        app_name=adk_app.name,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(
        app=adk_app,
        app_name=adk_app.name,
        session_service=session_service,
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )
    run_config = RunConfig(max_llm_calls=get_max_llm_calls())
    content = types.Content(role="user", parts=[types.Part(text=message)])
    final_text = "No response."
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
            run_config=run_config,
        ):
            if event.is_final_response():
                final_text = event.content.parts[0].text
                break
    finally:
        await runner.close()
    return final_text


def _read_message(message: str | None) -> str:
    if message:
        return message
    return console.input("message: ")


@app.command()
def run(message: str | None = typer.Argument(None, help="Message to send.")) -> None:
    load_dotenv()
    logger.info("Running ADK math_agent locally")
    try:
        output = asyncio.run(_run_local(_read_message(message)))
    except Exception:
        logger.exception("ADK math_agent run failed")
        raise typer.Exit(1)
    console.print(output)


if __name__ == "__main__":
    app()

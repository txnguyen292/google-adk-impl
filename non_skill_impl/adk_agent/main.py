from __future__ import annotations

import typer
from loguru import logger
from rich.console import Console

from core.utils.dotenv import load_dotenv
from adk_agent.cli import main as cli_main

console = Console()
app = typer.Typer(add_completion=False)


@app.command()
def run() -> None:
    load_dotenv()
    logger.info("Starting ADK FastAPI server")
    try:
        cli_main()
    except Exception:
        logger.exception("ADK server failed to start")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()

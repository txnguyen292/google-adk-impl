import json
import logging
import time
from typing import Any

LOGGER_NAME = "langgraph_vs_adk"


def _get_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def log_event(run_id: str, session_id: str, event: str, **fields: Any) -> None:
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": run_id,
        "session_id": session_id,
        "event": event,
        **fields,
    }
    logger = _get_logger()
    logger.info(json.dumps(payload, ensure_ascii=True))

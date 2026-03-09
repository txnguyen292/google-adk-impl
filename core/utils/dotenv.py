from __future__ import annotations

from pathlib import Path
import os
from typing import Iterable


def _find_dotenv(start: Path) -> Path | None:
    for parent in (start, *start.parents):
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
    return None


def _parse_env_lines(lines: Iterable[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"").strip("'")
        if key:
            values[key] = value
    return values


def load_dotenv(path: str | None = None, override: bool = False) -> Path | None:
    """Load .env into os.environ. Returns the path if loaded."""
    try:
        from dotenv import load_dotenv as _load
    except Exception:
        _load = None

    if path:
        dotenv_path = Path(path)
    else:
        dotenv_path = _find_dotenv(Path.cwd())

    if not dotenv_path or not dotenv_path.is_file():
        return None

    if _load:
        _load(dotenv_path=dotenv_path, override=override)
        return dotenv_path

    values = _parse_env_lines(dotenv_path.read_text(encoding="utf-8").splitlines())
    for key, value in values.items():
        if not override and key in os.environ:
            continue
        os.environ[key] = value
    return dotenv_path

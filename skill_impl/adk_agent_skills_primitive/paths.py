from __future__ import annotations

from pathlib import Path

_SKILL_DIRS = {
    "math": "math",
    "web_search": "web-search",
}


def native_skills_root() -> Path:
    return Path(__file__).resolve().parent / "native_skills"


def get_native_skill_dir(skill_key: str) -> Path:
    skill_dir_name = _SKILL_DIRS[skill_key]
    return native_skills_root() / skill_dir_name

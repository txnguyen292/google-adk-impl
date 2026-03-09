from __future__ import annotations

from pathlib import Path
import re

_INCLUDE_RE = re.compile(r"\{\{\s*include:([^}]+)\}\}")


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "non_skill_impl" / "adk_agent" / "skills").is_dir():
            return parent
    raise FileNotFoundError("skills directory not found")


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"Skill file not found: {path}")
    return path.read_text(encoding="utf-8")


def _resolve_include(repo_root: Path, target: str) -> Path:
    target = target.strip()
    if not target:
        raise FileNotFoundError("Empty include target")
    if target.endswith(".md") or "/" in target:
        return (repo_root / target).resolve()
    return (
        repo_root / "non_skill_impl" / "adk_agent" / "skills" / target / "skill.md"
    ).resolve()


def _expand_includes(repo_root: Path, text: str, seen: set[str]) -> str:
    def _replace(match: re.Match) -> str:
        target = match.group(1).strip()
        key = target
        if key in seen:
            return ""
        seen.add(key)
        path = _resolve_include(repo_root, target)
        included = _read_text(path)
        return _expand_includes(repo_root, included, seen)

    return _INCLUDE_RE.sub(_replace, text)


def load_skill_prompt(skill_name: str) -> str:
    repo_root = _find_repo_root()
    skill_path = repo_root / "non_skill_impl" / "adk_agent" / "skills" / skill_name / "skill.md"
    raw = _read_text(skill_path)
    expanded = _expand_includes(repo_root, raw, seen=set())
    return expanded.strip()


def load_orchestrator_prompt() -> str:
    base = load_skill_prompt("orchestrator")
    math_prompt = load_skill_prompt("math")
    web_prompt = load_skill_prompt("web_search")
    return (
        f"{base}\n\n"
        "Sub-agent prompts:\n"
        "[math_agent]\n"
        f"{math_prompt}\n\n"
        "[web_search_agent]\n"
        f"{web_prompt}"
    ).strip()

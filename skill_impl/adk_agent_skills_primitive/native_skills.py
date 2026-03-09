from __future__ import annotations

from google.adk.skills import Skill, load_skill_from_dir

from adk_agent_skills_primitive.paths import get_native_skill_dir
from adk_agent_skills_primitive.toolsets import ActivatingSkillToolset

def load_native_skill(skill_key: str) -> Skill:
    return load_skill_from_dir(get_native_skill_dir(skill_key))


def load_native_skills(skill_keys: tuple[str, ...] | None = None) -> list[Skill]:
    keys = skill_keys or ("math", "web_search")
    return [load_native_skill(key) for key in keys]


def build_native_skill_toolset(
    skill_keys: tuple[str, ...] | None = None,
) -> ActivatingSkillToolset:
    return ActivatingSkillToolset(skills=load_native_skills(skill_keys))


__all__ = [
    "build_native_skill_toolset",
    "get_native_skill_dir",
    "load_native_skill",
    "load_native_skills",
]

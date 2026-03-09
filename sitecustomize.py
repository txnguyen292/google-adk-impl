from __future__ import annotations

import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

for package_root in (REPO_ROOT / "skill_impl", REPO_ROOT / "non_skill_impl"):
    package_root_str = str(package_root)
    if package_root_str not in sys.path:
        sys.path.insert(0, package_root_str)

adk_fix = importlib.import_module("adk_agent.adk_fix")

adk_fix.silence_pydantic_pedantry()

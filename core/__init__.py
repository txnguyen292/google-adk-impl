from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Set


@dataclass
class RunContext:
    run_id: str
    session_id: str
    agents_used: Set[str] = field(default_factory=set)
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    citations: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    enabled: bool | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.enabled is None:
            self.enabled = _parse_bool_env("RUN_CONTEXT_ENABLED", default=False)

    def record_agent(self, name: str) -> None:
        if not self.enabled:
            return
        self.agents_used.add(name)

    def record_tool(self, agent: str, tool: str, args: Dict[str, Any]) -> None:
        if not self.enabled:
            return
        self.tools_used.append({"agent": agent, "tool": tool, "args": args})

    def record_citations(self, citations: List[Dict[str, str]]) -> None:
        if not self.enabled:
            return
        self.citations.extend(citations)

    def record_error(self, message: str) -> None:
        if not self.enabled:
            return
        self.errors.append(message)

    def to_response(self, final_answer: str) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "final_answer": final_answer,
            "agents_used": sorted(self.agents_used),
            "tools_used": self.tools_used,
            "citations": self.citations,
            "errors": self.errors,
        }


def _parse_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}

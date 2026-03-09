from __future__ import annotations

import asyncio
from types import SimpleNamespace

from non_skill_impl.adk_agent.utils.runner_utils import collect_final_response


class _FakeEvent:
    def __init__(
        self,
        *,
        author: str = "orchestrator",
        is_final: bool = False,
        text: str = "",
        responses: list[object] | None = None,
    ) -> None:
        self.author = author
        self.partial = False
        self.invocation_id = "inv"
        self.content = SimpleNamespace(parts=[SimpleNamespace(text=text)])
        self._is_final = is_final
        self._responses = responses or []

    def get_function_calls(self):
        return []

    def get_function_responses(self):
        return self._responses

    def is_final_response(self):
        return self._is_final


class _FakeRunner:
    def __init__(self, events: list[_FakeEvent]) -> None:
        self._events = events

    async def run_async(self, **_: object):
        for event in self._events:
            yield event


def test_collect_final_response_prefers_format_math_response_final_answer():
    format_response = SimpleNamespace(
        name="format_math_response",
        response={
            "status": "success",
            "final_answer": "Differential equation:\ndy/dx = x·y\n\nSolution:\ny(x) = C₁·exp(x²/2)",
        },
    )
    runner = _FakeRunner(
        [
            _FakeEvent(responses=[format_response]),
            _FakeEvent(
                is_final=True,
                text="## Final solution\n\\[y(x)=C_1 e^{x^2/2}\\]",
            ),
        ]
    )

    final_text = asyncio.run(
        collect_final_response(
            runner=runner,
            user_id="u",
            session_id="s",
            message="solve this",
            run_config=object(),
            final_author="orchestrator",
        )
    )

    assert final_text == format_response.response["final_answer"]

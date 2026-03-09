from __future__ import annotations

from typing import Any


async def collect_final_response(
    *,
    runner: Any,
    user_id: str,
    session_id: str,
    message: str,
    run_config: Any,
    final_author: str | None = None,
    debug: bool = False,
    trace: bool = False,
) -> str:
    """Run the ADK runner and return the final response text."""
    from google.genai import types
    from core.utils.math_render import render_math_for_terminal

    log_event = None
    if debug:
        from core.utils.observability import log_event as _log_event

        log_event = _log_event

    content = types.Content(role="user", parts=[types.Part(text=message)])
    final_text = "No response."
    preferred_final_text: str | None = None

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
        run_config=run_config,
    ):
        if debug or trace:
            try:
                calls = event.get_function_calls()
                responses = event.get_function_responses()
                if log_event:
                    log_event(
                        "adk",
                        session_id,
                        "adk_event",
                        author=event.author,
                        invocation_id=event.invocation_id,
                        is_final=event.is_final_response(),
                        partial=event.partial,
                        function_calls=[c.name for c in calls],
                        function_responses=[r.name for r in responses],
                    )
                if trace:
                    author = event.author or "unknown"
                    if calls:
                        print(f"[adk:{author}] function_calls: {', '.join(c.name for c in calls)}")
                    if responses:
                        print(
                            f"[adk:{author}] function_responses: "
                            f"{', '.join(r.name for r in responses)}"
                        )
                    if (
                        event.content
                        and event.content.parts
                        and getattr(event.content.parts[0], "text", None)
                    ):
                        text = event.content.parts[0].text.strip()
                        if text:
                            print(f"[adk:{author}] text: {render_math_for_terminal(text)}")
            except Exception:
                pass

        try:
            responses = event.get_function_responses()
            for response in responses:
                if response.name != "format_math_response":
                    continue
                payload = getattr(response, "response", None)
                if not isinstance(payload, dict):
                    continue
                candidate = payload.get("final_answer")
                if isinstance(candidate, str) and candidate.strip():
                    preferred_final_text = candidate.strip()
        except Exception:
            pass

        if event.is_final_response() and (
            final_author is None or event.author == final_author
        ):
            if preferred_final_text:
                final_text = render_math_for_terminal(preferred_final_text)
            else:
                final_text = render_math_for_terminal(event.content.parts[0].text)
            break

    return final_text

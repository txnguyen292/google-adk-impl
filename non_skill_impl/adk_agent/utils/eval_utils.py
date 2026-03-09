from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _content_to_text(content: dict[str, Any] | None) -> str:
    if not content:
        return ""
    parts = content.get("parts") or []
    texts: list[str] = []
    for part in parts:
        text = part.get("text")
        if text:
            texts.append(text)
    return "\n".join(texts)


def _tool_calls_to_text(intermediate_data: dict[str, Any] | None) -> str:
    if not intermediate_data:
        return ""
    events = intermediate_data.get("invocation_events") or []
    lines: list[str] = []
    for event in events:
        content = event.get("content") or {}
        parts = content.get("parts") or []
        for part in parts:
            call = part.get("function_call")
            if call:
                name = call.get("name")
                args = call.get("args")
                lines.append(f"call:{name} args={args}")
            response = part.get("function_response")
            if response:
                name = response.get("name")
                payload = response.get("response")
                lines.append(f"response:{name} response={payload}")
    return "\n".join(lines)


def _rubric_id(rubric: dict[str, Any]) -> str | None:
    return rubric.get("rubric_id") or rubric.get("rubricId") or rubric.get("id")


def _rubric_text(rubric: dict[str, Any]) -> str | None:
    content = rubric.get("rubric_content") or rubric.get("rubricContent") or {}
    if isinstance(content, dict):
        return content.get("text_property") or content.get("textProperty")
    return None


def export_eval_to_excel(input_path: Path, output_path: Path) -> Path | None:
    """Export ADK evalset_result JSON to an Excel workbook (or CSV fallback)."""
    with input_path.open() as f:
        payload = json.load(f)

    eval_case_results = payload.get("eval_case_results") or []
    summary_rows: list[dict[str, Any]] = []
    invocation_rows: list[dict[str, Any]] = []
    rubric_rows: list[dict[str, Any]] = []
    status_map = {1: "PASSED", 2: "FAILED", 3: "NOT_EVALUATED"}

    for case in eval_case_results:
        eval_id = case.get("eval_id")
        eval_set_id = case.get("eval_set_id")
        final_status = case.get("final_eval_status")

        for metric in case.get("overall_eval_metric_results") or []:
            summary_rows.append(
                {
                    "eval_set_id": eval_set_id,
                    "eval_id": eval_id,
                    "final_eval_status": status_map.get(final_status, final_status),
                    "metric_name": metric.get("metric_name"),
                    "score": metric.get("score"),
                    "threshold": metric.get("threshold"),
                    "eval_status": status_map.get(
                        metric.get("eval_status"), metric.get("eval_status")
                    ),
                }
            )

        per_inv = case.get("eval_metric_result_per_invocation") or []
        for idx, inv in enumerate(per_inv):
            actual = inv.get("actual_invocation") or {}
            expected = inv.get("expected_invocation") or {}
            row = {
                "eval_set_id": eval_set_id,
                "eval_id": eval_id,
                "invocation_index": idx,
                "prompt": _content_to_text(actual.get("user_content")),
                "expected_response": _content_to_text(
                    expected.get("final_response")
                ),
                "actual_response": _content_to_text(actual.get("final_response")),
                "expected_tool_calls": _tool_calls_to_text(
                    expected.get("intermediate_data")
                ),
                "actual_tool_calls": _tool_calls_to_text(
                    actual.get("intermediate_data")
                ),
            }

            for metric in inv.get("eval_metric_results") or []:
                metric_name = metric.get("metric_name")
                row[f"{metric_name}_score"] = metric.get("score")
                row[f"{metric_name}_status"] = status_map.get(
                    metric.get("eval_status"), metric.get("eval_status")
                )

                rubrics = (
                    (metric.get("criterion") or {}).get("rubrics") or []
                )
                rubric_text_map = {}
                for rubric in rubrics:
                    if isinstance(rubric, dict):
                        rid = _rubric_id(rubric)
                        if rid:
                            rubric_text_map[rid] = _rubric_text(rubric)

                for rubric_score in (
                    (metric.get("details") or {}).get("rubric_scores") or []
                ):
                    rid = rubric_score.get("rubric_id") or rubric_score.get(
                        "rubricId"
                    )
                    rubric_rows.append(
                        {
                            "eval_set_id": eval_set_id,
                            "eval_id": eval_id,
                            "invocation_index": idx,
                            "metric_name": metric_name,
                            "rubric_id": rid,
                            "rubric_text": rubric_text_map.get(rid),
                            "score": rubric_score.get("score"),
                            "rationale": rubric_score.get("rationale"),
                        }
                    )

            invocation_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    inv_df = pd.DataFrame(invocation_rows)
    rubric_df = pd.DataFrame(rubric_rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import openpyxl  # noqa: F401
    except ModuleNotFoundError:
        base = output_path.with_suffix("")
        summary_csv = base.with_name(base.name + "_summary.csv")
        inv_csv = base.with_name(base.name + "_invocations.csv")
        rubric_csv = base.with_name(base.name + "_rubrics.csv")
        summary_df.to_csv(summary_csv, index=False)
        inv_df.to_csv(inv_csv, index=False)
        rubric_df.to_csv(rubric_csv, index=False)
        print(
            "openpyxl is not installed. Wrote CSVs instead:\n"
            f"- {summary_csv}\n- {inv_csv}\n- {rubric_csv}"
        )
        return None

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        inv_df.to_excel(writer, sheet_name="invocations", index=False)
        rubric_df.to_excel(writer, sheet_name="rubrics", index=False)
    return output_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Export ADK evalset_result JSON to an Excel workbook."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()

    output = args.output
    if output is None:
        output = args.input.with_suffix(".xlsx")
    result = export_eval_to_excel(args.input, output)
    if result is not None:
        print(str(result))


if __name__ == "__main__":
    main()

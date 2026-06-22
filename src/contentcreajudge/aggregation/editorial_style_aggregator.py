"""Minimal aggregation layer for the editorial style evaluation flow."""

from __future__ import annotations


def aggregate_editorial_style_result(
    judge_result: dict[str, object],
) -> dict[str, object]:
    """Aggregate the result of the editorial style judge."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = int(judge_result.get("score", 0))

    findings = judge_result.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the editorial style dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": judge_status,
        "score": judge_score,
        "summary": "Global evaluation did not pass for the editorial style dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

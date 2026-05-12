"""Minimal aggregation layer for the length evaluation flow."""

from __future__ import annotations


def aggregate_length_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summary of the overall result of judge length."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = int(judge_result.get("score", 0))

    findings = judge_result.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the length dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": judge_score,
        "summary": "Global evaluation failed for the length dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

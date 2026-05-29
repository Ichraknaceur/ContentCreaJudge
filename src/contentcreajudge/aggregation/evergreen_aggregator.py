"""Aggregation layer for the evergreen evaluation flow."""

from __future__ import annotations


def aggregate_evergreen_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Aggregate the evergreen judge result safely."""
    judge_status = str(judge_result.get("status", "fail"))
    judge_score = int(judge_result.get("score", 0) or 0)
    findings = judge_result.get("findings", [])

    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the evergreen dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Global evaluation has warnings for the evergreen dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": judge_score,
        "summary": "Global evaluation failed for the evergreen dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

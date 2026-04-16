"""Minimal aggregation layer for the typography evaluation flow."""

from __future__ import annotations


def aggregate_typography_result(
    judge_result: dict[str, object],
) -> dict[str, object]:
    """Summary of the overall result of the typography judge."""

    judge_status = str(judge_result["status"])
    judge_score = int(judge_result["score"])
    findings = list(judge_result.get("findings", []))

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": 100,
            "summary": "Global evaluation passed for the typography dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Typography evaluation completed with minor issues.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    # fail
    return {
        "status": "fail",
        "score": judge_score,
        "summary": "Typography evaluation failed due to major issues.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }
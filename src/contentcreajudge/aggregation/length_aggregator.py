"""Minimal aggregation layer for the length evaluation flow."""

from __future__ import annotations


def aggregate_length_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summary of the overall result of judge length"""

    judge_status = str(judge_result["status"])

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": 100,
            "summary": "Global evaluation passed for the length dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": 0,
        "summary": "Global evaluation failed for the length dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": judge_result["findings"],
    }
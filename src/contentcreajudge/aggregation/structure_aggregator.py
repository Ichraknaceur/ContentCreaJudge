"""Minimal aggregation layer for the structure evaluation flow."""

from __future__ import annotations

from typing import Any


def aggregate_structure_result(
    judge_result: dict[str, Any],
) -> dict[str, Any]:
    """Build a minimal aggregated result for the structure dimension."""
    judge_status = str(judge_result["status"])

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": 100,
            "summary": "Global evaluation passed for the structure dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": 0,
        "summary": "Global evaluation failed for the structure dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": judge_result["findings"],
    }
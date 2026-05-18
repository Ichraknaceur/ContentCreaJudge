"""Minimal aggregation layer for the structure evaluation flow."""

from __future__ import annotations

from typing import Any


def aggregate_structure_result(
    judge_result: dict[str, Any],
) -> dict[str, Any]:
    """Build a minimal aggregated result for the structure dimension."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = int(judge_result.get("score", 0))

    findings = judge_result.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the structure dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": judge_score,
        "summary": "Global evaluation failed for the structure dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

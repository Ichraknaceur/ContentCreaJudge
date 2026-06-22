"""Minimal aggregation layer for the Brief evaluation flow."""

from __future__ import annotations


def aggregate_brief_result(
    judge_result: dict[str, object],
) -> dict[str, object]:
    """Summarize the overall result of the Brief judge."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = judge_result.get("score")
    findings = judge_result.get("findings") or []

    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the brief dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Global evaluation returned warnings for the brief dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "fail":
        return {
            "status": "fail",
            "score": judge_score,
            "summary": "Global evaluation failed for the brief dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": findings,
        }

    return {
        "status": "unknown",
        "score": judge_score,
        "summary": "Global evaluation could not be completed for the brief dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

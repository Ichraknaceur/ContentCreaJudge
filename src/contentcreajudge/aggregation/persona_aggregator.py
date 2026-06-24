"""Minimal aggregation layer for the persona evaluation flow."""

from __future__ import annotations


def aggregate_persona_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summarize the overall result of the persona judge."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = int(judge_result.get("score", 0) or 0)
    findings = judge_result.get("findings", [])

    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the persona dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Global evaluation raised warnings for the persona dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "fail":
        return {
            "status": "fail",
            "score": judge_score,
            "summary": "Global evaluation failed for the persona dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": findings,
        }

    return {
        "status": "unknown",
        "score": judge_score,
        "summary": (
            "Global evaluation could not reliably complete for the persona dimension."
        ),
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

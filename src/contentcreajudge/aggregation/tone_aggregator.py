"""Minimal aggregation layer for the tone evaluation flow."""

from __future__ import annotations


def aggregate_tone_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summarize the overall result of the tone judge."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = int(judge_result.get("score", 0) or 0)
    findings = judge_result.get("findings", [])

    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the tone dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Global evaluation raised warnings for the tone dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "fail":
        return {
            "status": "fail",
            "score": judge_score,
            "summary": "Global evaluation failed for the tone dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": findings,
        }

    return {
        "status": "unknown",
        "score": judge_score,
        "summary": (
            "Global evaluation could not reliably complete for the tone dimension."
        ),
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

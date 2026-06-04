"""Minimal aggregation layer for the funnel evaluation flow."""

from __future__ import annotations


def _safe_score(value: object) -> int | None:
    """Return a valid score or None when unavailable."""
    if value is None:
        return None

    try:
        score = int(value)
    except TypeError, ValueError:
        return None

    return max(0, min(100, score))


def aggregate_funnel_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summarize the overall result of the funnel judge."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = _safe_score(judge_result.get("score"))
    findings = judge_result.get("findings", [])

    if not isinstance(findings, list):
        findings = []

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the funnel dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Global evaluation raised warnings for the funnel dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warning":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Global evaluation raised warnings for the funnel dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "fail":
        return {
            "status": "fail",
            "score": judge_score,
            "summary": "Global evaluation failed for the funnel dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": findings,
        }

    return {
        "status": "unknown",
        "score": judge_score,
        "summary": (
            "Global evaluation could not reliably complete for the funnel dimension."
        ),
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

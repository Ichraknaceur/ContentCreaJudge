"""Minimal aggregation layer for the CTA evaluation flow."""

from __future__ import annotations


def aggregate_cta_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summarize the overall result of the CTA judge."""

    judge_status = str(judge_result["status"])
    judge_score = int(judge_result["score"])
    findings = judge_result.get("findings", [])

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the CTA dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "not_applicable":
        return {
            "status": "not_applicable",
            "score": judge_score,
            "summary": "CTA evaluation is not applicable for this content.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": "Global evaluation has warnings for the CTA dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": judge_score,
        "summary": "Global evaluation failed for the CTA dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }
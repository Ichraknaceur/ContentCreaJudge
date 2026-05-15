"""Minimal aggregation layer for the SEO evaluation flow."""

from __future__ import annotations


def aggregate_seo_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summarize the overall result of the SEO judge."""
    judge_status = str(judge_result.get("status", "unknown"))
    judge_score = int(judge_result.get("score", 0))
    findings = list(judge_result.get("findings", []))

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the SEO dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": (
                "Global evaluation completed with warnings for the SEO dimension."
            ),
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": judge_score,
        "summary": "Global evaluation failed for the SEO dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

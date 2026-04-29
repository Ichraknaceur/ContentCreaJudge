"""Minimal aggregation layer for the evergreen evaluation flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contentcreajudge.judges.evergreen.evergreen_judge import (
        EvergreenJudgeResult,
    )


def aggregate_evergreen_result(
    judge_result: EvergreenJudgeResult,
) -> dict[str, object]:
    """Summarize the overall result of the evergreen judge."""
    judge_status = judge_result.get("status", "warn")
    judge_score = judge_result.get("score", 0)
    findings = judge_result.get("findings", [])

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": judge_score,
            "summary": "Global evaluation passed for the evergreen dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": judge_score,
            "summary": (
                "Global evaluation returned warnings for the evergreen dimension."
            ),
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": judge_score,
        "summary": "Global evaluation failed for the evergreen dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": findings,
    }

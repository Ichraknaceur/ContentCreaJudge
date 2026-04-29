"""Minimal aggregation layer for the sources evaluation flow."""

from __future__ import annotations


def aggregate_sources_result(judge_result: dict[str, object]) -> dict[str, object]:
    """Summarize the overall result of the sources judge."""

    judge_status = str(judge_result["status"])
    findings = judge_result.get("findings", [])

    if not isinstance(findings, list):
        findings = []

    major_findings = [
        finding
        for finding in findings
        if isinstance(finding, dict) and finding.get("severity") == "major"
    ]

    if judge_status == "pass":
        return {
            "status": "pass",
            "score": 100,
            "summary": "Global evaluation passed for the sources dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    if judge_status == "warn":
        return {
            "status": "warn",
            "score": int(judge_result["score"]),
            "summary": "Global evaluation has warnings for the sources dimension.",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        }

    return {
        "status": "fail",
        "score": 0,
        "summary": "Global evaluation failed for the sources dimension.",
        "dimension_results": [judge_result],
        "blocking_issues": major_findings,
    }
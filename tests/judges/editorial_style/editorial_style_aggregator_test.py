"""Tests for the editorial style aggregator."""

from __future__ import annotations

from contentcreajudge.aggregation.editorial_style_aggregator import (
    aggregate_editorial_style_result,
)


def test_aggregate_editorial_style_result_pass() -> None:
    """It should return pass aggregation when judge passes."""
    judge_result = {
        "dimension": "editorial_style",
        "status": "pass",
        "score": 86,
        "findings": [],
    }

    result = aggregate_editorial_style_result(judge_result)

    assert result["status"] == "pass"
    assert result["score"] == 86
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == []


def test_aggregate_editorial_style_result_warn() -> None:
    """It should return findings when judge warns."""
    findings = [
        {
            "provider": "openai",
            "rule_id": "editorial_style.expression_control",
            "severity": "major",
            "message": "Expression trop emphatique.",
            "evidence": "Une révolution incroyable.",
        }
    ]

    judge_result = {
        "dimension": "editorial_style",
        "status": "warn",
        "score": 72,
        "findings": findings,
    }

    result = aggregate_editorial_style_result(judge_result)

    assert result["status"] == "warn"
    assert result["score"] == 72
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == findings


def test_aggregate_editorial_style_result_fail() -> None:
    """It should return findings when judge fails."""
    findings = [
        {
            "provider": "mistral",
            "rule_id": "editorial_style.style_alignment",
            "severity": "critical",
            "message": "Posture incompatible.",
            "evidence": "Salut à tous !",
        }
    ]

    judge_result = {
        "dimension": "editorial_style",
        "status": "fail",
        "score": 35,
        "findings": findings,
    }

    result = aggregate_editorial_style_result(judge_result)

    assert result["status"] == "fail"
    assert result["score"] == 35
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == findings

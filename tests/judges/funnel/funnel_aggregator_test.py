"""Tests for the funnel aggregation layer."""

from __future__ import annotations

from contentcreajudge.aggregation.funnel_aggregator import (
    _safe_score,
    aggregate_funnel_result,
)


def test_safe_score_returns_none_for_none() -> None:
    assert _safe_score(None) is None


def test_safe_score_returns_none_for_invalid_value() -> None:
    assert _safe_score("not-a-score") is None


def test_safe_score_clamps_score_to_minimum() -> None:
    assert _safe_score(-10) == 0


def test_safe_score_clamps_score_to_maximum() -> None:
    assert _safe_score(150) == 100


def test_safe_score_returns_valid_score() -> None:
    assert _safe_score("82") == 82


def test_aggregate_funnel_result_pass() -> None:
    judge_result = {
        "dimension": "funnel",
        "status": "pass",
        "score": 92,
        "findings": [{"criterion": "pedagogie"}],
    }

    result = aggregate_funnel_result(judge_result)

    assert result["status"] == "pass"
    assert result["score"] == 92
    assert result["summary"] == "Global evaluation passed for the funnel dimension."
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == []


def test_aggregate_funnel_result_warn() -> None:
    judge_result = {
        "dimension": "funnel",
        "status": "warn",
        "score": 72,
        "findings": [{"criterion": "purete_funnel_awareness"}],
    }

    result = aggregate_funnel_result(judge_result)

    assert result["status"] == "warn"
    assert result["score"] == 72
    assert result["summary"] == (
        "Global evaluation raised warnings for the funnel dimension."
    )
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == []


def test_aggregate_funnel_result_warning_is_normalized_to_warn() -> None:
    judge_result = {
        "dimension": "funnel",
        "status": "warning",
        "score": 72,
        "findings": [{"criterion": "purete_funnel_awareness"}],
    }

    result = aggregate_funnel_result(judge_result)

    assert result["status"] == "warn"
    assert result["score"] == 72
    assert result["blocking_issues"] == []


def test_aggregate_funnel_result_fail() -> None:
    findings = [{"criterion": "absence_argumentaire_commercial"}]
    judge_result = {
        "dimension": "funnel",
        "status": "fail",
        "score": 45,
        "findings": findings,
    }

    result = aggregate_funnel_result(judge_result)

    assert result["status"] == "fail"
    assert result["score"] == 45
    assert result["summary"] == "Global evaluation failed for the funnel dimension."
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == findings


def test_aggregate_funnel_result_unknown_status() -> None:
    findings = [{"criterion": "unknown"}]
    judge_result = {
        "dimension": "funnel",
        "status": "unexpected",
        "score": "invalid",
        "findings": findings,
    }

    result = aggregate_funnel_result(judge_result)

    assert result["status"] == "unknown"
    assert result["score"] is None
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == findings


def test_aggregate_funnel_result_non_list_findings() -> None:
    judge_result = {
        "dimension": "funnel",
        "status": "fail",
        "score": 40,
        "findings": "invalid",
    }

    result = aggregate_funnel_result(judge_result)

    assert result["status"] == "fail"
    assert result["blocking_issues"] == []

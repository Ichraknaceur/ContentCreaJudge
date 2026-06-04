from __future__ import annotations

from contentcreajudge.aggregation.tone_aggregator import aggregate_tone_result


def test_aggregate_tone_result_pass() -> None:
    judge_result = {
        "dimension": "tone",
        "status": "pass",
        "score": 90,
        "findings": [],
    }

    result = aggregate_tone_result(judge_result)

    assert result["status"] == "pass"
    assert result["score"] == 90
    assert result["blocking_issues"] == []
    assert result["dimension_results"] == [judge_result]


def test_aggregate_tone_result_warn() -> None:
    judge_result = {
        "dimension": "tone",
        "status": "warn",
        "score": 72,
        "findings": [
            {
                "rule_id": "tone.natural_expression",
                "severity": "minor",
                "message": "Some mechanical wording was detected.",
            }
        ],
    }

    result = aggregate_tone_result(judge_result)

    assert result["status"] == "warn"
    assert result["score"] == 72
    assert result["blocking_issues"] == []


def test_aggregate_tone_result_fail() -> None:
    findings = [
        {
            "rule_id": "tone.contextual_alignment",
            "severity": "major",
            "message": "Tone is not contextually aligned.",
        }
    ]

    judge_result = {
        "dimension": "tone",
        "status": "fail",
        "score": 45,
        "findings": findings,
    }

    result = aggregate_tone_result(judge_result)

    assert result["status"] == "fail"
    assert result["score"] == 45
    assert result["blocking_issues"] == findings


def test_aggregate_tone_result_unknown_when_status_missing() -> None:
    judge_result = {
        "dimension": "tone",
        "score": 0,
    }

    result = aggregate_tone_result(judge_result)

    assert result["status"] == "unknown"
    assert result["score"] == 0
    assert result["blocking_issues"] == []


def test_aggregate_tone_result_handles_invalid_findings() -> None:
    judge_result = {
        "dimension": "tone",
        "status": "fail",
        "score": 30,
        "findings": "invalid",
    }

    result = aggregate_tone_result(judge_result)

    assert result["status"] == "fail"
    assert result["blocking_issues"] == []

from contentcreajudge.aggregation.evergreen_aggregator import (
    aggregate_evergreen_result,
)


def _judge_result(status: str, score: int = 80) -> dict[str, object]:
    return {
        "dimension": "evergreen",
        "status": status,
        "score": score,
        "findings": [
            {
                "rule_id": "evergreen.llm.problematic_passage",
                "severity": "forte",
                "message": "Information datée.",
            },
        ],
    }


def test_aggregate_evergreen_result_pass() -> None:
    judge_result = _judge_result("pass", 85)

    result = aggregate_evergreen_result(judge_result)

    assert result["status"] == "pass"
    assert result["score"] == 85
    assert result["summary"] == "Global evaluation passed for the evergreen dimension."
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == []


def test_aggregate_evergreen_result_warn() -> None:
    judge_result = _judge_result("warn", 60)

    result = aggregate_evergreen_result(judge_result)

    assert result["status"] == "warn"
    assert result["score"] == 60
    assert result["summary"] == (
        "Global evaluation has warnings for the evergreen dimension."
    )
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == []


def test_aggregate_evergreen_result_fail_uses_findings_as_blocking_issues() -> None:
    judge_result = _judge_result("fail", 30)

    result = aggregate_evergreen_result(judge_result)

    assert result["status"] == "fail"
    assert result["score"] == 30
    assert result["summary"] == "Global evaluation failed for the evergreen dimension."
    assert result["dimension_results"] == [judge_result]
    assert result["blocking_issues"] == judge_result["findings"]


def test_aggregate_evergreen_result_ignores_non_list_findings() -> None:
    judge_result = {
        "dimension": "evergreen",
        "status": "fail",
        "score": 0,
        "findings": "invalid",
    }

    result = aggregate_evergreen_result(judge_result)

    assert result["status"] == "fail"
    assert result["blocking_issues"] == []

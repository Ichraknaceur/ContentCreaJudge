"""Tests for the Brief evaluation flow."""

from __future__ import annotations

from contentcreajudge.application.judge_flow import brief_flow


def test_execute_brief_flow_returns_expected_sections(
    monkeypatch,
) -> None:
    def fake_run_brief_judge(
        preprocessed_content: dict[str, object],
        judge_rules: dict[str, object],
    ) -> dict[str, object]:
        return {
            "dimension": "brief",
            "status": "pass",
            "score": 90,
            "confidence": 85,
            "findings": [],
        }

    monkeypatch.setattr(
        brief_flow,
        "run_brief_judge",
        fake_run_brief_judge,
    )

    payload = {
        "content": "<p>Article test</p>",
        "profile": "default",
        "context": {
            "brief": "Angle et message central : test",
        },
        "request_id": "test-1",
    }

    result = brief_flow.execute_brief_flow(payload)

    assert "request_echo" in result
    assert "rule_resolution" in result
    assert "preprocessing" in result
    assert "judge_result" in result
    assert "aggregation" in result


def test_execute_brief_flow_preprocesses_article_and_brief(
    monkeypatch,
) -> None:
    def fake_run_brief_judge(
        preprocessed_content: dict[str, object],
        judge_rules: dict[str, object],
    ) -> dict[str, object]:
        assert preprocessed_content["article_text"] == "Article test"
        assert (
            preprocessed_content["normalized_brief"]
            == "Angle et message central : test"
        )

        return {
            "dimension": "brief",
            "status": "pass",
            "score": 90,
            "confidence": 85,
            "findings": [],
        }

    monkeypatch.setattr(
        brief_flow,
        "run_brief_judge",
        fake_run_brief_judge,
    )

    payload = {
        "content": "<p>Article test</p>",
        "context": {
            "brief": "Angle et message central : test",
        },
    }

    result = brief_flow.execute_brief_flow(payload)

    assert result["preprocessing"]["article_text"] == "Article test"
    assert result["preprocessing"]["is_article_empty"] is False
    assert result["preprocessing"]["is_brief_empty"] is False


def test_execute_brief_flow_handles_missing_context(
    monkeypatch,
) -> None:
    def fake_run_brief_judge(
        preprocessed_content: dict[str, object],
        judge_rules: dict[str, object],
    ) -> dict[str, object]:
        return {
            "dimension": "brief",
            "status": "unknown",
            "score": None,
            "confidence": None,
            "findings": [],
        }

    monkeypatch.setattr(
        brief_flow,
        "run_brief_judge",
        fake_run_brief_judge,
    )

    payload = {
        "content": "Article test",
    }

    result = brief_flow.execute_brief_flow(payload)

    assert result["request_echo"]["context"] == {}
    assert result["preprocessing"]["normalized_brief"] == ""
    assert result["preprocessing"]["is_brief_empty"] is True


def test_execute_brief_flow_returns_aggregation(
    monkeypatch,
) -> None:
    def fake_run_brief_judge(
        preprocessed_content: dict[str, object],
        judge_rules: dict[str, object],
    ) -> dict[str, object]:
        return {
            "dimension": "brief",
            "status": "fail",
            "score": 40,
            "confidence": 80,
            "findings": [
                {
                    "rule_id": "brief.low_alignment",
                    "severity": "major",
                    "message": "Brief alignment is too low.",
                }
            ],
        }

    monkeypatch.setattr(
        brief_flow,
        "run_brief_judge",
        fake_run_brief_judge,
    )

    payload = {
        "content": "Article test",
        "context": {
            "brief": "Brief test",
        },
    }

    result = brief_flow.execute_brief_flow(payload)

    assert result["aggregation"]["status"] == "fail"
    assert result["aggregation"]["score"] == 40
    assert result["aggregation"]["blocking_issues"]

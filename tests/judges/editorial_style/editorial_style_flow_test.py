"""Tests for the editorial style evaluation flow."""

from __future__ import annotations

from typing import Any

from contentcreajudge.application.judge_flow.editorial_style_flow import (
    execute_editorial_style_flow,
)


def test_execute_editorial_style_flow_returns_expected_response(
    monkeypatch: Any,
) -> None:
    """It should execute the editorial style flow."""

    def fake_run_editorial_style_judge(
        preprocessed_content: dict[str, object],
        judge_rules: dict[str, object],
    ) -> dict[str, object]:
        return {
            "dimension": "editorial_style",
            "status": "pass",
            "score": 86,
            "criteria_scores": {
                "style_alignment": 90,
                "reasoning_alignment": 85,
                "concept_handling": 88,
                "expression_control": 86,
                "writing_conventions": 84,
                "example_alignment": 90,
            },
            "findings": [],
            "summary": "Article bien aligné.",
            "agreement": True,
            "score_gap": 0,
            "providers": {},
            "applied_rule": judge_rules,
        }

    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.editorial_style_flow.run_editorial_style_judge",
        fake_run_editorial_style_judge,
    )

    payload = {
        "content": "<p>Article à juger.</p>",
        "profile": "default",
        "editorial_style": {
            "writingStyle": "Style attendu.",
            "writeLikeThis": "Bon exemple.",
            "notLikeThis": "Mauvais exemple.",
        },
        "context": {
            "content_type": "articles",
            "locale": "fr-FR",
        },
        "request_id": "test-123",
    }

    result = execute_editorial_style_flow(payload)

    assert result["request_echo"]["profile"] == "default"
    assert result["request_echo"]["request_id"] == "test-123"

    assert result["rule_resolution"]["enabled_judges"] == ["editorial_style"]

    assert result["preprocessing"]["normalized_content"] == "Article à juger."
    assert result["judge_result"]["status"] == "pass"
    assert result["judge_result"]["score"] == 86

    assert result["aggregation"]["status"] == "pass"
    assert result["aggregation"]["score"] == 86

    assert "Editorial style flow complete" in result["message"]


def test_execute_editorial_style_flow_handles_missing_editorial_style(
    monkeypatch: Any,
) -> None:
    """It should handle missing editorial style as an empty style object."""

    def fake_run_editorial_style_judge(
        preprocessed_content: dict[str, object],
        judge_rules: dict[str, object],
    ) -> dict[str, object]:
        assert preprocessed_content["editorial_style"] == {
            "writingStyle": "",
            "writeLikeThis": "",
            "notLikeThis": "",
        }

        return {
            "dimension": "editorial_style",
            "status": "warn",
            "score": 60,
            "criteria_scores": {},
            "findings": [],
            "summary": "Style incomplet.",
            "agreement": True,
            "score_gap": 0,
            "providers": {},
            "applied_rule": judge_rules,
        }

    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.editorial_style_flow.run_editorial_style_judge",
        fake_run_editorial_style_judge,
    )

    result = execute_editorial_style_flow(
        {
            "content": "Article à juger.",
            "profile": "default",
        }
    )

    assert result["judge_result"]["status"] == "warn"
    assert result["preprocessing"]["style_stats"]["missing_style_fields"] == [
        "writingStyle",
        "writeLikeThis",
        "notLikeThis",
    ]

from __future__ import annotations

from unittest.mock import patch

from contentcreajudge.application.judge_flow.length_flow import (
    execute_length_flow,
)


def test_execute_length_flow_runs_complete_pipeline() -> None:
    """Run rule resolution, preprocessing, judging, and aggregation."""
    payload = {
        "content": "Bonjour le monde",
        "profile": "blog",
        "request_id": "req-123",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
        },
    }

    resolved_rules = {
        "judge_id": "length",
        "min_words": 1000,
        "max_words": 2000,
    }

    preprocessed_content = {
        "normalized_text": "Bonjour le monde",
        "word_count": 3,
        "is_empty": False,
    }

    judge_result = {
        "dimension": "length",
        "status": "pass",
        "score": 100,
        "findings": [],
    }

    aggregation_result = {
        "status": "pass",
        "score": 100,
    }

    with (
        patch(
            "contentcreajudge.application.judge_flow.length_flow.resolve_length_rules",
            return_value=resolved_rules,
        ) as mock_resolve,
        patch(
            "contentcreajudge.application.judge_flow.length_flow.preprocess_length_content",
            return_value=preprocessed_content,
        ) as mock_preprocess,
        patch(
            "contentcreajudge.application.judge_flow.length_flow.run_length_judge",
            return_value=judge_result,
        ) as mock_judge,
        patch(
            "contentcreajudge.application.judge_flow.length_flow.aggregate_length_result",
            return_value=aggregation_result,
        ) as mock_aggregate,
    ):
        result = execute_length_flow(payload)

    mock_resolve.assert_called_once_with(payload["context"])

    mock_preprocess.assert_called_once_with("Bonjour le monde")

    mock_judge.assert_called_once_with(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_rules,
    )

    mock_aggregate.assert_called_once_with(judge_result)

    assert result == {
        "request_echo": {
            "content": "Bonjour le monde",
            "profile": "blog",
            "request_id": "req-123",
            "context": {
                "content_type": "articles",
                "expected_length": "MEDIUM",
            },
        },
        "rule_resolution": {
            "profile": "blog",
            "enabled_judges": ["length"],
            "judge_rules": {
                "length": resolved_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": judge_result,
        "aggregation": aggregation_result,
        "message": (
            "Length flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }


def test_execute_length_flow_uses_default_values_when_missing() -> None:
    """Use safe default request values when payload keys are missing."""
    payload = {}

    resolved_rules = {
        "judge_id": "length",
        "min_words": 100,
        "max_words": 500,
    }

    preprocessed_content = {
        "normalized_text": "",
        "word_count": 0,
        "is_empty": True,
    }

    judge_result = {
        "dimension": "length",
        "status": "fail",
        "score": 0,
        "findings": [],
    }

    aggregation_result = {
        "status": "fail",
        "score": 0,
    }

    with (
        patch(
            "contentcreajudge.application.judge_flow.length_flow.resolve_length_rules",
            return_value=resolved_rules,
        ) as mock_resolve,
        patch(
            "contentcreajudge.application.judge_flow.length_flow.preprocess_length_content",
            return_value=preprocessed_content,
        ),
        patch(
            "contentcreajudge.application.judge_flow.length_flow.run_length_judge",
            return_value=judge_result,
        ),
        patch(
            "contentcreajudge.application.judge_flow.length_flow.aggregate_length_result",
            return_value=aggregation_result,
        ),
    ):
        result = execute_length_flow(payload)

    mock_resolve.assert_called_once_with({})

    assert result["request_echo"]["content"] == ""
    assert result["request_echo"]["profile"] == "default"
    assert result["request_echo"]["request_id"] is None
    assert result["request_echo"]["context"] == {}

    assert result["aggregation"] == aggregation_result


def test_execute_length_flow_uses_global_preprocessing_when_available() -> None:
    payload = {
        "content": "<p>Texte original court.</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "global_preprocessing": {
            "normalized_text": "mot " * 1200,
            "word_count": 1200,
            "is_empty": False,
        },
    }

    result = execute_length_flow(payload)

    preprocessing = result["preprocessing"]

    assert preprocessing["word_count"] == 1200
    assert preprocessing["is_empty"] is False
    assert result["judge_result"]["status"] == "pass"

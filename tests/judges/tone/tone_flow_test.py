from __future__ import annotations

from contentcreajudge.application.judge_flow.tone_flow import execute_tone_flow


def test_execute_tone_flow_returns_full_pipeline(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.tone_flow.run_tone_judge",
        lambda preprocessed_content, judge_rules: {
            "dimension": "tone",
            "status": "pass",
            "score": 90,
            "summary": "Tone is aligned.",
            "provider_results": {
                "openai": {"status": "pass", "score": 90},
                "mistral": {"status": "pass", "score": 90},
            },
            "agreement": {
                "status_match": True,
                "score_gap": 0,
            },
            "findings": [],
        },
    )

    payload = {
        "content": "<p>Texte didactique.</p>",
        "profile": "default",
        "context": {
            "expected_tone": "Didactique",
            "locale": "fr-FR",
        },
        "request_id": "test-tone-1",
    }

    result = execute_tone_flow(payload)

    assert result["request_echo"]["content"] == "<p>Texte didactique.</p>"
    assert result["request_echo"]["profile"] == "default"
    assert result["rule_resolution"]["enabled_judges"] == ["tone"]
    assert result["preprocessing"]["is_empty"] is False
    assert result["judge_result"]["dimension"] == "tone"
    assert result["aggregation"]["status"] == "pass"
    assert "Tone flow complete" in result["message"]


def test_execute_tone_flow_handles_missing_optional_context(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.tone_flow.run_tone_judge",
        lambda preprocessed_content, judge_rules: {
            "dimension": "tone",
            "status": "warn",
            "score": 70,
            "findings": [],
        },
    )

    payload = {
        "content": "Texte.",
        "context": {
            "expected_tone": "Neutre",
        },
    }

    result = execute_tone_flow(payload)

    assert result["request_echo"]["profile"] == "default"
    assert (
        result["rule_resolution"]["judge_rules"]["tone"]["context"]["expected_tone"]
        == "Neutre"
    )
    assert result["aggregation"]["status"] == "warn"

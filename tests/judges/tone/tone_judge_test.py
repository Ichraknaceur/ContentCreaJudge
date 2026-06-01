from __future__ import annotations

import json

from contentcreajudge.judges.tone.tone_judge import run_tone_judge


def _judge_rules() -> dict[str, object]:
    return {
        "judge_id": "tone",
        "version": 1,
        "criteria": [
            {"criterion_id": "tone.expected_tone_match", "weight": 35},
            {"criterion_id": "tone.contextual_alignment", "weight": 25},
            {"criterion_id": "tone.register_consistency", "weight": 15},
            {"criterion_id": "tone.intensity_calibration", "weight": 15},
            {"criterion_id": "tone.natural_expression", "weight": 10},
        ],
        "context": {
            "expected_tone": "Didactique",
        },
        "messages": {
            "pass": "The content respects the expected tone.",
            "warn": "The content mostly respects the expected tone.",
            "fail": "The content does not sufficiently respect the expected tone.",
            "unknown": "Tone evaluation could not be completed reliably.",
        },
    }


def _provider_response(score: int, status: str) -> str:
    return json.dumps(
        {
            "dimension": "tone",
            "status": status,
            "score": score,
            "expected_tone": "Didactique",
            "detected_tone": "Didactique",
            "confidence": 0.9,
            "summary": "Tone is mostly aligned.",
            "criterion_scores": {
                "tone.expected_tone_match": score,
                "tone.contextual_alignment": score,
                "tone.register_consistency": score,
                "tone.intensity_calibration": score,
                "tone.natural_expression": score,
            },
            "findings": [],
        }
    )


def test_run_tone_judge_returns_provider_results(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: _provider_response(90, "pass"),
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: _provider_response(80, "pass"),
    )

    result = run_tone_judge(
        preprocessed_content={"content": "<p>Texte pédagogique.</p>"},
        judge_rules=_judge_rules(),
    )

    assert result["dimension"] == "tone"
    assert result["status"] == "pass"
    assert result["score"] == 85
    assert "provider_results" in result
    assert "openai" in result["provider_results"]
    assert "mistral" in result["provider_results"]


def test_run_tone_judge_detects_status_disagreement(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: _provider_response(85, "pass"),
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: _provider_response(55, "fail"),
    )

    result = run_tone_judge(
        preprocessed_content={"content": "Texte."},
        judge_rules=_judge_rules(),
    )

    assert result["agreement"]["status_match"] is False
    assert result["agreement"]["score_gap"] == 30
    assert result["status"] == "warn"


def test_run_tone_judge_recalculates_score_from_criteria(monkeypatch) -> None:
    raw_response = json.dumps(
        {
            "dimension": "tone",
            "status": "pass",
            "score": 100,
            "expected_tone": "Didactique",
            "detected_tone": "Didactique",
            "confidence": 0.9,
            "summary": "Tone is aligned.",
            "criterion_scores": {
                "tone.expected_tone_match": 50,
                "tone.contextual_alignment": 50,
                "tone.register_consistency": 50,
                "tone.intensity_calibration": 50,
                "tone.natural_expression": 50,
            },
            "findings": [],
        }
    )

    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: raw_response,
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: raw_response,
    )

    result = run_tone_judge(
        preprocessed_content={"content": "Texte."},
        judge_rules=_judge_rules(),
    )

    assert result["score"] == 50
    assert result["status"] == "fail"

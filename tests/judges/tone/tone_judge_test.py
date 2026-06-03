from __future__ import annotations

import json

from contentcreajudge.judges.tone.tone_judge import run_tone_judge


def _judge_rules() -> dict[str, object]:
    return {
        "judge_id": "tone",
        "version": 1,
        "criteria": [
            {"criterion_id": "tone.contextual_alignment", "weight": 30},
            {"criterion_id": "tone.register_consistency", "weight": 25},
            {"criterion_id": "tone.intensity_calibration", "weight": 25},
            {"criterion_id": "tone.natural_expression", "weight": 20},
        ],
        "guards": {
            "min_words": 80,
            "min_sentences": 3,
        },
        "organization_tones": {},
        "blind_observation": {},
        "context": {
            "expected_tone": "Pédagogique",
            "org_tones": ["posé", "pédagogique", "convaincant"],
        },
        "messages": {
            "pass": "The content respects the expected tone.",
            "warn": "The content mostly respects the expected tone.",
            "fail": "The content does not sufficiently respect the expected tone.",
            "unknown": "Tone evaluation could not be completed reliably.",
        },
    }


def _provider_response(
    *,
    score: int,
    status: str,
    perceived_tone: str = "pédagogique structuré",
) -> str:
    return json.dumps(
        {
            "dimension": "tone",
            "status": status,
            "score": score,
            "confidence": 0.9,
            "blind_observation": {
                "perceived_tone": perceived_tone,
                "tone_presence": {
                    perceived_tone: 100,
                },
                "lexical_evidence": [
                    "Citation exacte 1 — explication courte.",
                    "Citation exacte 2 — explication courte.",
                ],
            },
            "ton_distribution": [
                {
                    "source_tone": "pédagogique",
                    "source_score": 100,
                    "in_org_list": True,
                    "distribution": [
                        {
                            "tone": "posé",
                            "score": 0,
                            "justification": "Absent du contenu.",
                        },
                        {
                            "tone": "pédagogique",
                            "score": 90,
                            "justification": "Ton dominant.",
                        },
                        {
                            "tone": "convaincant",
                            "score": 10,
                            "justification": "Quelques passages affirmatifs.",
                        },
                    ],
                    "sum_check": 100,
                }
            ],
            "expected_tone": "Pédagogique",
            "detected_tone": perceived_tone,
            "summary": "Le ton est pédagogique et aligné.",
            "criterion_scores": {
                "detected_tone": {
                    "tone.contextual_alignment": score,
                    "tone.register_consistency": score,
                    "tone.intensity_calibration": score,
                    "tone.natural_expression": score,
                },
                "expected_tone": {
                    "tone.contextual_alignment": score,
                    "tone.register_consistency": score,
                    "tone.intensity_calibration": score,
                    "tone.natural_expression": score,
                },
            },
            "findings": [],
        }
    )


def test_run_tone_judge_returns_provider_results(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: _provider_response(score=90, status="pass"),
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: _provider_response(score=80, status="pass"),
    )

    result = run_tone_judge(
        preprocessed_content={"content": "<p>Texte pédagogique suffisamment long.</p>"},
        judge_rules=_judge_rules(),
    )

    assert result["dimension"] == "tone"
    assert result["status"] == "pass"
    assert result["score"] == 85
    assert "provider_results" in result
    assert "openai" in result["provider_results"]
    assert "mistral" in result["provider_results"]


def test_run_tone_judge_keeps_blind_observation(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: _provider_response(score=90, status="pass"),
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: _provider_response(score=90, status="pass"),
    )

    result = run_tone_judge(
        preprocessed_content={"content": "Texte pédagogique."},
        judge_rules=_judge_rules(),
    )

    openai_result = result["provider_results"]["openai"]

    assert openai_result["blind_observation"]["perceived_tone"] == (
        "pédagogique structuré"
    )
    assert openai_result["blind_observation"]["tone_presence"] == {
        "pédagogique structuré": 100,
    }
    assert len(openai_result["blind_observation"]["lexical_evidence"]) == 2


def test_run_tone_judge_keeps_ton_distribution(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: _provider_response(score=90, status="pass"),
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: _provider_response(score=90, status="pass"),
    )

    result = run_tone_judge(
        preprocessed_content={"content": "Texte pédagogique."},
        judge_rules=_judge_rules(),
    )

    distribution = result["provider_results"]["openai"]["ton_distribution"]

    assert distribution[0]["source_tone"] == "pédagogique"
    assert distribution[0]["source_score"] == 100
    assert distribution[0]["in_org_list"] is True
    assert distribution[0]["sum_check"] == 100
    assert len(distribution[0]["distribution"]) == 3


def test_run_tone_judge_recalculates_score_from_criteria(monkeypatch) -> None:
    raw_response = _provider_response(score=50, status="pass")

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
    assert result["provider_results"]["openai"]["score"] == 50


def test_run_tone_judge_recalculates_score_from_expected_tone_scores(
    monkeypatch,
) -> None:
    response = _provider_response(score=90, status="pass")
    parsed_response = json.loads(response)

    parsed_response["criterion_scores"]["detected_tone"] = {
        "tone.contextual_alignment": 100,
        "tone.register_consistency": 100,
        "tone.intensity_calibration": 100,
        "tone.natural_expression": 100,
    }
    parsed_response["criterion_scores"]["expected_tone"] = {
        "tone.contextual_alignment": 50,
        "tone.register_consistency": 50,
        "tone.intensity_calibration": 50,
        "tone.natural_expression": 50,
    }

    raw_response = json.dumps(parsed_response)

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


def test_run_tone_judge_detects_status_disagreement(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: _provider_response(score=85, status="pass"),
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: _provider_response(score=55, status="fail"),
    )

    result = run_tone_judge(
        preprocessed_content={"content": "Texte."},
        judge_rules=_judge_rules(),
    )

    assert result["agreement"]["status_match"] is False
    assert result["agreement"]["score_gap"] == 30
    assert result["status"] == "warn"
    assert result["score"] == 70


def test_run_tone_judge_handles_invalid_json_response(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: "not valid json",
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: _provider_response(score=90, status="pass"),
    )

    result = run_tone_judge(
        preprocessed_content={"content": "Texte."},
        judge_rules=_judge_rules(),
    )

    openai_result = result["provider_results"]["openai"]

    assert openai_result["status"] == "unknown"
    assert openai_result["score"] is None
    assert openai_result["criterion_scores"] is None
    assert openai_result["blind_observation"] is None
    assert result["score"] == 90
    assert result["status"] == "pass"


def test_run_tone_judge_handles_unknown_guard_response(monkeypatch) -> None:
    unknown_response = json.dumps(
        {
            "dimension": "tone",
            "status": "unknown",
            "score": None,
            "confidence": None,
            "blind_observation": None,
            "ton_distribution": None,
            "criterion_scores": None,
            "findings": [],
            "expected_tone": "Pédagogique",
            "detected_tone": "",
            "summary": "Le contenu est trop court pour une évaluation fiable du ton.",
        }
    )

    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_openai_json",
        lambda prompt: unknown_response,
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.tone.tone_judge.call_mistral_json",
        lambda prompt: unknown_response,
    )

    result = run_tone_judge(
        preprocessed_content={"content": "Texte court."},
        judge_rules=_judge_rules(),
    )

    assert result["status"] == "unknown"
    assert result["score"] is None
    assert result["agreement"]["score_gap"] is None


def test_run_tone_judge_normalizes_tone_presence(monkeypatch) -> None:
    tone_presence_response = json.loads(_provider_response(score=82, status="pass"))
    tone_presence_response["blind_observation"]["perceived_tone"] = (
        "pédagogique, convaincant"
    )
    tone_presence_response["blind_observation"]["tone_presence"] = {
        "pédagogique": 70,
        "convaincant": 30,
    }

    raw_response = json.dumps(tone_presence_response)

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

    tone_presence = result["provider_results"]["openai"]["blind_observation"][
        "tone_presence"
    ]

    assert tone_presence == {
        "pédagogique": 70,
        "convaincant": 30,
    }


def test_run_tone_judge_flags_inconsistent_tone_presence(monkeypatch) -> None:
    response = json.loads(
        _provider_response(score=82, status="pass", perceived_tone="empathique")
    )
    response["blind_observation"]["tone_presence"] = {
        "posé": 60,
        "pédagogique": 40,
    }

    raw_response = json.dumps(response)

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

    findings = result["provider_results"]["openai"]["findings"]

    assert any(
        finding["rule_id"] == "tone.invalid_tone_presence"
        and finding["severity"] == "critical"
        for finding in findings
    )


def test_run_tone_judge_handles_tone_not_in_org_list(monkeypatch) -> None:
    response = json.loads(
        _provider_response(score=70, status="warn", perceived_tone="émotionnel")
    )
    response["ton_distribution"] = [
        {
            "source_tone": "émotionnel",
            "source_score": 100,
            "in_org_list": False,
            "distribution": [],
            "sum_check": 100,
        }
    ]

    raw_response = json.dumps(response)

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

    distribution = result["provider_results"]["openai"]["ton_distribution"][0]

    assert distribution["source_tone"] == "émotionnel"
    assert distribution["in_org_list"] is False
    assert distribution["distribution"] == []
    assert distribution["sum_check"] == 100

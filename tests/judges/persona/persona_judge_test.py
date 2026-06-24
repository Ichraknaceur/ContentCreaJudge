"""Tests for the persona judge."""

from __future__ import annotations

import json

from contentcreajudge.judges.persona.persona_judge import run_persona_judge


def _resolved_rules() -> dict[str, object]:
    return {
        "judge_id": "persona",
        "version": 1,
        "persona": {
            "first_name": "Sophie",
            "function": "Consultant indépendant",
            "persona_fields": {
                "professional_objectives": "Structurer sa stratégie éditoriale.",
                "problems_frustrations": "Éviter la dispersion des contenus.",
            },
        },
        "business_type": "B2B",
        "content_type": "articles",
        "funnel_stage": "AWARENESS",
        "locale": "fr-FR",
        "criteria": [
            {"criterion_id": "persona.relevance", "weight": 0.30},
            {"criterion_id": "persona.coverage", "weight": 0.20},
        ],
        "hard_rules": [
            {
                "rule_id": "persona.first_name_mentioned",
                "severity": "blocking",
            }
        ],
        "scoring": {
            "thresholds": {
                "pass": 80,
                "warn": 60,
            }
        },
        "messages": {
            "unknown": "Persona evaluation could not be completed.",
        },
    }


def test_run_persona_judge_returns_normalized_result() -> None:
    """Persona judge should return a normalized result."""

    def fake_llm_caller(prompt: str, provider: str) -> str:
        return json.dumps(
            {
                "dimension": "persona",
                "status": "pass",
                "score": 86,
                "criteria_scores": {
                    "persona.relevance": 3,
                    "persona.coverage": 2,
                },
                "identified_persona_elements": {
                    "goals": ["Structurer sa stratégie éditoriale"],
                    "pain_points": ["Éviter la dispersion des contenus"],
                },
                "findings": [],
                "summary": "Le contenu est bien adapté au persona.",
            }
        )

    result = run_persona_judge(
        content="Contenu de test.",
        resolved_rules=_resolved_rules(),
        provider="openai",
        llm_caller=fake_llm_caller,
    )

    assert result["dimension"] == "persona"
    assert result["status"] == "pass"
    assert result["score"] == 86
    assert result["provider"] == "openai"
    assert "applied_rule" in result


def test_run_persona_judge_handles_invalid_json() -> None:
    """Persona judge should not crash when LLM returns invalid JSON."""

    def fake_llm_caller(prompt: str, provider: str) -> str:
        return "This is not JSON"

    result = run_persona_judge(
        content="Contenu de test.",
        resolved_rules=_resolved_rules(),
        provider="mistral",
        llm_caller=fake_llm_caller,
    )

    assert result["dimension"] == "persona"
    assert result["status"] == "unknown"
    assert result["score"] == 0
    assert result["provider"] == "mistral"
    assert result["findings"][0]["rule_id"] == "persona.invalid_llm_json"


def test_run_persona_judge_clamps_score_to_100() -> None:
    """Persona judge should clamp scores above 100."""

    def fake_llm_caller(prompt: str, provider: str) -> str:
        return json.dumps(
            {
                "dimension": "persona",
                "status": "pass",
                "score": 130,
                "findings": [],
            }
        )

    result = run_persona_judge(
        content="Contenu de test.",
        resolved_rules=_resolved_rules(),
        provider="openai",
        llm_caller=fake_llm_caller,
    )

    assert result["score"] == 100


def test_run_persona_judge_defaults_invalid_status_to_unknown() -> None:
    """Persona judge should normalize invalid statuses."""

    def fake_llm_caller(prompt: str, provider: str) -> str:
        return json.dumps(
            {
                "dimension": "persona",
                "status": "excellent",
                "score": 90,
                "findings": [],
            }
        )

    result = run_persona_judge(
        content="Contenu de test.",
        resolved_rules=_resolved_rules(),
        provider="openai",
        llm_caller=fake_llm_caller,
    )

    assert result["status"] == "unknown"

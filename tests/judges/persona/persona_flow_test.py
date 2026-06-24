"""Tests for the persona evaluation flow."""

from __future__ import annotations

from unittest.mock import patch

from contentcreajudge.application.judge_flow.persona_flow import (
    execute_persona_flow,
)


def _payload() -> dict[str, object]:
    return {
        "content": "Un contenu de test pour consultant indépendant.",
        "profile": "default",
        "context": {
            "personas": [
                {
                    "persona_id": "persona-sophie",
                    "first_name": "Sophie",
                    "function": "Consultant indépendant",
                    "persona_fields": {
                        "professional_objectives": "Structurer une stratégie éditoriale.",
                        "problems_frustrations": "Éviter la dispersion des contenus.",
                        "decision_making_influence": "Décide seul après test concret.",
                        "psy_profile": "Autonome, analytique, sensible à la structure.",
                    },
                },
            ],
            "expected_persona_id": "persona-sophie",
            "business_type": "B2B",
            "content_type": "articles",
            "funnel_stage": "AWARENESS",
            "locale": "fr-FR",
        },
    }


def test_execute_persona_flow_returns_expected_sections() -> None:
    """Persona flow should return request, rules, judge result and aggregation."""
    with patch(
        "contentcreajudge.application.judge_flow.persona_flow.run_persona_judge",
    ) as run_persona_judge_mock:
        run_persona_judge_mock.return_value = {
            "dimension": "persona",
            "status": "pass",
            "score": 85,
            "findings": [],
            "provider_results": [],
            "agreement": {
                "status_agreement": True,
                "score_gap": 0,
            },
        }

        result = execute_persona_flow(_payload())

    assert result["request_echo"]["profile"] == "default"
    assert result["rule_resolution"]["enabled_judges"] == ["persona"]
    assert result["judge_result"]["dimension"] == "persona"
    assert result["aggregation"]["status"] == "pass"

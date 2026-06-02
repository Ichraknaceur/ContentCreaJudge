"""API tests for the persona judge endpoint."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app


def test_persona_judge_endpoint_returns_success() -> None:
    """Persona endpoint should return the persona flow response."""
    app = create_app()
    client = TestClient(app)

    payload = {
        "content": "Un contenu de test.",
        "profile": "default",
        "context": {
            "personas": [
                {
                    "persona_id": "persona-sophie",
                    "first_name": "Sophie",
                    "function": "Consultant indépendant",
                    "persona_fields": {
                        "professional_objectives": "Structurer sa stratégie éditoriale.",
                        "problems_frustrations": "Éviter la dispersion des contenus.",
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

    with patch(
        "contentcreajudge.api.judges.persona.execute_persona_flow",
    ) as execute_persona_flow_mock:
        execute_persona_flow_mock.return_value = {
            "judge_result": {
                "dimension": "persona",
                "status": "pass",
                "score": 85,
            },
            "aggregation": {
                "status": "pass",
                "score": 85,
            },
        }

        response = client.post("/api/v1/judges/persona/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json()["judge_result"]["dimension"] == "persona"

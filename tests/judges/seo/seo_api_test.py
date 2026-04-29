from __future__ import annotations

from fastapi.testclient import TestClient

from contentcreajudge.api.app import app

client = TestClient(app)


def _build_payload() -> dict[str, object]:
    return {
        "content": """
        <p>La différenciation éditoriale en milieu saturé commence ici.</p>

        <h2>différenciation éditoriale en milieu saturé</h2>
        <p>La coherence de la voix editoriale améliore la lisibilite.</p>

        <h2>Construire un repère stable</h2>
        <p>L autorite thematique de la marque se construit aussi par la différenciation éditoriale en milieu saturé.</p>

        <h2>Conclusion</h2>
        <p>La différenciation éditoriale en milieu saturé demeure un repère stable
        pour l autorite thematique de la marque et repetition strategique du message sans impression de deja-vu en b2b.</p>
        """,
        "profile": "default",
        "request_id": "seo-api-test-001",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "funnel_stage": "AWARENESS",
            "locale": "fr-FR",
            "main_keyword": "différenciation éditoriale en milieu saturé",
            "secondary_keywords": [
                "coherence de la voix editoriale",
                "autorite thematique de la marque",
            ],
            "long_tail_keywords": [
                "repetition strategique du message sans impression de deja-vu en b2b",
            ],
        },
    }


def test_evaluate_seo_judge_returns_200() -> None:
    response = client.post("/api/v1/judges/seo/evaluate", json=_build_payload())

    assert response.status_code == 200

    body = response.json()
    assert "request_echo" in body
    assert "rule_resolution" in body
    assert "preprocessing" in body
    assert "judge_result" in body
    assert "aggregation" in body

    assert body["judge_result"]["dimension"] == "seo"
    assert body["request_echo"]["request_id"] == "seo-api-test-001"


def test_evaluate_seo_judge_rejects_extra_fields() -> None:
    payload = _build_payload()
    payload["unexpected_field"] = "forbidden"

    response = client.post("/api/v1/judges/seo/evaluate", json=payload)

    assert response.status_code == 422


def test_evaluate_seo_judge_rejects_missing_main_keyword() -> None:
    payload = _build_payload()
    del payload["context"]["main_keyword"]

    response = client.post("/api/v1/judges/seo/evaluate", json=payload)

    assert response.status_code == 422

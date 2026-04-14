from fastapi.testclient import TestClient

from contentcreajudge.api.app import app

client = TestClient(app)


def test_evaluate_structure_judge_api_passes_with_valid_payload() -> None:
    payload = {
        "content": """
        <p>Introduction générée.</p>
        <h2>Section A</h2>
        <p>Contenu</p>
        <h3>Sous-section A.1</h3>
        <p>Contenu</p>
        <h2>Conclusion</h2>
        <p>Contenu final</p>
        """,
        "profile": "default",
        "context": {
            "expected_outline_html": """
            <p>Introduction attendue.</p>
            <h2>Section A</h2>
            <p>Texte</p>
            <h3>Sous-section A.1</h3>
            <p>Texte</p>
            <h2>Conclusion</h2>
            <p>Texte final</p>
            """,
            "locale": "fr-FR",
        },
    }

    response = client.post("/api/v1/judges/structure/evaluate", json=payload)

    assert response.status_code == 200

    body = response.json()
    assert body["judge_result"]["dimension"] == "structure"
    assert body["judge_result"]["status"] == "pass"
    assert body["aggregation"]["status"] == "pass"


def test_evaluate_structure_judge_api_rejects_invalid_payload() -> None:
    payload = {
        "content": "<p>Intro</p><h2>Section A</h2>",
        "profile": "default",
        "context": {
            "locale": "fr-FR",
        },
    }

    response = client.post("/api/v1/judges/structure/evaluate", json=payload)

    assert response.status_code == 422
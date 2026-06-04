from __future__ import annotations

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app


def test_tone_judge_endpoint_returns_success(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.api.judges.tone.execute_tone_flow",
        lambda payload: {
            "judge_result": {
                "dimension": "tone",
                "status": "pass",
                "score": 90,
            },
            "message": "Tone flow complete.",
        },
    )

    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/tone/evaluate",
        json={
            "content": "<p>Texte didactique.</p>",
            "profile": "default",
            "context": {
                "expected_tone": "Didactique",
                "locale": "fr-FR",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["judge_result"]["dimension"] == "tone"
    assert data["judge_result"]["status"] == "pass"


def test_tone_judge_endpoint_requires_expected_tone() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/tone/evaluate",
        json={
            "content": "<p>Texte.</p>",
            "profile": "default",
            "context": {
                "locale": "fr-FR",
            },
        },
    )

    assert response.status_code == 422

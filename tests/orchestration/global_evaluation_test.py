from __future__ import annotations

from fastapi.testclient import TestClient

from contentcreajudge.api.app import app


def test_global_evaluation_endpoint_runs_length_judge() -> None:
    client = TestClient(app)

    payload = {
        "content": "<p>" + "mot " * 1200 + "</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "enabled_judges": ["length"],
    }

    response = client.post("/api/v1/evaluations", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["score"] is None

    assert len(data["judge_results"]) == 1
    assert data["judge_results"][0]["judge"] == "length"
    assert data["judge_results"][0]["status"] == "pass"
    assert data["judge_results"][0]["score"] == 100

    assert len(data["dimension_results"]) == 1
    assert data["dimension_results"][0]["dimension"] == "length"

    assert "global_preprocessing" in data
    assert data["global_preprocessing"]["word_count"] == 1200


def test_global_evaluation_endpoint_returns_length_fail() -> None:
    client = TestClient(app)

    payload = {
        "content": "<p>Texte trop court.</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "enabled_judges": ["length"],
    }

    response = client.post("/api/v1/evaluations", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "completed"
    assert data["score"] is None

    assert data["judge_results"][0]["judge"] == "length"
    assert data["judge_results"][0]["status"] == "fail"
    assert data["judge_results"][0]["score"] == 0


def test_global_evaluation_endpoint_rejects_extra_fields() -> None:
    client = TestClient(app)

    payload = {
        "content": "<p>test</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "unknown_field": "not allowed",
    }

    response = client.post("/api/v1/evaluations", json=payload)

    assert response.status_code == 422

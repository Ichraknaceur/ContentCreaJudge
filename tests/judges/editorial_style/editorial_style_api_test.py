"""Tests for the editorial style API endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app


def test_editorial_style_endpoint_returns_response(monkeypatch) -> None:
    """It should execute the editorial style endpoint."""

    def fake_execute_editorial_style_flow(
        payload: dict[str, object],
    ) -> dict[str, object]:
        return {
            "request_echo": payload,
            "judge_result": {
                "dimension": "editorial_style",
                "status": "pass",
                "score": 86,
            },
            "aggregation": {
                "status": "pass",
                "score": 86,
            },
            "message": "Editorial style flow complete.",
        }

    monkeypatch.setattr(
        "contentcreajudge.api.judges.editorial_style.execute_editorial_style_flow",
        fake_execute_editorial_style_flow,
    )

    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/editorial-style/evaluate",
        json={
            "content": "Article à juger.",
            "profile": "default",
            "editorial_style": {
                "writingStyle": "Style attendu.",
                "writeLikeThis": "Bon exemple.",
                "notLikeThis": "Mauvais exemple.",
            },
            "context": {
                "content_type": "articles",
                "locale": "fr-FR",
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["judge_result"]["dimension"] == "editorial_style"
    assert data["judge_result"]["status"] == "pass"
    assert data["aggregation"]["status"] == "pass"


def test_editorial_style_endpoint_rejects_extra_fields() -> None:
    """It should reject unknown payload fields."""
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/editorial-style/evaluate",
        json={
            "content": "Article à juger.",
            "profile": "default",
            "editorial_style": {
                "writingStyle": "Style attendu.",
                "writeLikeThis": "Bon exemple.",
                "notLikeThis": "Mauvais exemple.",
            },
            "unknown": "not allowed",
        },
    )

    assert response.status_code == 422

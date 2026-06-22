"""Tests for the Brief judge API endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app
from contentcreajudge.api.judges import brief as brief_endpoint


def test_brief_endpoint_accepts_valid_payload(monkeypatch) -> None:
    def fake_execute_brief_flow(payload: dict[str, object]) -> dict[str, object]:
        return {
            "judge_result": {
                "dimension": "brief",
                "status": "pass",
                "score": 90,
            },
            "aggregation": {
                "status": "pass",
                "score": 90,
            },
        }

    monkeypatch.setattr(
        brief_endpoint,
        "execute_brief_flow",
        fake_execute_brief_flow,
    )

    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/brief/evaluate",
        json={
            "content": "Article test",
            "profile": "default",
            "context": {
                "brief": "Brief test",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["judge_result"]["dimension"] == "brief"
    assert data["aggregation"]["status"] == "pass"


def test_brief_endpoint_rejects_missing_context() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/brief/evaluate",
        json={
            "content": "Article test",
            "profile": "default",
        },
    )

    assert response.status_code == 422


def test_brief_endpoint_rejects_missing_brief() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/brief/evaluate",
        json={
            "content": "Article test",
            "profile": "default",
            "context": {},
        },
    )

    assert response.status_code == 422


def test_brief_endpoint_rejects_extra_fields() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/brief/evaluate",
        json={
            "content": "Article test",
            "profile": "default",
            "context": {
                "brief": "Brief test",
            },
            "unexpected": "not allowed",
        },
    )

    assert response.status_code == 422

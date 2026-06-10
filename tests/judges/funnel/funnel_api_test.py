"""Tests for the funnel judge API endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from contentcreajudge.api.app import app


def test_evaluate_funnel_judge_endpoint(monkeypatch) -> None:
    def fake_execute_funnel_flow(payload: dict[str, object]) -> dict[str, object]:
        assert payload["content"] == "Contenu pédagogique."
        assert payload["profile"] == "default"
        assert payload["context"] == {
            "expected_funnel": "awareness",
        }

        return {
            "judge_results": {
                "openai": {
                    "dimension": "funnel",
                    "status": "pass",
                    "score": 90,
                },
                "mistral": {
                    "dimension": "funnel",
                    "status": "warn",
                    "score": 72,
                },
            },
            "aggregations": {
                "openai": {"status": "pass", "score": 90},
                "mistral": {"status": "warn", "score": 72},
            },
        }

    monkeypatch.setattr(
        "contentcreajudge.api.judges.funnel.execute_funnel_flow",
        fake_execute_funnel_flow,
    )

    client = TestClient(app)

    response = client.post(
        "/api/v1/judges/funnel/evaluate",
        json={
            "content": "Contenu pédagogique.",
            "profile": "default",
            "context": {
                "expected_funnel": "awareness",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()

    assert body["judge_results"]["openai"]["status"] == "pass"
    assert body["judge_results"]["mistral"]["status"] == "warn"


def test_evaluate_funnel_judge_rejects_missing_expected_funnel() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/judges/funnel/evaluate",
        json={
            "content": "Contenu pédagogique.",
            "profile": "default",
            "context": {},
        },
    )

    assert response.status_code == 422

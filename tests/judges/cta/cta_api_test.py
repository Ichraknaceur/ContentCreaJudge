"""Tests for CTA judge API endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app


def test_cta_api_evaluates_valid_cta() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/cta/evaluate",
        json={
            "content": '<p>Intro</p><p class="cta"><strong>Read more</strong></p>',
            "profile": "default",
            "context": {
                "content_type": "articles",
                "funnel_stage": "AWARENESS",
                "expected_cta": "Read more",
                "content_purpose": "Sensibilisation",
                "language": "en",
            },
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["judge_result"]["dimension"] == "cta"
    assert data["judge_result"]["status"] == "pass"
    assert data["aggregation"]["status"] == "pass"


def test_cta_api_returns_validation_error_without_context() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/cta/evaluate",
        json={
            "content": "<p>Intro</p>",
            "profile": "default",
        },
    )

    assert response.status_code == 422


def test_cta_api_returns_validation_error_with_extra_field() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/cta/evaluate",
        json={
            "content": "<p>Intro</p>",
            "profile": "default",
            "context": {
                "content_type": "articles",
                "funnel_stage": "AWARENESS",
                "expected_cta": "Read more",
            },
            "unexpected": "not allowed",
        },
    )

    assert response.status_code == 422

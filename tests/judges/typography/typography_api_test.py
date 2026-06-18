from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app


def test_evaluate_typography_judge_returns_success() -> None:
    """The typography endpoint should return a successful evaluation payload."""
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/typography/evaluate",
        json={
            "content": "<p>Bonjour\u00a0! Texte propre.</p>",
            "profile": "default",
            "context": {
                "locale": "fr-FR",
            },
            "request_id": "req-typography-001",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["judge_result"]["dimension"] == "typography"
    assert payload["judge_result"]["status"] == "pass"
    assert payload["request_echo"]["request_id"] == "req-typography-001"


def test_evaluate_typography_judge_rejects_unsupported_locale() -> None:
    """The typography endpoint should expose a typed 422 for bad locales."""
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/typography/evaluate",
        json={
            "content": "<p>Bonjour!</p>",
            "profile": "default",
            "context": {
                "locale": "en-US",
            },
            "request_id": "req-typography-unsupported-locale",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload == {
        "error": {
            "code": "unsupported_typography_locale",
            "message": "Unsupported locale for typography evaluation: en-US",
            "details": {
                "locale": "en-US",
                "supported_locales": ["fr-FR"],
            },
        },
        "request_id": None,
    }


def test_evaluate_typography_judge_normalizes_pydantic_validation_error() -> None:
    """Missing required fields should return a normalized 422 error envelope."""
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/typography/evaluate",
        json={
            "content": "<p>Bonjour!</p>",
            "profile": "default",
            "context": {},
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "request_validation_error"
    assert payload["error"]["message"] == "Request payload validation failed."
    assert "errors" in payload["error"]["details"]
    assert payload["request_id"] is None

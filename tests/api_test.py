"""API tests for service bootstrap endpoints."""

from fastapi import APIRouter
from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app
from contentcreajudge.core.errors import DomainValidationError


def test_root_endpoint_returns_discovery_payload() -> None:
    """The root endpoint should expose basic API navigation details."""
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service"] == "contentcreajudge"
    assert payload["status"] == "ok"
    assert payload["endpoints"]["health"] == "/health"
    assert payload["endpoints"]["evaluations"] == "/api/v1/evaluations"


def test_health_endpoint_returns_ok_status() -> None:
    """The health endpoint should confirm the API is running."""
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_endpoint_returns_service_metadata() -> None:
    """The health endpoint should expose stable service metadata."""
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.json()["service"] == "contentcreajudge"
    assert response.json()["version"]


def test_evaluations_endpoint_accepts_v1_payload_shape() -> None:
    """The evaluations endpoint should already accept the minimal V1 payload."""
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/evaluations",
        json={
            "content": "Sample editorial content.",
            "profile": "default",
            "request_id": "req-001",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "accepted"
    assert payload["received_profile"] == "default"
    assert payload["request_id"] == "req-001"


def test_evaluations_endpoint_rejects_unknown_fields() -> None:
    """The evaluations endpoint should keep the V1 contract explicit."""
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/evaluations",
        json={
            "content": "Sample editorial content.",
            "profile": "default",
            "unexpected": "value",
        },
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "request_validation_error"
    assert payload["error"]["message"] == "Request payload validation failed."
    assert "errors" in payload["error"]["details"]
    assert payload["request_id"] is None


def test_domain_errors_use_standard_error_envelope() -> None:
    """Application-specific errors should be converted into stable JSON payloads."""
    app = create_app()
    router = APIRouter()

    @router.get("/_test/domain-error")
    def raise_domain_error() -> None:
        raise DomainValidationError(
            "Profile is not allowed for this workflow.",
            details={"profile": "legacy"},
        )

    app.include_router(router)
    client = TestClient(app)

    response = client.get("/_test/domain-error")

    assert response.status_code == 422
    payload = response.json()
    assert payload == {
        "error": {
            "code": "domain_validation_error",
            "message": "Profile is not allowed for this workflow.",
            "details": {"profile": "legacy"},
        },
        "request_id": None,
    }


def test_unexpected_errors_use_standard_error_envelope() -> None:
    """Unexpected exceptions should still return a stable API error response."""
    app = create_app()
    router = APIRouter()

    @router.get("/_test/unexpected-error")
    def raise_unexpected_error() -> None:
        raise RuntimeError("boom")

    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/_test/unexpected-error")

    assert response.status_code == 500
    payload = response.json()
    assert payload == {
        "error": {
            "code": "internal_server_error",
            "message": "An unexpected internal server error occurred.",
            "details": None,
        },
        "request_id": None,
    }

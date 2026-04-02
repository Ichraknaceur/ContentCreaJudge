"""API tests for service bootstrap endpoints."""

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app


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

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app
from contentcreajudge.api.judges.length import LengthJudgeRequestPayload


def test_evaluate_length_judge_endpoint_returns_flow_result() -> None:
    """Return the length flow result from the API endpoint."""
    app = create_app()
    client = TestClient(app)

    payload = {
        "content": "Bonjour le monde",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "request_id": "req-123",
    }

    flow_result = {
        "message": "Length flow complete.",
        "judge_result": {
            "dimension": "length",
            "status": "pass",
            "score": 100,
        },
    }

    with patch(
        "contentcreajudge.api.judges.length.execute_length_flow",
        return_value=flow_result,
    ) as mock_execute:
        response = client.post("/api/v1/judges/length/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json() == flow_result
    mock_execute.assert_called_once_with(payload)


def test_evaluate_length_judge_endpoint_uses_default_profile() -> None:
    """Use the default profile when the request omits one."""
    app = create_app()
    client = TestClient(app)

    payload = {
        "content": "Bonjour le monde",
        "context": {
            "content_type": "articles",
            "expected_length": "SIMPLE",
        },
    }

    flow_result = {
        "message": "Length flow complete.",
    }

    expected_model_dump = {
        "content": "Bonjour le monde",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "SIMPLE",
            "locale": None,
        },
        "request_id": None,
    }

    with patch(
        "contentcreajudge.api.judges.length.execute_length_flow",
        return_value=flow_result,
    ) as mock_execute:
        response = client.post("/api/v1/judges/length/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json() == flow_result
    mock_execute.assert_called_once_with(expected_model_dump)


def test_evaluate_length_judge_endpoint_rejects_extra_fields() -> None:
    """Reject payloads that include unknown fields."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/judges/length/evaluate",
        json={
            "content": "Bonjour",
            "context": {
                "content_type": "articles",
                "expected_length": "SIMPLE",
            },
            "unexpected_field": "not allowed",
        },
    )

    assert response.status_code == 422


def test_evaluate_length_judge_endpoint_rejects_missing_context() -> None:
    """Reject payloads that omit the required context."""
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/judges/length/evaluate",
        json={
            "content": "Bonjour",
        },
    )

    assert response.status_code == 422


def test_length_judge_request_payload_model_dump() -> None:
    """Serialize the length judge request payload with defaults."""
    payload = LengthJudgeRequestPayload(
        content="Bonjour",
        context={
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
    )

    assert payload.model_dump() == {
        "content": "Bonjour",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "request_id": None,
    }

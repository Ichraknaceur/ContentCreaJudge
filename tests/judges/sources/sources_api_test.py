from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app


def test_sources_judge_endpoint_returns_result() -> None:
    client = TestClient(create_app())

    payload = {
        "content": (
            '<p>Selon <a href="https://example.com/report" '
            'target="_blank" rel="noopener noreferrer">Example Report</a>, '
            "les sources doivent être vérifiées.</p>"
        ),
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
            "require_sources": True,
        },
    }

    with patch(
        "contentcreajudge.application.judge_flow.sources_flow.validate_source_urls"
    ) as mock_validate:
        mock_validate.return_value = [
            {
                "url": "https://example.com/report",
                "is_valid_format": True,
                "has_tracking_parameters": False,
                "tracking_parameters": [],
                "network_status": "reachable",
                "http_status_code": 200,
                "error": None,
            }
        ]

        response = client.post("/api/v1/judges/sources/evaluate", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["judge_result"]["dimension"] == "sources"
    assert data["judge_result"]["status"] == "pass"
    assert data["aggregation"]["status"] == "pass"


def test_sources_judge_endpoint_rejects_extra_payload_field() -> None:
    client = TestClient(create_app())

    payload = {
        "content": "<p>Test</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
        },
        "unexpected": "not allowed",
    }

    response = client.post("/api/v1/judges/sources/evaluate", json=payload)

    assert response.status_code == 422
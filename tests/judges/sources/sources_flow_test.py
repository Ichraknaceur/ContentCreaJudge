from __future__ import annotations

from unittest.mock import patch

from contentcreajudge.application.judge_flow.sources_flow import (
    execute_sources_flow,
)


def test_execute_sources_flow_passes_with_valid_source() -> None:
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

        result = execute_sources_flow(payload)

    assert result["rule_resolution"]["enabled_judges"] == ["sources"]
    assert result["preprocessing"]["external_links_count"] == 1
    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"
    assert result["aggregation"]["score"] == 100


def test_execute_sources_flow_fails_with_raw_url() -> None:
    payload = {
        "content": "<p>Voir cette source : https://example.com/report</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
            "require_sources": True,
        },
    }

    result = execute_sources_flow(payload)

    assert result["preprocessing"]["raw_urls_count"] == 1
    assert result["judge_result"]["status"] == "fail"
    assert result["aggregation"]["status"] == "fail"


def test_execute_sources_flow_raises_error_when_context_is_not_dict() -> None:
    payload = {
        "content": "<p>Test</p>",
        "profile": "default",
        "context": "invalid",
    }

    try:
        execute_sources_flow(payload)
    except ValueError as exc:
        assert str(exc) == "context must be a dictionary."
    else:
        raise AssertionError("Expected ValueError was not raised.")
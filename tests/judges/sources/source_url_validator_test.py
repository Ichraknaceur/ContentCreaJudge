from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import httpx

from contentcreajudge.adapters.sources.source_url_validator import (
    validate_source_url,
    validate_source_urls,
)

NETWORK_RULES = {
    "enabled": True,
    "timeout_seconds": 5,
    "follow_redirects": True,
    "method_priority": ["HEAD", "GET"],
    "allowed_http_status_codes": [200, 301, 302],
    "forbidden_http_status_codes": [400, 401, 403, 404, 410, 500, 502, 503],
}

FORBIDDEN_PARAMS = [
    "utm_*",
    "ref",
    "trk",
    "src",
    "source",
    "campaign",
    "mc_cid",
    "mc_eid",
    "gclid",
    "fbclid",
    "msclkid",
]


def test_validate_source_url_detects_invalid_format() -> None:
    """Verify that validate source url detects invalid format."""
    result = asyncio.run(
        validate_source_url(
            client=AsyncMock(),
            url="example.com/report",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["is_valid_format"] is False
    assert result["has_allowed_scheme"] is False
    assert result["network_status"] == "not_checked"
    assert result["error"] == "invalid_url_format"


def test_validate_source_url_detects_empty_url() -> None:
    """Verify that validate source url detects empty url."""
    result = asyncio.run(
        validate_source_url(
            client=AsyncMock(),
            url="   ",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["url"] == ""
    assert result["is_valid_format"] is False
    assert result["has_allowed_scheme"] is False
    assert result["network_status"] == "not_checked"
    assert result["error"] == "empty_url"


def test_validate_source_url_detects_tracking_parameters() -> None:
    """Verify that validate source url detects tracking parameters."""
    client = AsyncMock()
    response = Mock()
    response.status_code = 200
    response.url = "https://example.com/report?utm_source=linkedin"
    client.head.return_value = response

    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/report?utm_source=linkedin",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["is_valid_format"] is True
    assert result["has_tracking_parameters"] is True
    assert result["tracking_parameters"] == ["utm_source"]
    assert result["network_status"] == "reachable"


def test_validate_source_url_marks_reachable_url() -> None:
    """Verify that validate source url marks reachable url."""
    client = AsyncMock()
    response = Mock()
    response.status_code = 200
    response.url = "https://example.com/report"
    client.head.return_value = response

    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/report",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["is_valid_format"] is True
    assert result["network_status"] == "reachable"
    assert result["http_status_code"] == 200
    assert result["error"] is None


def test_validate_source_url_marks_404_as_unreachable() -> None:
    """Verify that validate source url marks 404 as unreachable."""
    client = AsyncMock()
    response = Mock()
    response.status_code = 404
    response.url = "https://example.com/missing"
    client.head.return_value = response

    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/missing",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["network_status"] == "unreachable"
    assert result["http_status_code"] == 404
    assert result["error"] == "http_status_404"


def test_validate_source_url_skips_network_when_disabled() -> None:
    """Verify that validate source url skips network when disabled."""
    result = asyncio.run(
        validate_source_url(
            client=AsyncMock(),
            url="https://example.com/report",
            network_rules={"enabled": False},
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["is_valid_format"] is True
    assert result["network_status"] == "disabled"
    assert result["http_status_code"] is None
    assert result["error"] is None


def test_validate_source_url_returns_unknown_for_unhandled_http_status() -> None:
    """Verify that validate source url returns unknown for unhandled http status."""
    client = AsyncMock()
    response = Mock()
    response.status_code = 418
    response.url = "https://example.com/teapot"
    client.head.return_value = response

    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/teapot",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["network_status"] == "unknown"
    assert result["http_status_code"] == 418
    assert result["error"] == "unhandled_http_status_418"


def test_validate_source_url_returns_unknown_on_timeout() -> None:
    """Verify that validate source url returns unknown on timeout."""
    client = AsyncMock()
    client.head.side_effect = httpx.TimeoutException("timeout")
    client.get.side_effect = httpx.TimeoutException("timeout")
    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/report",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["network_status"] == "unknown"
    assert result["error"] == "timeout"


def test_validate_source_url_returns_unknown_on_ssl_error() -> None:
    """Verify that validate source url returns unknown on ssl error."""

    class FakeSSLError(httpx.TransportError):
        """Transport error whose name exercises SSL normalization."""

    client = AsyncMock()
    client.head.side_effect = FakeSSLError("ssl")
    client.get.side_effect = FakeSSLError("ssl")
    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/report",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["network_status"] == "unknown"
    assert result["error"] == "ssl_error"


def test_validate_source_url_returns_unknown_on_connection_error() -> None:
    """Verify that validate source url returns unknown on connection error."""
    client = AsyncMock()
    client.head.side_effect = httpx.ConnectError("connection failed")
    client.get.side_effect = httpx.ConnectError("connection failed")
    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/report",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["network_status"] == "unknown"
    assert result["error"] == "connection_error"


def test_validate_source_url_returns_unknown_on_generic_request_exception() -> None:
    """Verify that validate source url returns unknown on generic request exception."""
    client = AsyncMock()
    client.head.side_effect = httpx.RequestError("boom")
    client.get.side_effect = httpx.RequestError("boom")
    result = asyncio.run(
        validate_source_url(
            client=client,
            url="https://example.com/report",
            network_rules=NETWORK_RULES,
            forbidden_query_parameters=FORBIDDEN_PARAMS,
        ),
    )

    assert result["network_status"] == "unknown"
    assert result["error"] == "request_error:RequestError"


def test_validate_source_urls_validates_multiple_urls() -> None:
    """Verify that validate source urls validates multiple urls."""
    with patch(
        "contentcreajudge.adapters.sources.source_url_validator.validate_source_url",
        new_callable=AsyncMock,
    ) as mock_validate:
        mock_validate.side_effect = [
            {"url": "https://example.com/one", "network_status": "reachable"},
            {"url": "https://example.com/two", "network_status": "unreachable"},
        ]

        results = asyncio.run(
            validate_source_urls(
                urls=["https://example.com/one", "https://example.com/two"],
                network_rules=NETWORK_RULES,
                forbidden_query_parameters=FORBIDDEN_PARAMS,
            ),
        )

    assert results == [
        {"url": "https://example.com/one", "network_status": "reachable"},
        {"url": "https://example.com/two", "network_status": "unreachable"},
    ]
    assert mock_validate.call_count == 2

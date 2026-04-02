"""HTTP client helpers for the Streamlit UI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPSConnection
from urllib.parse import urlparse

HTTP_SUCCESS_MIN = 200
HTTP_REDIRECT_MIN = 300


@dataclass(frozen=True)
class ApiCallResult:
    """Represent the result of an API call from the Streamlit UI."""

    ok: bool
    status_code: int | None
    payload: dict[str, object]
    error: str | None = None


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
) -> ApiCallResult:
    """Perform a JSON HTTP request against the backend."""
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        return ApiCallResult(
            ok=False,
            status_code=None,
            payload={},
            error="Unsupported API URL scheme.",
        )

    request_data: bytes | None = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        request_data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    path = parsed_url.path or "/"
    if parsed_url.query:
        path = f"{path}?{parsed_url.query}"

    connection_cls = (
        HTTPSConnection if parsed_url.scheme == "https" else HTTPConnection
    )
    connection = connection_cls(parsed_url.netloc, timeout=5)

    try:
        connection.request(
            method=method,
            url=path,
            body=request_data,
            headers=headers,
        )
        response = connection.getresponse()
        raw_payload = response.read().decode("utf-8")
        parsed_payload = json.loads(raw_payload) if raw_payload else {}
        status_code = response.status
        is_success = HTTP_SUCCESS_MIN <= status_code < HTTP_REDIRECT_MIN
        return ApiCallResult(
            ok=is_success,
            status_code=status_code,
            payload=parsed_payload,
            error=None if is_success else f"HTTP {status_code}",
        )
    except OSError as error:
        return ApiCallResult(
            ok=False,
            status_code=None,
            payload={},
            error=f"API unreachable: {error.strerror or error}",
        )
    finally:
        connection.close()

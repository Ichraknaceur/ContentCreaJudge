"""Network and URL validation adapter for the sources judge."""

from __future__ import annotations

from fnmatch import fnmatch
from urllib.parse import parse_qs, urlparse

import requests


def _has_allowed_scheme(url: str) -> bool:
    """Check if the URL uses an allowed HTTP scheme."""
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _detect_tracking_parameters(
    url: str,
    forbidden_parameters: list[str],
) -> list[str]:
    """Return forbidden tracking parameters found in the URL."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    detected: list[str] = []

    for parameter_name in query_params:
        for forbidden_pattern in forbidden_parameters:
            if fnmatch(parameter_name, forbidden_pattern):
                detected.append(parameter_name)

    return detected


def _request_url(
    url: str,
    method: str,
    timeout_seconds: int,
    follow_redirects: bool,
) -> requests.Response:
    """Execute one HTTP request with the requested method."""
    if method.upper() == "HEAD":
        return requests.head(
            url,
            timeout=timeout_seconds,
            allow_redirects=follow_redirects,
        )

    return requests.get(
        url,
        timeout=timeout_seconds,
        allow_redirects=follow_redirects,
    )


def validate_source_url(
    url: str,
    network_rules: dict[str, object],
    forbidden_query_parameters: list[str],
) -> dict[str, object]:
    """Validate one source URL using deterministic checks and optional network calls."""

    normalized_url = url.strip()

    result: dict[str, object] = {
        "url": normalized_url,
        "is_valid_format": False,
        "has_allowed_scheme": False,
        "tracking_parameters": [],
        "has_tracking_parameters": False,
        "network_status": "not_checked",
        "http_status_code": None,
        "final_url": normalized_url,
        "error": None,
    }

    if not normalized_url:
        result["error"] = "empty_url"
        return result

    has_allowed_scheme = _has_allowed_scheme(normalized_url)
    result["has_allowed_scheme"] = has_allowed_scheme
    result["is_valid_format"] = has_allowed_scheme

    tracking_parameters = _detect_tracking_parameters(
        normalized_url,
        forbidden_query_parameters,
    )
    result["tracking_parameters"] = tracking_parameters
    result["has_tracking_parameters"] = len(tracking_parameters) > 0

    if not has_allowed_scheme:
        result["network_status"] = "not_checked"
        result["error"] = "invalid_url_format"
        return result

    if not bool(network_rules.get("enabled", False)):
        result["network_status"] = "disabled"
        return result

    timeout_seconds = int(network_rules.get("timeout_seconds", 5))
    follow_redirects = bool(network_rules.get("follow_redirects", True))
    method_priority = network_rules.get("method_priority", ["HEAD", "GET"])
    allowed_status_codes = set(network_rules.get("allowed_http_status_codes", []))
    forbidden_status_codes = set(network_rules.get("forbidden_http_status_codes", []))
    unknown_status_codes = set(network_rules.get("unknown_http_status_codes", []))

    last_error: str | None = None

    for method in method_priority:
        try:
            response = _request_url(
                normalized_url,
                str(method),
                timeout_seconds,
                follow_redirects,
            )

            status_code = response.status_code
            result["http_status_code"] = status_code
            result["final_url"] = response.url

            if status_code in allowed_status_codes:
                result["network_status"] = "reachable"
                result["error"] = None
                return result

            if status_code in forbidden_status_codes:
                result["network_status"] = "unreachable"
                result["error"] = f"http_status_{status_code}"
                return result
            
            if status_code in unknown_status_codes:
                result["network_status"] = "unknown"
                result["error"] = f"http_status_{status_code}"
                return result

            result["network_status"] = "unknown"
            result["error"] = f"unhandled_http_status_{status_code}"
            return result

        except requests.exceptions.Timeout:
            last_error = "timeout"

        except requests.exceptions.SSLError:
            last_error = "ssl_error"

        except requests.exceptions.ConnectionError:
            last_error = "connection_error"

        except requests.exceptions.RequestException as exc:
            last_error = f"request_error:{exc.__class__.__name__}"

    result["network_status"] = "unknown"
    result["error"] = last_error or "unknown_network_error"
    return result


def validate_source_urls(
    urls: list[str],
    network_rules: dict[str, object],
    forbidden_query_parameters: list[str],
) -> list[dict[str, object]]:
    """Validate multiple source URLs."""
    return [
        validate_source_url(
            url=url,
            network_rules=network_rules,
            forbidden_query_parameters=forbidden_query_parameters,
        )
        for url in urls
    ]
"""Network and URL validation adapter for the sources judge."""

from __future__ import annotations

import asyncio
from fnmatch import fnmatch
from urllib.parse import parse_qs, urlparse

import httpx

_ALLOWED_METHODS = {"HEAD", "GET"}


def _normalize_method_priority(method_priority: object) -> list[str]:
    """Validate and normalize configured HTTP methods."""
    if not isinstance(method_priority, list):
        raise TypeError("network_rules.method_priority must be a list.")

    normalized_methods: list[str] = []

    for method in method_priority:
        normalized_method = str(method).upper().strip()

        if normalized_method not in _ALLOWED_METHODS:
            raise ValueError(
                f"Unsupported HTTP method in method_priority: {normalized_method}. "
                "Allowed methods are: HEAD, GET.",
            )

        normalized_methods.append(normalized_method)

    if not normalized_methods:
        raise ValueError("network_rules.method_priority must not be empty.")

    return normalized_methods


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

    detected.extend(
        parameter_name
        for parameter_name in query_params
        for forbidden_pattern in forbidden_parameters
        if fnmatch(parameter_name, forbidden_pattern)
    )

    return detected


async def _request_url(
    client: httpx.AsyncClient,
    url: str,
    method: str,
) -> httpx.Response:
    """Execute one async HTTP request with the requested method."""
    normalized_method = method.upper().strip()

    if normalized_method == "HEAD":
        return await client.head(url)

    if normalized_method == "GET":
        return await client.get(url)

    raise ValueError(f"Unsupported HTTP method: {normalized_method}")


def _build_initial_result(normalized_url: str) -> dict[str, object]:
    """Create the default URL validation payload."""
    return {
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


def _apply_network_response(
    result: dict[str, object],
    response: httpx.Response,
    allowed_status_codes: set[object],
    forbidden_status_codes: set[object],
    unknown_status_codes: set[object],
) -> dict[str, object]:
    """Apply an HTTP response to the validation payload."""
    status_code = response.status_code
    result["http_status_code"] = status_code
    result["final_url"] = str(response.url)

    if status_code in allowed_status_codes:
        result["network_status"] = "reachable"
        result["error"] = None
    elif status_code in forbidden_status_codes:
        result["network_status"] = "unreachable"
        result["error"] = f"http_status_{status_code}"
    elif status_code in unknown_status_codes:
        result["network_status"] = "unknown"
        result["error"] = f"http_status_{status_code}"
    else:
        result["network_status"] = "unknown"
        result["error"] = f"unhandled_http_status_{status_code}"

    return result


def _network_error_name(exc: httpx.TransportError) -> str:
    """Return the normalized error name for a transport failure."""
    if "ssl" in exc.__class__.__name__.lower():
        return "ssl_error"
    return f"request_error:{exc.__class__.__name__}"


async def validate_source_url(
    client: httpx.AsyncClient,
    url: str,
    network_rules: dict[str, object],
    forbidden_query_parameters: list[str],
) -> dict[str, object]:
    """Validate one source URL using deterministic checks and optional network calls."""
    normalized_url = url.strip()
    result = _build_initial_result(normalized_url)

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

    method_priority = _normalize_method_priority(
        network_rules.get("method_priority", ["HEAD", "GET"]),
    )
    allowed_status_codes = set(network_rules.get("allowed_http_status_codes", []))
    forbidden_status_codes = set(network_rules.get("forbidden_http_status_codes", []))
    unknown_status_codes = set(network_rules.get("unknown_http_status_codes", []))

    last_error: str | None = None

    for method in method_priority:
        try:
            response = await _request_url(
                client=client,
                url=normalized_url,
                method=str(method),
            )

        except httpx.TimeoutException:
            last_error = "timeout"
        except httpx.ConnectError:
            last_error = "connection_error"
        except httpx.TransportError as exc:
            last_error = _network_error_name(exc)
        except httpx.RequestError as exc:
            last_error = f"request_error:{exc.__class__.__name__}"
        else:
            return _apply_network_response(
                result=result,
                response=response,
                allowed_status_codes=allowed_status_codes,
                forbidden_status_codes=forbidden_status_codes,
                unknown_status_codes=unknown_status_codes,
            )

    result["network_status"] = "unknown"
    result["error"] = last_error or "unknown_network_error"
    return result


async def validate_source_urls(
    urls: list[str],
    network_rules: dict[str, object],
    forbidden_query_parameters: list[str],
) -> list[dict[str, object]]:
    """Validate multiple source URLs concurrently."""
    timeout_seconds = int(network_rules.get("timeout_seconds", 5))
    follow_redirects = bool(network_rules.get("follow_redirects", True))
    max_concurrency = int(network_rules.get("max_concurrency", 5))

    semaphore = asyncio.Semaphore(max_concurrency)

    async with httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=follow_redirects,
    ) as client:

        async def validate_with_limit(url: str) -> dict[str, object]:
            async with semaphore:
                return await validate_source_url(
                    client=client,
                    url=url,
                    network_rules=network_rules,
                    forbidden_query_parameters=forbidden_query_parameters,
                )

        return await asyncio.gather(
            *(validate_with_limit(url) for url in urls),
        )

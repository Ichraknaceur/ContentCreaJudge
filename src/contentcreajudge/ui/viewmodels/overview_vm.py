"""View model helpers for the Overview screen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contentcreajudge.ui.services.api_client import ApiCallResult


@dataclass(frozen=True)
class OverviewViewModel:
    """Carry precomputed values for the overview and hero screens."""

    endpoint_count: int
    health_label: str
    health_note: str
    version: str
    status_label: str
    status_note: str
    status_message: str


def build_overview_view_model(
    *,
    health_result: ApiCallResult,
    root_result: ApiCallResult,
) -> OverviewViewModel:
    """Build the overview view model from API results."""
    endpoint_count = 0
    if root_result.ok:
        endpoints = root_result.payload.get("endpoints")
        if isinstance(endpoints, dict):
            endpoint_count = len(endpoints)

    health_label = "Connected" if health_result.ok else "Offline"
    health_note = health_result.error or "Health endpoint reachable."
    version = "Unavailable"
    if health_result.ok:
        version = str(health_result.payload.get("version", "unknown"))

    status_label = "API linked" if health_result.ok else "API offline"
    status_note = (
        "Backend and Streamlit are synchronized."
        if health_result.ok
        else "Launch `make run` to reconnect the workspace."
    )
    status_message = (
        "Backend API is reachable from the UI."
        if health_result.ok
        else (
            "Backend API is not reachable yet. The workspace remains usable "
            "for composing demo payloads."
        )
    )
    return OverviewViewModel(
        endpoint_count=endpoint_count,
        health_label=health_label,
        health_note=health_note,
        version=version,
        status_label=status_label,
        status_note=status_note,
        status_message=status_message,
    )

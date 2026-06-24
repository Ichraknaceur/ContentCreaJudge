"""Shared API error response models."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorDetails(BaseModel):
    """Describe one normalized API error payload."""

    code: str
    message: str
    details: dict[str, object] | None = None


class ErrorResponse(BaseModel):
    """Top-level API error envelope."""

    error: ErrorDetails
    request_id: str | None = None

"""Evaluation API endpoints."""

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


class EvaluationRequestPayload(BaseModel):
    """Minimal V1 request payload for an editorial evaluation."""

    content: str
    profile: str
    content_title: str | None = None
    content_type: str | None = None
    channel: str | None = None
    locale: str | None = None
    target_keywords: list[str] = []
    declared_sources: list[str] = []
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


class EvaluationPlaceholderResponse(BaseModel):
    """Placeholder response for the future evaluation workflow."""

    status: str
    message: str
    received_profile: str
    request_id: str | None
    next_step: str


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def create_evaluation(
    payload: EvaluationRequestPayload,
) -> EvaluationPlaceholderResponse:
    """Accept an evaluation request and return a placeholder V1 response."""
    return EvaluationPlaceholderResponse(
        status="accepted",
        message=(
            "Evaluation orchestration is not implemented yet. "
            "This endpoint is ready to receive V1 payloads."
        ),
        received_profile=payload.profile,
        request_id=payload.request_id,
        next_step="Connect preprocessing, judge orchestration, and aggregation.",
    )

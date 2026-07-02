"""Global evaluation API endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response, status  # noqa: TC002
from pydantic import BaseModel, ConfigDict, Field

from contentcreajudge.application.orchestration.orchestrator import (
    execute_global_evaluation,
)

router = APIRouter(prefix="/api/v1/evaluations", tags=["evaluations"])


class GlobalEvaluationContext(BaseModel):
    """Context needed by the enabled judges."""

    content_type: str
    expected_length: str | None = None
    locale: str | None = None

    organization_website: str | None = None
    expected_cta: str | None = None
    funnel_stage: str | None = None
    evergreen: bool | None = None

    main_keyword: str | None = None
    secondary_keywords: list[str] = Field(default_factory=list)
    expected_structure: str | None = None
    expected_outline_html: str | None = None


class GlobalEvaluationRequestPayload(BaseModel):
    """Request body for running a global evaluation."""

    content: str
    profile: str = "default"
    context: GlobalEvaluationContext | None = None
    enabled_judges: list[str] | None = None
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("", status_code=status.HTTP_200_OK)
async def evaluate_global_content(
    payload: GlobalEvaluationRequestPayload,
    response: Response,
) -> dict[str, Any]:
    """Execute the global evaluation orchestration."""
    if payload.context is None:
        response.status_code = status.HTTP_202_ACCEPTED
        return {
            "status": "accepted",
            "message": (
                "Evaluation orchestration is not implemented yet. "
                "This endpoint is ready to receive V1 payloads."
            ),
            "received_profile": payload.profile,
            "request_id": payload.request_id,
            "next_step": "Connect preprocessing, judge orchestration, and aggregation.",
        }

    return await execute_global_evaluation(payload.model_dump())

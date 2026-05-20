"""Dedicated API endpoint for the CTA judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.cta_flow import execute_cta_flow

router = APIRouter(prefix="/api/v1/judges/cta", tags=["judges", "cta"])


class CtaJudgeContext(BaseModel):
    """Context required for running the CTA judge."""

    content_type: str
    funnel_stage: str
    expected_cta: str | None = None
    content_purpose: str | None = None
    language: str | None = "fr"


class CtaJudgeRequestPayload(BaseModel):
    """Request body for running the CTA judge."""

    content: str
    profile: str = "default"
    context: CtaJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_cta_judge(payload: CtaJudgeRequestPayload) -> dict[str, object]:
    """Execute the CTA flow."""
    return execute_cta_flow(payload.model_dump())

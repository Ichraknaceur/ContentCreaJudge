"""Dedicated API endpoint for the tone judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.tone_flow import execute_tone_flow

router = APIRouter(prefix="/api/v1/judges/tone", tags=["judges", "tone"])


class ToneJudgeContext(BaseModel):
    """Context required to run the tone judge."""

    expected_tone: str
    organization_voice: str | None = None
    organization_voice_description: str | None = None
    writing_style: str | None = None
    funnel_stage: str | None = None
    persona: str | None = None
    content_type: str | None = None
    brief: str | None = None
    locale: str | None = None


class ToneJudgeRequestPayload(BaseModel):
    """Request body for running the tone judge."""

    content: str
    profile: str = "default"
    context: ToneJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_tone_judge(payload: ToneJudgeRequestPayload) -> dict[str, object]:
    """Execute the tone flow."""
    return execute_tone_flow(payload.model_dump())

"""Dedicated API endpoint for the length judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.length_flow import execute_length_flow

router = APIRouter(prefix="/api/v1/judges/length", tags=["judges", "length"])


class LengthJudgeContext(BaseModel):
    content_type: str
    expected_length: str
    locale: str | None = None


class LengthJudgeRequestPayload(BaseModel):
    """Request body for running the length judge"""

    content: str
    profile: str = "default"
    context: LengthJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_length_judge(payload: LengthJudgeRequestPayload) -> dict[str, object]:
    """Execute the length flow"""
    return execute_length_flow(payload.model_dump())

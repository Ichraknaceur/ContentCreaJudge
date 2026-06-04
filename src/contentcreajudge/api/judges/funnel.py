"""Dedicated API endpoint for the funnel judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.funnel_flow import execute_funnel_flow

router = APIRouter(prefix="/api/v1/judges/funnel", tags=["judges", "funnel"])


class FunnelJudgeContext(BaseModel):
    """Context required for running the funnel judge."""

    expected_funnel: str


class FunnelJudgeRequestPayload(BaseModel):
    """Request body for running the funnel judge."""

    content: str
    profile: str = "default"
    context: FunnelJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_funnel_judge(payload: FunnelJudgeRequestPayload) -> dict[str, object]:
    """Execute the funnel flow."""
    return execute_funnel_flow(payload.model_dump())

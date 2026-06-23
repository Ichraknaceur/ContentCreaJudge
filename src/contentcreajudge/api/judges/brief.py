"""Dedicated API endpoint for the Brief judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.brief_flow import execute_brief_flow

router = APIRouter(prefix="/api/v1/judges/brief", tags=["judges", "brief"])


class BriefJudgeContext(BaseModel):
    """Context required for running the Brief judge."""

    brief: str


class BriefJudgeRequestPayload(BaseModel):
    """Request body for running the Brief judge."""

    content: str
    profile: str = "default"
    context: BriefJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_brief_judge(payload: BriefJudgeRequestPayload) -> dict[str, object]:
    """Execute the Brief judge flow."""
    return execute_brief_flow(payload.model_dump())

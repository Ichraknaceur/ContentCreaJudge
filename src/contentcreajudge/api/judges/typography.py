"""Dedicated API endpoint for the typography judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.typography_flow import (
    execute_typography_flow,
)

router = APIRouter(prefix="/api/v1/judges/typography", tags=["judges", "typography"])


class TypographyJudgeContext(BaseModel):
    locale: str


class TypographyJudgeRequestPayload(BaseModel):
    """Request body for running the typography judge."""

    content: str
    profile: str = "default"
    context: TypographyJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_typography_judge(
    payload: TypographyJudgeRequestPayload,
) -> dict[str, object]:
    """Execute the typography flow."""
    return execute_typography_flow(payload.model_dump())
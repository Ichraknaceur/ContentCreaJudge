"""Dedicated API endpoint for the evergreen judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.evergreen_flow import (
    execute_evergreen_flow,
)

router = APIRouter(prefix="/api/v1/judges/evergreen", tags=["judges", "evergreen"])


class EvergreenJudgeContext(BaseModel):
    """Evaluation context for the evergreen judge."""

    evergreen: bool = False
    locale: str | None = "fr-FR"
    brief: str | None = None


class EvergreenJudgeRequestPayload(BaseModel):
    """Request body for running the evergreen judge."""

    content: str = ""
    profile: str = "default"
    context: EvergreenJudgeContext = EvergreenJudgeContext()
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_evergreen_judge(
    payload: EvergreenJudgeRequestPayload,
) -> dict[str, object]:
    """Execute the evergreen flow."""
    return execute_evergreen_flow(payload.model_dump())

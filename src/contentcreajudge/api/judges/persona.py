"""Dedicated API endpoint for the persona judge."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.persona_flow import (
    execute_persona_flow,
)

router = APIRouter(
    prefix="/api/v1/judges/persona",
    tags=["judges", "persona"],
)


class PersonaJudgeContext(BaseModel):
    """Context required to run the persona judge."""

    personas: list[dict[str, Any]]
    expected_persona_id: str
    business_type: str
    content_type: str | None = None
    funnel_stage: str | None = None
    locale: str | None = None
    providers: list[str] | None = None

    model_config = ConfigDict(extra="forbid")


class PersonaJudgeRequestPayload(BaseModel):
    """Request body for running the persona judge."""

    content: str
    profile: str = "default"
    context: PersonaJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post(
    "/evaluate",
    status_code=status.HTTP_200_OK,
)
def evaluate_persona_judge(
    payload: PersonaJudgeRequestPayload,
) -> dict[str, object]:
    """Execute the persona flow."""
    return execute_persona_flow(payload.model_dump())

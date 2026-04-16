"""Dedicated API endpoint for the structure judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.structure_flow import execute_structure_flow


router = APIRouter(prefix="/api/v1/judges/structure", tags=["judges", "structure"])


class StructureJudgeContext(BaseModel):
    expected_outline_html: str
    locale: str | None = None


class StructureJudgeRequestPayload(BaseModel):
    """Request body for running the structure judge."""

    content: str
    profile: str = "default"
    context: StructureJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_structure_judge(
    payload: StructureJudgeRequestPayload,
) -> dict[str, object]:
    """Execute the structure flow."""
    return execute_structure_flow(payload.model_dump())
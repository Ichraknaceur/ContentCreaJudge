"""Dedicated API endpoint for the sources judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.sources_flow import execute_sources_flow

router = APIRouter(prefix="/api/v1/judges/sources", tags=["judges", "sources"])


class SourcesJudgeContext(BaseModel):
    """Context required for running the sources judge."""

    content_type: str
    expected_length: str
    organization_website: str = "https://contentcrea.com"
    locale: str | None = None
    require_sources: bool | None = None


class SourcesJudgeRequestPayload(BaseModel):
    """Request body for running the sources judge."""

    content: str
    profile: str = "default"
    context: SourcesJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
async def evaluate_sources_judge(
    payload: SourcesJudgeRequestPayload,
) -> dict[str, object]:
    """Execute the sources flow."""
    return await execute_sources_flow(payload.model_dump())

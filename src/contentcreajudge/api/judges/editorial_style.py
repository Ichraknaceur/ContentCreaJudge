"""Dedicated API endpoint for the editorial style judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from contentcreajudge.application.judge_flow.editorial_style_flow import (
    execute_editorial_style_flow,
)

router = APIRouter(
    prefix="/api/v1/judges/editorial-style",
    tags=["judges", "editorial-style"],
)


class EditorialStylePayload(BaseModel):
    """Editorial style fields used by the judge."""

    writing_style: str | None = Field(default=None, alias="writingStyle")
    write_like_this: str | None = Field(default=None, alias="writeLikeThis")
    not_like_this: str | None = Field(default=None, alias="notLikeThis")

    model_config = ConfigDict(populate_by_name=True)


class EditorialStyleJudgeContext(BaseModel):
    """Optional context for editorial style evaluation."""

    content_type: str | None = None
    locale: str | None = None
    funnel_stage: str | None = None
    organization_name: str | None = None


class EditorialStyleJudgeRequestPayload(BaseModel):
    """Request body for running the editorial style judge."""

    content: str
    profile: str = "default"
    editorial_style: EditorialStylePayload
    context: EditorialStyleJudgeContext | None = None
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_editorial_style_judge(
    payload: EditorialStyleJudgeRequestPayload,
) -> dict[str, object]:
    """Execute the editorial style flow."""
    return execute_editorial_style_flow(payload.model_dump(by_alias=True))

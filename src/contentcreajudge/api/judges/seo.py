"""Dedicated API endpoint for the SEO judge."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from contentcreajudge.application.judge_flow.seo_flow import execute_seo_flow

router = APIRouter(prefix="/api/v1/judges/seo", tags=["judges", "seo"])


class SeoJudgeContext(BaseModel):
    """Context required to resolve and run the SEO judge."""

    content_type: str
    expected_length: str
    funnel_stage: str
    locale: str | None = None
    main_keyword: str
    secondary_keywords: list[str] = []
    long_tail_keywords: list[str] = []


class SeoJudgeRequestPayload(BaseModel):
    """Request body for running the SEO judge."""

    content: str
    profile: str = "default"
    context: SeoJudgeContext
    request_id: str | None = None

    model_config = ConfigDict(extra="forbid")


@router.post("/evaluate", status_code=status.HTTP_200_OK)
def evaluate_seo_judge(payload: SeoJudgeRequestPayload) -> dict[str, object]:
    """Execute the SEO flow."""
    return execute_seo_flow(payload.model_dump())

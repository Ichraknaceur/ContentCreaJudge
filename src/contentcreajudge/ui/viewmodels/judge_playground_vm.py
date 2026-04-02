"""View model helpers for the Judge Playground screen."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeWorkbenchItem:
    """Describe one judge workspace card in the UI."""

    key: str
    title: str
    summary: str
    endpoint: str
    status: str


def get_judge_workbench_items() -> list[JudgeWorkbenchItem]:
    """Return the judge catalog displayed in the UI."""
    return [
        JudgeWorkbenchItem(
            key="structure",
            title="Structure",
            summary="Validate editorial structure and section organization.",
            endpoint="/api/v1/judges/structure/evaluate",
            status="Scaffolded",
        ),
        JudgeWorkbenchItem(
            key="length",
            title="Length",
            summary="Validate target size, min and max content boundaries.",
            endpoint="/api/v1/judges/length/evaluate",
            status="Scaffolded",
        ),
        JudgeWorkbenchItem(
            key="typography",
            title="Typography",
            summary="Validate formatting and typographic hygiene.",
            endpoint="/api/v1/judges/typography/evaluate",
            status="Scaffolded",
        ),
        JudgeWorkbenchItem(
            key="evergreen",
            title="Evergreen",
            summary="Validate time-sensitive phrasing and durability rules.",
            endpoint="/api/v1/judges/evergreen/evaluate",
            status="Planned",
        ),
        JudgeWorkbenchItem(
            key="cta",
            title="CTA",
            summary="Validate presence and structure of calls to action.",
            endpoint="/api/v1/judges/cta/evaluate",
            status="Planned",
        ),
        JudgeWorkbenchItem(
            key="sources",
            title="Sources",
            summary="Validate source references and supporting links.",
            endpoint="/api/v1/judges/sources/evaluate",
            status="Planned",
        ),
        JudgeWorkbenchItem(
            key="seo",
            title="SEO",
            summary="Validate keyword presence and basic search constraints.",
            endpoint="/api/v1/judges/seo/evaluate",
            status="Planned",
        ),
    ]


def get_judge_by_key(key: str) -> JudgeWorkbenchItem:
    """Return a single judge workspace item by key."""
    for item in get_judge_workbench_items():
        if item.key == key:
            return item
    return get_judge_workbench_items()[0]

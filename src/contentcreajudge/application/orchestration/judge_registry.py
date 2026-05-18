"""Registry of judge flows available for global orchestration."""
# ruff: noqa: I001

from __future__ import annotations

from collections.abc import Callable

from contentcreajudge.application.judge_flow.length_flow import execute_length_flow
from contentcreajudge.application.judge_flow.seo_flow import execute_seo_flow
from contentcreajudge.application.judge_flow.typography_flow import (
    execute_typography_flow,
)


JudgeFlow = Callable[[dict[str, object]], dict[str, object]]


JUDGE_REGISTRY: dict[str, JudgeFlow] = {
    "length": execute_length_flow,
    "typography": execute_typography_flow,
    "seo": execute_seo_flow,
}


DEFAULT_ENABLED_JUDGES = ["length", "typography", "seo"]


def get_runnable_judges(
    enabled_judges: object,
) -> dict[str, JudgeFlow]:
    """Return the judge flows that can be executed."""
    selected_judges = (
        enabled_judges if isinstance(enabled_judges, list) else DEFAULT_ENABLED_JUDGES
    )

    return {
        judge_name: JUDGE_REGISTRY[judge_name]
        for judge_name in selected_judges
        if isinstance(judge_name, str) and judge_name in JUDGE_REGISTRY
    }

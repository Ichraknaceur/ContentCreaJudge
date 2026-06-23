"""Application orchestration for the Brief evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.brief_aggregator import aggregate_brief_result
from contentcreajudge.judges.brief.brief_judge import run_brief_judge
from contentcreajudge.preprocessing.brief_preprocessor import (
    preprocess_brief_content,
)
from contentcreajudge.rules.judges.brief.brief_resolver import resolve_brief_rules


def execute_brief_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the Brief judge flow."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    if not isinstance(context, dict):
        context = {}

    brief = str(context.get("brief", ""))

    resolved_brief_rules = resolve_brief_rules()

    preprocessed_content = preprocess_brief_content(
        article=content,
        brief=brief,
    )

    brief_result = run_brief_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_brief_rules,
    )

    aggregation_result = aggregate_brief_result(brief_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["brief"],
            "judge_rules": {
                "brief": resolved_brief_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": brief_result,
        "aggregation": aggregation_result,
        "message": (
            "Brief flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }

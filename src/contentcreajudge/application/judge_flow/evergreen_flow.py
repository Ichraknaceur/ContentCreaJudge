"""Application orchestration for the evergreen evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.evergreen_aggregator import (
    aggregate_evergreen_result,
)
from contentcreajudge.judges.evergreen.evergreen_judge import run_evergreen_judge
from contentcreajudge.preprocessing.evergreen_preprocessor import (
    preprocess_evergreen_content,
)
from contentcreajudge.rules.judges.evergreen.evergreen_resolver import (
    resolve_evergreen_rules,
)


def execute_evergreen_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the Evergreen judge flow with safe fallbacks."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")

    context_value = payload.get("context")
    context = context_value if isinstance(context_value, dict) else {}

    resolved_evergreen_rules = resolve_evergreen_rules(context)

    preprocessed_content = preprocess_evergreen_content(
        content=content,
        judge_rules=resolved_evergreen_rules,
    )

    evergreen_result = run_evergreen_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_evergreen_rules,
    )

    aggregation_result = aggregate_evergreen_result(evergreen_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["evergreen"],
            "judge_rules": {
                "evergreen": resolved_evergreen_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": evergreen_result,
        "aggregation": aggregation_result,
        "message": (
            "Evergreen flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }

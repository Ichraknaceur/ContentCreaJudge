"""Application orchestration for the editorial style evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.editorial_style_aggregator import (
    aggregate_editorial_style_result,
)
from contentcreajudge.judges.editorial_style.editorial_style_judge import (
    run_editorial_style_judge,
)
from contentcreajudge.preprocessing.editorial_style_preprocessor import (
    preprocess_editorial_style_content,
)
from contentcreajudge.rules.judges.editorial_style.editorial_style_resolver import (
    resolve_editorial_style_rules,
)


def execute_editorial_style_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the editorial style judge flow."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")

    editorial_style = payload.get("editorial_style") or {}
    context = payload.get("context") or {}

    if not isinstance(editorial_style, dict):
        editorial_style = {}

    if not isinstance(context, dict):
        context = {}

    resolved_editorial_style_rules = resolve_editorial_style_rules(context)

    preprocessed_content = preprocess_editorial_style_content(
        content=content,
        editorial_style=editorial_style,
    )

    judge_result = run_editorial_style_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_editorial_style_rules,
    )

    aggregation_result = aggregate_editorial_style_result(judge_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
            "editorial_style": editorial_style,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["editorial_style"],
            "judge_rules": {
                "editorial_style": resolved_editorial_style_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": judge_result,
        "aggregation": aggregation_result,
        "message": (
            "Editorial style flow complete: request, rule resolution, "
            "preprocessing, judge, aggregation, response."
        ),
    }

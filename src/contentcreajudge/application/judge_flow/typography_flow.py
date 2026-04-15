"""Application orchestration for the typography evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.typography_aggregator import (
    aggregate_typography_result,
)
from contentcreajudge.judges.typography.typography_judge import (
    run_typography_judge,
)
from contentcreajudge.preprocessing.typography_preprocessor import (
    preprocess_typography_content,
)
from contentcreajudge.rules.judges.typography.typography_resolver import (
    resolve_typography_rules,
)


def execute_typography_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the typography judge flow."""

    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    resolved_typography_rules = resolve_typography_rules(context)
    preprocessed_content = preprocess_typography_content(content)
    typography_result = run_typography_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_typography_rules,
    )
    aggregation_result = aggregate_typography_result(typography_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["typography"],
            "judge_rules": {
                "typography": resolved_typography_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": typography_result,
        "aggregation": aggregation_result,
        "message": (
            "Typography flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }
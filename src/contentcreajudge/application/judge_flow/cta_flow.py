"""Application orchestration for the CTA evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.cta_aggregator import aggregate_cta_result
from contentcreajudge.judges.cta.cta_judge import run_cta_judge
from contentcreajudge.preprocessing.cta_preprocessor import preprocess_cta_content
from contentcreajudge.rules.judges.cta.cta_resolver import resolve_cta_rules


def execute_cta_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the CTA judge flow."""

    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary.")

    resolved_cta_rules = resolve_cta_rules(context)
    preprocessed_content = preprocess_cta_content(content)

    cta_result = run_cta_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_cta_rules,
    )

    aggregation_result = aggregate_cta_result(cta_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["cta"],
            "judge_rules": {
                "cta": resolved_cta_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": cta_result,
        "aggregation": aggregation_result,
        "message": (
            "CTA flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }
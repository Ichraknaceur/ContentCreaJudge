"""Application orchestration for the SEO evaluation flow."""

from __future__ import annotations

from typing import Any

from contentcreajudge.aggregation.seo_aggregator import aggregate_seo_result
from contentcreajudge.judges.seo.seo_judge import run_seo_judge
from contentcreajudge.preprocessing.seo_preprocessor import preprocess_seo_content
from contentcreajudge.rules.judges.seo.seo_resolver import resolve_seo_rules


def execute_seo_flow(payload: dict[str, Any]) -> dict[str, Any]:
    """Execute the steps of the SEO judge flow."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    resolved_seo_rules = resolve_seo_rules(context)

    preprocessed_content = preprocess_seo_content(
        content=content,
        judge_rules=resolved_seo_rules,
    )

    seo_result = run_seo_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_seo_rules,
    )

    aggregation_result = aggregate_seo_result(seo_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["seo"],
            "judge_rules": {
                "seo": resolved_seo_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": seo_result,
        "aggregation": aggregation_result,
        "message": (
            "SEO flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }

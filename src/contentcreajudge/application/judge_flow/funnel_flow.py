"""Application orchestration for the funnel evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.funnel_aggregator import aggregate_funnel_result
from contentcreajudge.judges.funnel.funnel_judge import run_funnel_judge
from contentcreajudge.preprocessing.funnel_preprocessor import preprocess_funnel_content
from contentcreajudge.rules.judges.funnel.funnel_resolver import resolve_funnel_rules


def execute_funnel_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the funnel judge flow with OpenAI and Mistral."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    if not isinstance(context, dict):
        context = {}

    resolved_funnel_rules = resolve_funnel_rules(context)
    preprocessed_content = preprocess_funnel_content(content)
    normalized_content = str(preprocessed_content.get("normalized_text", ""))

    openai_judge_result = run_funnel_judge(
        content=normalized_content,
        judge_rules=resolved_funnel_rules,
        provider="openai",
    )

    mistral_judge_result = run_funnel_judge(
        content=normalized_content,
        judge_rules=resolved_funnel_rules,
        provider="mistral",
    )

    openai_aggregation = aggregate_funnel_result(openai_judge_result)
    mistral_aggregation = aggregate_funnel_result(mistral_judge_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["funnel"],
            "judge_rules": {
                "funnel": resolved_funnel_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_results": {
            "openai": openai_judge_result,
            "mistral": mistral_judge_result,
        },
        "aggregations": {
            "openai": openai_aggregation,
            "mistral": mistral_aggregation,
        },
        "message": (
            "Funnel flow complete: request, rule resolution, preprocessing, "
            "OpenAI judge, Mistral judge, aggregations, response."
        ),
    }

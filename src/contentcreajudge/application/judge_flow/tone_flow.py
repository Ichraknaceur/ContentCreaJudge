"""Application orchestration for the tone evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.tone_aggregator import aggregate_tone_result
from contentcreajudge.judges.tone.tone_judge import run_tone_judge
from contentcreajudge.preprocessing.tone_preprocessor import preprocess_tone_content
from contentcreajudge.rules.judges.tone.tone_resolver import resolve_tone_rules


def execute_tone_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the tone judge flow."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    if not isinstance(context, dict):
        context = {}

    resolved_tone_rules = resolve_tone_rules(context)

    preprocessed_content = preprocess_tone_content(content)

    tone_result = run_tone_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_tone_rules,
    )

    aggregation_result = aggregate_tone_result(tone_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["tone"],
            "judge_rules": {
                "tone": resolved_tone_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": tone_result,
        "aggregation": aggregation_result,
        "message": (
            "Tone flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }

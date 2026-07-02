"""Application orchestration for the length evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.length_aggregator import aggregate_length_result
from contentcreajudge.judges.length.length_judge import run_length_judge
from contentcreajudge.preprocessing.length_preprocessor import preprocess_length_content
from contentcreajudge.rules.judges.length.length_resolver import resolve_length_rules


def execute_length_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the Length judge flow."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    resolved_length_rules = resolve_length_rules(context)

    global_preprocessing = payload.get("global_preprocessing")

    if isinstance(global_preprocessing, dict):
        preprocessed_content = {
            "original_content": content,
            "normalized_text": global_preprocessing.get("normalized_text", ""),
            "word_count": global_preprocessing.get("word_count", 0),
            "is_empty": global_preprocessing.get("is_empty", True),
        }
    else:
        preprocessed_content = preprocess_length_content(content)

    length_result = run_length_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_length_rules,
    )
    aggregation_result = aggregate_length_result(length_result)
    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["length"],
            "judge_rules": {
                "length": resolved_length_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": length_result,
        "aggregation": aggregation_result,
        "message": (
            "Length flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }

"""Application orchestration for the length evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.length_aggregator import aggregate_length_result
from contentcreajudge.judges.length.length_judge import run_length_judge
from contentcreajudge.rules.judges.length.length_resolver import resolve_length_rules
from contentcreajudge.preprocessing.length_preprocessor import (preprocess_length_content, )


def execute_length_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the Length judge flow"""

    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    resolved_length_rules = resolve_length_rules(context)
   
    preprocessed_content = preprocess_length_content(content)
    length_result = run_length_judge(
        preprocessed_content=preprocessed_content,
        judge_rules= resolved_length_rules,
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
        "aggregation" : aggregation_result,
        "message": (
                "Length flow complete: request, rule resolution, preprocessing, "
                "judge, aggregation, response."
        ),
    }
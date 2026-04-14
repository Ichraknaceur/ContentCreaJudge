"""Application orchestration for the structure evaluation flow."""

from __future__ import annotations

from typing import Any

from contentcreajudge.aggregation.structure_aggregator import (
    aggregate_structure_result,
)
from contentcreajudge.judges.structure.structure_judge import (
    run_structure_judge,
)
from contentcreajudge.preprocessing.structure_preprocessor import (
    preprocess_structure_content,
)
from contentcreajudge.rules.judges.structure.structure_resolver import (
    resolve_structure_rules,
)


def execute_structure_flow(payload: dict[str, object]) -> dict[str, Any]:
    """Execute the steps of the Structure judge flow."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    resolved_structure_rules = resolve_structure_rules(context)

    internal_comment_patterns = resolved_structure_rules["structure_rules"][
        "internal_outline_comments"
    ]["patterns"]

    preprocessed_content = preprocess_structure_content(
        expected_outline_html=resolved_structure_rules["expected_outline_html"],
        generated_html=content,
        internal_comment_patterns=internal_comment_patterns,
    )

    structure_result = run_structure_judge(
        preprocessed_content=preprocessed_content,
        judge_rules=resolved_structure_rules,
    )

    aggregation_result = aggregate_structure_result(structure_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["structure"],
            "judge_rules": {
                "structure": resolved_structure_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": structure_result,
        "aggregation": aggregation_result,
        "message": (
            "Structure flow complete: request, rule resolution, preprocessing, "
            "judge, aggregation, response."
        ),
    }
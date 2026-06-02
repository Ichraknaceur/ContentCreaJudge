"""Application orchestration for the persona evaluation flow."""

from __future__ import annotations

from contentcreajudge.aggregation.persona_aggregator import aggregate_persona_result
from contentcreajudge.judges.persona.persona_judge import run_persona_judge
from contentcreajudge.preprocessing.persona_preprocessor import (
    preprocess_persona_content,
)
from contentcreajudge.rules.judges.persona.persona_resolver import (
    resolve_persona_rules,
)


def execute_persona_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the steps of the Persona judge flow."""
    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    if not isinstance(context, dict):
        context = {}

    preprocessed_content = preprocess_persona_content(
        content=content,
        context=context,
    )

    resolved_persona_rules = resolve_persona_rules(preprocessed_content)

    persona_result = run_persona_judge(
        content=str(preprocessed_content.get("normalized_text", "")),
        resolved_rules=resolved_persona_rules,
    )

    aggregation_result = aggregate_persona_result(persona_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["persona"],
            "judge_rules": {
                "persona": resolved_persona_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "judge_result": persona_result,
        "aggregation": aggregation_result,
        "message": (
            "Persona flow complete: request, rule resolution, preprocessing, "
            "OpenAI and Mistral judge, aggregation, response."
        ),
    }

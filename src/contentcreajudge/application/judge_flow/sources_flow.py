"""Application orchestration for the sources evaluation flow."""

from __future__ import annotations

from contentcreajudge.adapters.sources.source_url_validator import (
    validate_source_urls,
)
from contentcreajudge.aggregation.sources_aggregator import (
    aggregate_sources_result,
)
from contentcreajudge.judges.sources.sources_judge import run_sources_judge
from contentcreajudge.preprocessing.sources_preprocessor import (
    preprocess_sources_content,
)
from contentcreajudge.rules.judges.sources.sources_resolver import (
    resolve_sources_rules,
)


def execute_sources_flow(payload: dict[str, object]) -> dict[str, object]:
    """Execute the full Sources judge flow."""

    content = str(payload.get("content", ""))
    profile = str(payload.get("profile", "default"))
    request_id = payload.get("request_id")
    context = payload.get("context") or {}

    if not isinstance(context, dict):
        raise ValueError("context must be a dictionary.")

    resolved_sources_rules = resolve_sources_rules(context)

    internal_domain = str(
        resolved_sources_rules["complementary_reading"]["required_domain"]
    )

    preprocessed_content = preprocess_sources_content(
        content=content,
        internal_domain=internal_domain,
    )

    urls_to_validate = [
        str(link["href"])
        for link in preprocessed_content["external_links"]
        if str(link.get("href", "")).strip()
    ]

    validation_results = validate_source_urls(
        urls=urls_to_validate,
        network_rules=resolved_sources_rules["network_validation"],
        forbidden_query_parameters=resolved_sources_rules["url_cleaning"][
            "forbidden_query_parameters"
        ],
    )

    sources_result = run_sources_judge(
        preprocessed_content=preprocessed_content,
        validation_results=validation_results,
        judge_rules=resolved_sources_rules,
    )

    aggregation_result = aggregate_sources_result(sources_result)

    return {
        "request_echo": {
            "content": content,
            "profile": profile,
            "request_id": request_id,
            "context": context,
        },
        "rule_resolution": {
            "profile": profile,
            "enabled_judges": ["sources"],
            "judge_rules": {
                "sources": resolved_sources_rules,
            },
        },
        "preprocessing": preprocessed_content,
        "url_validation": validation_results,
        "judge_result": sources_result,
        "aggregation": aggregation_result,
        "message": (
            "Sources flow complete: request, rule resolution, preprocessing, "
            "URL validation, judge, aggregation, response."
        ),
    }
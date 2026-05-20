"""Rule resolver for the sources judge."""

from __future__ import annotations

from pathlib import Path

from contentcreajudge.judges.sources.exceptions import (
    MissingSourcesContextError,
    UnsupportedSourcesValueError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config


def resolve_sources_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the sources rules defined in the YAML based on the evaluation context."""
    config_path = Path(__file__).with_name("sources.yaml")

    config = load_yaml_config(config_path)

    sources_rules = config.get("sources_rules") or {}

    content_type = str(context.get("content_type", "")).strip()
    expected_length = str(context.get("expected_length", "")).strip()
    locale = str(context.get("locale", "fr-FR") or "fr-FR")
    require_sources = bool(context.get("require_sources", False))
    organization_website = str(context.get("organization_website", "")).strip()

    if not content_type:
        raise MissingSourcesContextError("content_type")

    if not expected_length:
        raise MissingSourcesContextError("expected_length")

    if not organization_website:
        raise MissingSourcesContextError("organization_website")

    content_type_policy = sources_rules.get("content_type_policy", {})
    allowed_content_types = content_type_policy.get("allowed", [])
    cautious_content_types = content_type_policy.get("allowed_with_caution", [])
    forbidden_content_types = content_type_policy.get(
        "forbidden_except_official_or_regulatory_need",
        [],
    )

    known_content_types = (
        allowed_content_types + cautious_content_types + forbidden_content_types
    )

    if content_type not in known_content_types:
        raise UnsupportedSourcesValueError(
            "content_type",
            content_type,
            known_content_types,
        )

    references_by_length = sources_rules.get("references_by_length", {})

    if expected_length not in references_by_length:
        raise UnsupportedSourcesValueError(
            "expected_length",
            expected_length,
            list(references_by_length.keys()),
        )

    complementary_reading_rules = dict(
        sources_rules.get("complementary_reading", {}),
    )
    complementary_reading_rules["required_domain"] = organization_website

    return {
        "judge_id": config.get("judge_id", "sources"),
        "version": config.get("version", 1),
        "label": config.get("label", "Sources judge"),
        "description": config.get("description", ""),
        "content_type": content_type,
        "expected_length": expected_length,
        "locale": locale,
        "require_sources": require_sources,
        "organization_website": organization_website,
        "is_content_type_allowed": content_type in allowed_content_types,
        "is_content_type_allowed_with_caution": content_type in cautious_content_types,
        "is_content_type_forbidden": content_type in forbidden_content_types,
        "reference_limits": references_by_length.get(expected_length, {}),
        "html_link_format": sources_rules.get("html_link_format", {}),
        "url_cleaning": sources_rules.get("url_cleaning", {}),
        "network_validation": sources_rules.get("network_validation", {}),
        "source_placement": sources_rules.get("source_placement", {}),
        "data_claims": sources_rules.get("data_claims", {}),
        "complementary_reading": complementary_reading_rules,
        "conflict_resolution": sources_rules.get("conflict_resolution", {}),
        "rules": sources_rules.get("rules", []),
        "messages": sources_rules.get("messages", {}),
    }

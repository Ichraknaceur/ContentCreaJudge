"""Rule resolver for the sources judge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def resolve_sources_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the sources rules defined in the YAML based on the evaluation context."""

    config_path = Path(__file__).with_name("sources.yaml")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    sources_rules = config["sources_rules"]

    content_type = context.get("content_type")
    expected_length = context.get("expected_length")
    locale = context.get("locale", "fr-FR")
    require_sources = context.get("require_sources")

    if not content_type:
        raise ValueError("Missing context.content_type for sources evaluation.")

    if not expected_length:
        raise ValueError("Missing context.expected_length for sources evaluation.")

    content_type_policy = sources_rules["content_type_policy"]
    allowed_content_types = content_type_policy["allowed"]
    cautious_content_types = content_type_policy["allowed_with_caution"]
    forbidden_content_types = content_type_policy[
        "forbidden_except_official_or_regulatory_need"
    ]

    if content_type not in (
        allowed_content_types + cautious_content_types + forbidden_content_types
    ):
        raise ValueError(f"Unknown content_type for sources evaluation: {content_type}")

    references_by_length = sources_rules["references_by_length"]

    if expected_length not in references_by_length:
        raise ValueError(f"Unknown expected_length for sources evaluation: {expected_length}")

    if require_sources is None:
        require_sources = False

    return {
        "judge_id": config["judge_id"],
        "version": config["version"],
        "label": config["label"],
        "description": config["description"],
        "content_type": content_type,
        "expected_length": expected_length,
        "locale": locale,
        "require_sources": bool(require_sources),
        "is_content_type_allowed": content_type in allowed_content_types,
        "is_content_type_allowed_with_caution": content_type in cautious_content_types,
        "is_content_type_forbidden": content_type in forbidden_content_types,
        "reference_limits": references_by_length[expected_length],
        "html_link_format": sources_rules["html_link_format"],
        "url_cleaning": sources_rules["url_cleaning"],
        "network_validation": sources_rules["network_validation"],
        "source_placement": sources_rules["source_placement"],
        "data_claims": sources_rules["data_claims"],
        "complementary_reading": sources_rules["complementary_reading"],
        "conflict_resolution": sources_rules["conflict_resolution"],
        "rules": sources_rules["rules"],
        "messages": sources_rules["messages"],
    }
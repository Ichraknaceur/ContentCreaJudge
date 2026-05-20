"""Rule resolver for the CTA judge."""

from __future__ import annotations

from pathlib import Path

from contentcreajudge.judges.cta.exceptions import (
    MissingCTAContextError,
    UnsupportedCTAValueError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config


def resolve_cta_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve CTA rules from YAML and evaluation context."""
    config_path = Path(__file__).with_name("cta.yaml")

    config = load_yaml_config(config_path)

    cta_rules = config.get("cta_rules") or {}

    expected_cta = context.get("expected_cta")
    content_type = context.get("content_type")
    funnel_stage = context.get("funnel_stage")
    content_purpose = context.get("content_purpose")
    language = context.get("language", "fr")

    if not content_type:
        raise MissingCTAContextError("content_type")

    if not funnel_stage:
        raise MissingCTAContextError("funnel_stage")

    normalized_funnel_stage = str(funnel_stage).upper()

    funnel_alignment = cta_rules.get("funnel_alignment") or {}
    expected_by_funnel = funnel_alignment.get("expected_by_funnel") or {}

    if normalized_funnel_stage not in expected_by_funnel:
        raise UnsupportedCTAValueError(
            "funnel_stage",
            str(funnel_stage),
            list(expected_by_funnel.keys()),
        )

    return {
        "judge_id": config.get("judge_id", "cta"),
        "version": config.get("version", 1),
        "label": config.get("label", "CTA judge"),
        "description": config.get(
            "description",
            "Evaluate CTA compliance.",
        ),
        "expected_cta": str(expected_cta).strip() if expected_cta else None,
        "content_type": str(content_type),
        "funnel_stage": normalized_funnel_stage,
        "content_purpose": str(content_purpose).strip() if content_purpose else None,
        "language": str(language).lower(),
        "input_source": cta_rules.get("input_source", {}),
        "activation": cta_rules.get("activation", {}),
        "quantity": cta_rules.get("quantity", {}),
        "html_format": cta_rules.get("html_format", {}),
        "placement": cta_rules.get("placement", {}),
        "quiz_specific": cta_rules.get("quiz_specific", {}),
        "complementary_reading_conflict": cta_rules.get(
            "complementary_reading_conflict",
            {},
        ),
        "funnel_alignment": funnel_alignment,
        "content_purpose_alignment": cta_rules.get(
            "content_purpose_alignment",
            {},
        ),
        "brief_alignment": cta_rules.get("brief_alignment", {}),
        "anchor_quality": cta_rules.get("anchor_quality", {}),
        "language_policy": cta_rules.get("language_policy", {}),
        "style_constraints": cta_rules.get("style_constraints", {}),
        "semantic_fallback": cta_rules.get("semantic_fallback", {}),
        "rules": cta_rules.get("rules", []),
        "messages": cta_rules.get("messages", {}),
    }

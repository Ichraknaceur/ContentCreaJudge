"""Rule resolver for the CTA judge."""

from __future__ import annotations

from pathlib import Path

import yaml


def resolve_cta_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve CTA rules from YAML and evaluation context."""

    config_path = Path(__file__).with_name("cta.yaml")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    cta_rules = config["cta_rules"]

    expected_cta = context.get("expected_cta")
    content_type = context.get("content_type")
    funnel_stage = context.get("funnel_stage")
    content_purpose = context.get("content_purpose")
    language = context.get("language", "fr")

    if not content_type:
        raise ValueError("Missing context.content_type for CTA evaluation.")

    if not funnel_stage:
        raise ValueError("Missing context.funnel_stage for CTA evaluation.")

    normalized_funnel_stage = str(funnel_stage).upper()
    expected_by_funnel = cta_rules["funnel_alignment"]["expected_by_funnel"]

    if normalized_funnel_stage not in expected_by_funnel:
        raise ValueError(f"Unknown funnel_stage: {funnel_stage}")

    return {
        "judge_id": config["judge_id"],
        "version": config["version"],
        "label": config["label"],
        "description": config["description"],
        "expected_cta": str(expected_cta).strip() if expected_cta else None,
        "content_type": str(content_type),
        "funnel_stage": normalized_funnel_stage,
        "content_purpose": str(content_purpose).strip() if content_purpose else None,
        "language": str(language).lower(),
        "input_source": cta_rules["input_source"],
        "activation": cta_rules["activation"],
        "quantity": cta_rules["quantity"],
        "html_format": cta_rules["html_format"],
        "placement": cta_rules["placement"],
        "quiz_specific": cta_rules["quiz_specific"],
        "complementary_reading_conflict": cta_rules["complementary_reading_conflict"],
        "funnel_alignment": cta_rules["funnel_alignment"],
        "content_purpose_alignment": cta_rules["content_purpose_alignment"],
        "brief_alignment": cta_rules["brief_alignment"],
        "anchor_quality": cta_rules["anchor_quality"],
        "language_policy": cta_rules["language_policy"],
        "style_constraints": cta_rules["style_constraints"],
        "semantic_fallback": cta_rules["semantic_fallback"],
        "rules": cta_rules["rules"],
        "messages": cta_rules["messages"],
    }
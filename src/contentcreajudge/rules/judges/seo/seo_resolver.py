from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ALLOWED_LENGTHS = {"SIMPLE", "MEDIUM", "LONG"}
ALLOWED_FUNNEL_STAGES = {"AWARENESS", "CONSIDERATION", "DECISION"}


def resolve_seo_rules(context: dict[str, Any]) -> dict[str, Any]:
    """Resolve the SEO rules defined in YAML based on the evaluation context."""

    config_path = Path(__file__).with_name("seo.yaml")

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    seo_rules = config["seo_rules"]

    content_type = context.get("content_type")
    expected_length = context.get("expected_length")
    funnel_stage = context.get("funnel_stage")
    locale = context.get("locale")

    main_keyword = context.get("main_keyword")
    secondary_keywords = context.get("secondary_keywords", [])
    long_tail_keywords = context.get("long_tail_keywords", [])

    if not content_type:
        raise ValueError("Missing context.content_type for SEO evaluation.")

    if not expected_length:
        raise ValueError("Missing context.expected_length for SEO evaluation.")

    if expected_length not in ALLOWED_LENGTHS:
        raise ValueError(f"Unknown expected_length: {expected_length}")

    if not funnel_stage:
        raise ValueError("Missing context.funnel_stage for SEO evaluation.")

    if funnel_stage not in ALLOWED_FUNNEL_STAGES:
        raise ValueError(f"Unknown funnel_stage: {funnel_stage}")

    if not main_keyword:
        raise ValueError("Missing context.main_keyword for SEO evaluation.")

    if not isinstance(secondary_keywords, list):
        raise ValueError("context.secondary_keywords must be a list.")

    if not isinstance(long_tail_keywords, list):
        raise ValueError("context.long_tail_keywords must be a list.")

    keyword_occurrence_rules = seo_rules["keyword_occurrences"]["by_length"][expected_length]
    long_tail_rules = seo_rules["long_tail_keywords"]
    exceptions = seo_rules.get("exceptions", {})

    awareness_simple_exception = (
        funnel_stage == "AWARENESS"
        and expected_length == "SIMPLE"
        and exceptions.get("awareness_simple_disables_mandatory_full_long_tail", False)
    )

    allow_long_tail_keywords = True
    if (
        funnel_stage == "AWARENESS"
        and expected_length == "SIMPLE"
        and long_tail_rules.get("awareness_simple_excludes_complex_long_tail", False)
    ):
        allow_long_tail_keywords = False

    resolved_long_tail_keywords = long_tail_keywords if allow_long_tail_keywords else []

    return {
        "judge_id": "seo",
        "content_type": content_type,
        "expected_length": expected_length,
        "funnel_stage": funnel_stage,
        "locale": locale,
        "main_keyword": main_keyword,
        "secondary_keywords": secondary_keywords,
        "long_tail_keywords": resolved_long_tail_keywords,
        "main_keyword_rules": seo_rules["main_keyword"],
        "keyword_occurrence_rules": {
            "enforce_minimum_occurrences": seo_rules["keyword_occurrences"]["enforce_minimum_occurrences"],
            "min_total": keyword_occurrence_rules.get("min_total"),
            "max_total": keyword_occurrence_rules.get("max_total"),
            "min_main": keyword_occurrence_rules.get("min_main"),
        },
        "secondary_keyword_rules": seo_rules["secondary_keywords"],
        "long_tail_keyword_rules": {
            **long_tail_rules,
            "allow_long_tail_keywords": allow_long_tail_keywords,
            "awareness_simple_exception_applied": awareness_simple_exception,
        },
        "keyword_integrity_rules": seo_rules["keyword_integrity"],
        "keyword_distribution_rules": seo_rules["keyword_distribution"],
        "readability_priority_rules": seo_rules["readability_priority"],
        "over_optimization_rules": seo_rules["over_optimization"],
        "formatting_constraints_rules": seo_rules["formatting_constraints"],
        "rules": config["rules"],
        "messages": config["messages"],
    }
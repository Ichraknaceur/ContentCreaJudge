from __future__ import annotations

from pathlib import Path
from typing import Any

from contentcreajudge.judges.seo.exceptions import (
    MissingSeoContextError,
    UnsupportedSeoValueError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config

ALLOWED_LENGTHS = {"SIMPLE", "MEDIUM", "LONG"}
ALLOWED_FUNNEL_STAGES = {"AWARENESS", "CONSIDERATION", "DECISION"}


def _validate_seo_context(context_values: dict[str, object]) -> None:
    """Validate the required SEO context fields."""
    content_type = context_values["content_type"]
    expected_length = context_values["expected_length"]
    funnel_stage = context_values["funnel_stage"]
    main_keyword = context_values["main_keyword"]
    secondary_keywords = context_values["secondary_keywords"]
    long_tail_keywords = context_values["long_tail_keywords"]

    if not content_type:
        raise MissingSeoContextError("content_type")

    if not expected_length:
        raise MissingSeoContextError("expected_length")

    if expected_length not in ALLOWED_LENGTHS:
        raise UnsupportedSeoValueError(
            "expected_length",
            str(expected_length),
            sorted(ALLOWED_LENGTHS),
        )

    if not funnel_stage:
        raise MissingSeoContextError("funnel_stage")

    if funnel_stage not in ALLOWED_FUNNEL_STAGES:
        raise UnsupportedSeoValueError(
            "funnel_stage",
            str(funnel_stage),
            sorted(ALLOWED_FUNNEL_STAGES),
        )

    if not main_keyword:
        raise MissingSeoContextError("main_keyword")

    if not isinstance(secondary_keywords, list):
        raise MissingSeoContextError("secondary_keywords")

    if not isinstance(long_tail_keywords, list):
        raise MissingSeoContextError("long_tail_keywords")


def _allow_long_tail_keywords(
    funnel_stage: object,
    expected_length: object,
    long_tail_rules: dict[str, Any],
) -> bool:
    """Return whether long-tail keywords should be applied."""
    return not (
        funnel_stage == "AWARENESS"
        and expected_length == "SIMPLE"
        and long_tail_rules.get("awareness_simple_excludes_complex_long_tail", False)
    )


def _build_keyword_occurrence_rules(
    seo_rules: dict[str, Any],
    expected_length: object,
) -> dict[str, Any]:
    """Build keyword occurrence rules for the resolved context."""
    length_rules = seo_rules["keyword_occurrences"]["by_length"][expected_length]
    return {
        "enforce_minimum_occurrences": seo_rules["keyword_occurrences"][
            "enforce_minimum_occurrences"
        ],
        "min_total": length_rules.get("min_total"),
        "max_total": length_rules.get("max_total"),
        "min_main": length_rules.get("min_main"),
    }


def _apply_quiz_overrides(
    content_type: object,
    seo_rules: dict[str, Any],
    main_keyword_rules: dict[str, Any],
    keyword_occurrence_rules: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply quiz-specific SEO rule overrides when needed."""
    if content_type != "quiz":
        return main_keyword_rules, keyword_occurrence_rules

    return (
        {
            **seo_rules["main_keyword"],
            "required_locations": {
                "introduction": True,
                "heading_h2_or_h3": False,
                "conclusion": False,
                "body": True,
            },
        },
        {
            "enforce_minimum_occurrences": True,
            "min_total": 2,
            "max_total": 6,
            "min_main": None,
        },
    )


def resolve_seo_rules(context: dict[str, Any]) -> dict[str, Any]:
    """Resolve the SEO rules defined in YAML based on the evaluation context."""
    config_path = Path(__file__).with_name("seo.yaml")

    config = load_yaml_config(config_path)

    seo_rules = config.get("seo_rules") or {}

    content_type = context.get("content_type")
    expected_length = context.get("expected_length")
    funnel_stage = context.get("funnel_stage")
    locale = context.get("locale")

    main_keyword = context.get("main_keyword")
    secondary_keywords = context.get("secondary_keywords", [])
    long_tail_keywords = context.get("long_tail_keywords", [])

    _validate_seo_context(
        {
            "content_type": content_type,
            "expected_length": expected_length,
            "funnel_stage": funnel_stage,
            "main_keyword": main_keyword,
            "secondary_keywords": secondary_keywords,
            "long_tail_keywords": long_tail_keywords,
        },
    )

    long_tail_rules = seo_rules["long_tail_keywords"]
    exceptions = seo_rules.get("exceptions", {})

    awareness_simple_exception = (
        funnel_stage == "AWARENESS"
        and expected_length == "SIMPLE"
        and exceptions.get("awareness_simple_disables_mandatory_full_long_tail", False)
    )

    allow_long_tail_keywords = _allow_long_tail_keywords(
        funnel_stage,
        expected_length,
        long_tail_rules,
    )

    resolved_long_tail_keywords = long_tail_keywords if allow_long_tail_keywords else []

    main_keyword_rules = seo_rules["main_keyword"]
    keyword_occurrence_rules = _build_keyword_occurrence_rules(
        seo_rules,
        expected_length,
    )

    main_keyword_rules, keyword_occurrence_rules = _apply_quiz_overrides(
        content_type,
        seo_rules,
        main_keyword_rules,
        keyword_occurrence_rules,
    )

    return {
        "judge_id": "seo",
        "content_type": content_type,
        "expected_length": expected_length,
        "funnel_stage": funnel_stage,
        "locale": locale,
        "main_keyword": main_keyword,
        "secondary_keywords": secondary_keywords,
        "long_tail_keywords": resolved_long_tail_keywords,
        "main_keyword_rules": main_keyword_rules,
        "keyword_occurrence_rules": keyword_occurrence_rules,
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
        "scoring": config.get("scoring", {}),
    }

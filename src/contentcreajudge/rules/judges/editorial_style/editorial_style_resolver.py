"""Rule resolver for the editorial style judge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from contentcreajudge.judges.editorial_style.exceptions import (
    InvalidEditorialStyleRulesError,
    InvalidEditorialStyleWeightError,
    MissingEditorialStyleCriterionError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config

_REQUIRED_CRITERIA = (
    "style_alignment",
    "reasoning_alignment",
    "concept_handling",
    "expression_control",
    "writing_conventions",
    "example_alignment",
)


def _validate_criteria(criteria: dict[str, Any]) -> None:
    """Validate that all required editorial style criteria exist."""
    for criterion_name in _REQUIRED_CRITERIA:
        if criterion_name not in criteria:
            raise MissingEditorialStyleCriterionError(criterion_name)


def _validate_weights(criteria: dict[str, Any]) -> None:
    """Validate that criteria weights sum to 1.0."""
    total_weight = 0.0

    for criterion_name in _REQUIRED_CRITERIA:
        criterion = criteria.get(criterion_name) or {}
        weight = criterion.get("weight")

        if not isinstance(weight, (int, float)):
            raise InvalidEditorialStyleRulesError(
                f"Invalid weight for criterion: {criterion_name}",
                details={
                    "criterion_name": criterion_name,
                    "weight": weight,
                },
            )

        total_weight += float(weight)

    if round(total_weight, 6) != 1.0:
        raise InvalidEditorialStyleWeightError(total_weight)


def _validate_thresholds(thresholds: dict[str, Any]) -> None:
    """Validate editorial style status thresholds."""
    pass_score = thresholds.get("pass_score")
    warn_score = thresholds.get("warn_score")

    if not isinstance(pass_score, (int, float)):
        raise InvalidEditorialStyleRulesError(
            "Missing or invalid editorial style pass_score.",
            details={"pass_score": pass_score},
        )

    if not isinstance(warn_score, (int, float)):
        raise InvalidEditorialStyleRulesError(
            "Missing or invalid editorial style warn_score.",
            details={"warn_score": warn_score},
        )

    if float(warn_score) >= float(pass_score):
        raise InvalidEditorialStyleRulesError(
            "warn_score must be lower than pass_score.",
            details={
                "warn_score": warn_score,
                "pass_score": pass_score,
            },
        )


def resolve_editorial_style_rules(
    context: dict[str, object] | None = None,
) -> dict[str, object]:
    """Resolve editorial style rules from YAML configuration."""
    _ = context

    config_path = Path(__file__).with_name("editorial_style.yaml")
    config = load_yaml_config(config_path)

    rules = config.get("editorial_style_rules") or {}

    if not isinstance(rules, dict) or not rules:
        raise InvalidEditorialStyleRulesError(
            "Missing editorial_style_rules configuration.",
        )

    criteria = rules.get("criteria") or {}
    thresholds = rules.get("thresholds") or {}

    if not isinstance(criteria, dict):
        raise InvalidEditorialStyleRulesError(
            "editorial_style criteria must be a dictionary.",
        )

    if not isinstance(thresholds, dict):
        raise InvalidEditorialStyleRulesError(
            "editorial_style thresholds must be a dictionary.",
        )

    _validate_criteria(criteria)
    _validate_weights(criteria)
    _validate_thresholds(thresholds)

    return {
        "judge_id": rules.get("judge_id", "editorial_style"),
        "version": rules.get("version", 1),
        "label": rules.get("label", "Editorial style judge"),
        "description": rules.get(
            "description",
            "Evaluate alignment with the organization's editorial style.",
        ),
        "required_style_fields": rules.get(
            "required_style_fields",
            ["writingStyle", "writeLikeThis", "notLikeThis"],
        ),
        "criteria": criteria,
        "thresholds": thresholds,
        "severity_policy": rules.get("severity_policy", {}),
        "scoring_caps": rules.get("scoring_caps", {}),
        "output": rules.get("output", {}),
    }

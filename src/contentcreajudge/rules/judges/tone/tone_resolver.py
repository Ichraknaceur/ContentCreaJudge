"""Rule resolver for the tone judge."""

from __future__ import annotations

from pathlib import Path

from contentcreajudge.judges.tone.exceptions import (
    InvalidToneConfigurationError,
    MissingToneContextError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config

_TOTAL_CRITERIA_WEIGHT = 100


def _normalize_optional_context_value(
    context: dict[str, object],
    field_name: str,
    default: str = "",
) -> str:
    """Return an optional context value as a stripped string."""
    value = context.get(field_name)

    if value is None:
        return default

    normalized_value = str(value).strip()

    return normalized_value or default


def _normalize_org_tones(context: dict[str, object]) -> list[str]:
    """Return organization tones as a clean list of strings."""
    value = context.get("org_tones")

    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]

    return []


def _validate_tone_configuration(rules: dict[str, object]) -> None:
    """Validate the tone YAML configuration before returning resolved rules."""
    criteria = rules.get("criteria") or []

    if not isinstance(criteria, list) or not criteria:
        raise InvalidToneConfigurationError(
            "Tone configuration must define at least one criterion."
        )

    total_weight = 0

    for criterion in criteria:
        if not isinstance(criterion, dict):
            raise InvalidToneConfigurationError(
                "Each tone criterion must be a dictionary."
            )

        criterion_id = criterion.get("criterion_id")
        if not criterion_id:
            raise InvalidToneConfigurationError(
                "Each tone criterion must define a criterion_id."
            )

        total_weight += int(criterion.get("weight", 0))

    if total_weight != _TOTAL_CRITERIA_WEIGHT:
        raise InvalidToneConfigurationError("Tone criteria weights must sum to 100.")


def resolve_tone_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the tone rules defined in the YAML based on the evaluation context."""
    config_path = Path(__file__).with_name("tone.yaml")

    config = load_yaml_config(config_path)

    rules = config.get("tone_rules") or {}

    expected_tone = context.get("expected_tone")

    if not expected_tone:
        raise MissingToneContextError("expected_tone")

    normalized_expected_tone = str(expected_tone).strip()

    if not normalized_expected_tone:
        raise MissingToneContextError("expected_tone")

    _validate_tone_configuration(rules)

    return {
        "judge_id": config.get("judge_id", "tone"),
        "version": config.get("version", 1),
        "label": config.get("label", "Tone judge"),
        "description": config.get(
            "description",
            "Evaluate whether the content respects the expected tone.",
        ),
        "is_blocking_rule": rules.get("is_blocking_rule", False),
        "evaluation_method": rules.get("evaluation_method", "llm_judge"),
        "supported_providers": rules.get("supported_providers", []),
        "default_providers": rules.get("default_providers", []),
        "guards": rules.get("guards", {}),
        "score": rules.get("score", {}),
        "decision_rules": rules.get("decision_rules", {}),
        "phases": rules.get("phases", []),
        "organization_tones": rules.get("organization_tones", {}),
        "blind_observation": rules.get("blind_observation", {}),
        "criteria": rules.get("criteria", []),
        "expected_criterion_ids": rules.get("expected_criterion_ids", []),
        "criterion_scoring": rules.get("criterion_scoring", {}),
        "output_schema": rules.get("output_schema", {}),
        "finding_rules": rules.get("finding_rules", {}),
        "severity_policy": rules.get("severity_policy", {}),
        "confidence": rules.get("confidence", {}),
        "natural_expression_thresholds": rules.get(
            "natural_expression_thresholds",
            {},
        ),
        "messages": rules.get("messages", {}),
        "context": {
            "expected_tone": normalized_expected_tone,
            "org_tones": _normalize_org_tones(context),
            "organization_voice": _normalize_optional_context_value(
                context,
                "organization_voice",
            ),
            "organization_voice_description": _normalize_optional_context_value(
                context,
                "organization_voice_description",
            ),
            "writing_style": _normalize_optional_context_value(
                context,
                "writing_style",
            ),
            "funnel_stage": _normalize_optional_context_value(
                context,
                "funnel_stage",
            ),
            "persona": _normalize_optional_context_value(
                context,
                "persona",
            ),
            "content_type": _normalize_optional_context_value(
                context,
                "content_type",
            ),
            "brief": _normalize_optional_context_value(
                context,
                "brief",
            ),
            "locale": _normalize_optional_context_value(
                context,
                "locale",
                "fr-FR",
            ),
        },
    }

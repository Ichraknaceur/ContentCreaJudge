"""Rule resolver for the persona judge."""

from __future__ import annotations

from pathlib import Path

from contentcreajudge.judges.persona.exceptions import (
    InvalidPersonaRulesError,
    MissingPersonaContextError,
    UnsupportedPersonaValueError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config

_ALLOWED_BUSINESS_TYPES = ["B2B", "B2C", "B2B2C"]
_ALLOWED_PROVIDERS = ["openai", "mistral"]


def _extract_persona_id(persona: object) -> str | None:
    """Extract a stable persona identifier from supported persona formats."""
    if not isinstance(persona, dict):
        return None

    persona_id = persona.get("persona_id") or persona.get("uuid")

    if persona_id:
        return str(persona_id)

    data = persona.get("data")
    if isinstance(data, dict):
        nested_persona_id = data.get("persona_id") or data.get("uuid")
        if nested_persona_id:
            return str(nested_persona_id)

    return None


def _validate_expected_persona_exists(
    *,
    personas: list[object],
    expected_persona_id: str,
) -> None:
    """Ensure the expected persona is present in the provided personas list."""
    persona_ids = [
        persona_id
        for persona_id in (_extract_persona_id(persona) for persona in personas)
        if persona_id
    ]

    if expected_persona_id not in persona_ids:
        raise UnsupportedPersonaValueError(
            "expected_persona_id",
            expected_persona_id,
            persona_ids,
        )


def _resolve_context_values(
    context: dict[str, object],
    rules: dict[str, object],
) -> tuple[list[object], str, object, list[object]]:
    """Validate and return persona resolver context values."""
    personas = context.get("personas")
    expected_persona_id = context.get("expected_persona_id")
    business_type = context.get("business_type")
    providers = context.get("providers") or rules.get("providers") or _ALLOWED_PROVIDERS

    if not personas:
        raise MissingPersonaContextError("personas")

    if not isinstance(personas, list):
        raise UnsupportedPersonaValueError(
            "personas",
            str(type(personas).__name__),
            ["list"],
        )

    if not expected_persona_id:
        raise MissingPersonaContextError("expected_persona_id")

    if not business_type:
        raise MissingPersonaContextError("business_type")

    if str(business_type) not in _ALLOWED_BUSINESS_TYPES:
        raise UnsupportedPersonaValueError(
            "business_type",
            str(business_type),
            _ALLOWED_BUSINESS_TYPES,
        )

    _validate_expected_persona_exists(
        personas=personas,
        expected_persona_id=str(expected_persona_id),
    )

    if not isinstance(providers, list):
        raise UnsupportedPersonaValueError(
            "providers",
            str(providers),
            _ALLOWED_PROVIDERS,
        )

    unsupported_providers = [
        str(provider)
        for provider in providers
        if str(provider) not in _ALLOWED_PROVIDERS
    ]

    if unsupported_providers:
        raise UnsupportedPersonaValueError(
            "providers",
            ", ".join(unsupported_providers),
            _ALLOWED_PROVIDERS,
        )

    return personas, str(expected_persona_id), business_type, providers


def _validate_rules_config(
    *,
    detection: object,
    criteria: object,
    hard_rules: object,
    scoring: object,
) -> None:
    """Validate required persona rules configuration sections."""
    if not detection:
        raise InvalidPersonaRulesError("missing detection")

    if not criteria:
        raise InvalidPersonaRulesError("missing criteria")

    if not hard_rules:
        raise InvalidPersonaRulesError("missing hard_rules")

    if not scoring:
        raise InvalidPersonaRulesError("missing scoring")

    criteria_weight_sum = sum(
        float(criterion.get("weight", 0))
        for criterion in criteria
        if isinstance(criterion, dict)
    )

    if round(criteria_weight_sum, 2) != 1.0:
        raise InvalidPersonaRulesError("criteria weights must sum to 1.0")


def resolve_persona_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the persona rules defined in the YAML based on the evaluation context."""
    config_path = Path(__file__).with_name("persona.yaml")

    config = load_yaml_config(config_path)

    rules = config.get("persona_rules") or {}
    personas, expected_persona_id, business_type, providers = _resolve_context_values(
        context,
        rules,
    )

    detection = rules.get("detection") or {}
    criteria = rules.get("criteria") or []
    hard_rules = rules.get("hard_rules") or []
    scoring = rules.get("scoring") or {}

    _validate_rules_config(
        detection=detection,
        criteria=criteria,
        hard_rules=hard_rules,
        scoring=scoring,
    )

    return {
        "judge_id": config.get("judge_id", "persona"),
        "version": config.get("version", 2),
        "label": config.get("label", "Persona judge"),
        "description": config.get(
            "description",
            "Detect and evaluate persona alignment compliance.",
        ),
        "is_llm_judge": rules.get("is_llm_judge", True),
        "providers": providers,
        "detection": detection,
        "scoring": scoring,
        "hard_rules": hard_rules,
        "criteria": criteria,
        "output_contract": rules.get("output_contract", {}),
        "personas": personas,
        "expected_persona_id": expected_persona_id,
        "business_type": business_type,
        "content_type": context.get("content_type"),
        "funnel_stage": context.get("funnel_stage"),
        "locale": context.get("locale"),
        "messages": rules.get("messages", {}),
    }

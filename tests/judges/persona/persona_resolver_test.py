"""Tests for the persona rule resolver."""

from __future__ import annotations

import pytest

from contentcreajudge.judges.persona.exceptions import (
    MissingPersonaContextError,
    UnsupportedPersonaValueError,
)
from contentcreajudge.rules.judges.persona.persona_resolver import (
    resolve_persona_rules,
)


def _valid_context() -> dict[str, object]:
    return {
        "personas": [
            {
                "persona_id": "persona-consultant",
                "function": "Consultant indépendant",
                "persona_fields": {
                    "professional_objectives": "Structurer une stratégie éditoriale claire.",
                    "problems_frustrations": "Éviter la dispersion des contenus.",
                    "decision_making_influence": "Décide seul après test concret.",
                    "psy_profile": "Autonome, analytique, sensible à la structure.",
                },
            },
        ],
        "expected_persona_id": "persona-consultant",
        "business_type": "B2B",
        "content_type": "articles",
        "funnel_stage": "AWARENESS",
        "locale": "fr-FR",
    }


def test_resolve_persona_rules_returns_persona_judge_id() -> None:
    """Resolver should return the persona judge id."""
    resolved_rules = resolve_persona_rules(_valid_context())

    assert resolved_rules["judge_id"] == "persona"


def test_resolve_persona_rules_requires_personas() -> None:
    """Resolver should fail when personas context is missing."""
    context = _valid_context()
    context.pop("personas")

    with pytest.raises(MissingPersonaContextError):
        resolve_persona_rules(context)


def test_resolve_persona_rules_requires_business_type() -> None:
    """Resolver should fail when business_type context is missing."""
    context = _valid_context()
    context.pop("business_type")

    with pytest.raises(MissingPersonaContextError):
        resolve_persona_rules(context)


def test_resolve_persona_rules_rejects_unknown_business_type() -> None:
    """Resolver should reject unsupported business types."""
    context = _valid_context()
    context["business_type"] = "B2G"

    with pytest.raises(UnsupportedPersonaValueError):
        resolve_persona_rules(context)


def test_resolve_persona_rules_returns_configured_criteria() -> None:
    """Resolver should return the configured persona criteria."""
    resolved_rules = resolve_persona_rules(_valid_context())

    assert len(resolved_rules["criteria"]) == 5


def test_resolve_persona_rules_weights_sum_to_one() -> None:
    """Resolved persona criteria weights should sum to one."""
    resolved_rules = resolve_persona_rules(_valid_context())

    total_weight = sum(
        float(criterion["weight"]) for criterion in resolved_rules["criteria"]
    )

    assert round(total_weight, 2) == 1.0


def test_resolve_persona_rules_defaults_to_openai_and_mistral() -> None:
    """Resolver should return OpenAI and Mistral as default providers."""
    resolved_rules = resolve_persona_rules(_valid_context())

    assert resolved_rules["providers"] == ["openai", "mistral"]


def test_resolve_persona_rules_rejects_unknown_provider() -> None:
    """Resolver should reject unsupported providers."""
    context = _valid_context()
    context["providers"] = ["openai", "unknown"]

    with pytest.raises(UnsupportedPersonaValueError):
        resolve_persona_rules(context)

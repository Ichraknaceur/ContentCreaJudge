from __future__ import annotations

import pytest

from contentcreajudge.judges.tone.exceptions import MissingToneContextError
from contentcreajudge.rules.judges.tone.tone_resolver import resolve_tone_rules


def test_resolve_tone_rules_returns_expected_config() -> None:
    context = {
        "expected_tone": "Pédagogique",
        "org_tones": ["posé", "pédagogique", "convaincant"],
        "organization_voice": "structurée, équilibrée, accessible",
        "organization_voice_description": "Voix claire et mesurée.",
        "writing_style": "Phrases claires et progressives.",
        "funnel_stage": "Consideration",
        "persona": "Doctorant",
        "content_type": "articles",
        "brief": "Expliquer la place de l’IA dans un travail scientifique.",  # noqa: RUF001
        "locale": "fr-FR",
    }

    rules = resolve_tone_rules(context)

    assert rules["judge_id"] == "tone"
    assert rules["version"] == 1
    assert rules["evaluation_method"] == "llm_judge"
    assert rules["context"]["expected_tone"] == "Pédagogique"
    assert rules["context"]["org_tones"] == ["posé", "pédagogique", "convaincant"]
    assert rules["context"]["locale"] == "fr-FR"
    assert "guards" in rules
    assert "blind_observation" in rules
    assert "organization_tones" in rules
    assert "criterion_scoring" in rules
    assert len(rules["criteria"]) == 4


def test_resolve_tone_rules_accepts_org_tones_as_comma_separated_string() -> None:
    context = {
        "expected_tone": "Pédagogique",
        "org_tones": "posé, pédagogique, convaincant",
    }

    rules = resolve_tone_rules(context)

    assert rules["context"]["org_tones"] == [
        "posé",
        "pédagogique",
        "convaincant",
    ]


def test_resolve_tone_rules_ignores_empty_org_tones_items() -> None:
    context = {
        "expected_tone": "Pédagogique",
        "org_tones": ["posé", "", "  ", "convaincant"],
    }

    rules = resolve_tone_rules(context)

    assert rules["context"]["org_tones"] == ["posé", "convaincant"]


def test_resolve_tone_rules_defaults_org_tones_to_empty_list() -> None:
    context = {
        "expected_tone": "Pédagogique",
    }

    rules = resolve_tone_rules(context)

    assert rules["context"]["org_tones"] == []


def test_resolve_tone_rules_requires_expected_tone() -> None:
    context = {
        "org_tones": ["pédagogique"],
        "locale": "fr-FR",
    }

    with pytest.raises(MissingToneContextError):
        resolve_tone_rules(context)


def test_resolve_tone_rules_rejects_empty_expected_tone() -> None:
    context = {
        "expected_tone": "   ",
        "org_tones": ["pédagogique"],
    }

    with pytest.raises(MissingToneContextError):
        resolve_tone_rules(context)


def test_resolve_tone_rules_uses_default_locale() -> None:
    context = {
        "expected_tone": "Pédagogique",
    }

    rules = resolve_tone_rules(context)

    assert rules["context"]["locale"] == "fr-FR"


def test_resolve_tone_rules_keeps_optional_context_empty_when_missing() -> None:
    context = {
        "expected_tone": "Pédagogique",
    }

    rules = resolve_tone_rules(context)

    assert rules["context"]["organization_voice"] == ""
    assert rules["context"]["organization_voice_description"] == ""
    assert rules["context"]["writing_style"] == ""
    assert rules["context"]["funnel_stage"] == ""
    assert rules["context"]["persona"] == ""
    assert rules["context"]["content_type"] == ""
    assert rules["context"]["brief"] == ""


def test_resolve_tone_rules_weights_sum_to_100() -> None:
    context = {
        "expected_tone": "Pédagogique",
    }

    rules = resolve_tone_rules(context)

    total_weight = sum(int(criterion["weight"]) for criterion in rules["criteria"])

    assert total_weight == 100


def test_resolve_tone_rules_returns_expected_criterion_ids() -> None:
    context = {
        "expected_tone": "Pédagogique",
    }

    rules = resolve_tone_rules(context)

    assert rules["expected_criterion_ids"] == [
        "tone.contextual_alignment",
        "tone.register_consistency",
        "tone.intensity_calibration",
        "tone.natural_expression",
    ]

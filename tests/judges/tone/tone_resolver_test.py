from __future__ import annotations

import pytest

from contentcreajudge.judges.tone.exceptions import MissingToneContextError
from contentcreajudge.rules.judges.tone.tone_resolver import resolve_tone_rules


def test_resolve_tone_rules_returns_expected_config() -> None:
    context = {
        "expected_tone": "Didactique",
        "organization_voice": "structurée, équilibrée, accessible",
        "organization_voice_description": "Voix claire et mesurée.",
        "writing_style": "Phrases claires et progressives.",
        "funnel_stage": "Awareness",
        "persona": "Consultant indépendant",
        "content_type": "articles",
        "brief": "Expliquer une tension éditoriale.",
        "locale": "fr-FR",
    }

    rules = resolve_tone_rules(context)

    assert rules["judge_id"] == "tone"
    assert rules["evaluation_method"] == "llm_judge"
    assert rules["context"]["expected_tone"] == "Didactique"
    assert rules["context"]["locale"] == "fr-FR"
    assert len(rules["criteria"]) == 5


def test_resolve_tone_rules_requires_expected_tone() -> None:
    context = {
        "locale": "fr-FR",
    }

    with pytest.raises(MissingToneContextError):
        resolve_tone_rules(context)


def test_resolve_tone_rules_rejects_empty_expected_tone() -> None:
    context = {
        "expected_tone": "   ",
    }

    with pytest.raises(MissingToneContextError):
        resolve_tone_rules(context)


def test_resolve_tone_rules_uses_default_locale() -> None:
    context = {
        "expected_tone": "Didactique",
    }

    rules = resolve_tone_rules(context)

    assert rules["context"]["locale"] == "fr-FR"


def test_resolve_tone_rules_keeps_optional_context_empty_when_missing() -> None:
    context = {
        "expected_tone": "Didactique",
    }

    rules = resolve_tone_rules(context)

    assert rules["context"]["organization_voice"] == ""
    assert rules["context"]["brief"] == ""

"""Tests for the CTA rule resolver."""

from __future__ import annotations

import pytest

from contentcreajudge.rules.judges.cta.cta_resolver import resolve_cta_rules


def test_resolve_cta_rules_with_valid_context() -> None:
    context = {
        "content_type": "articles",
        "funnel_stage": "AWARENESS",
        "expected_cta": "Read more",
        "content_purpose": "Sensibilisation",
        "language": "fr",
    }

    resolved_rules = resolve_cta_rules(context)

    assert resolved_rules["judge_id"] == "cta"
    assert resolved_rules["version"] == 1
    assert resolved_rules["expected_cta"] == "Read more"
    assert resolved_rules["content_type"] == "articles"
    assert resolved_rules["funnel_stage"] == "AWARENESS"
    assert resolved_rules["content_purpose"] == "Sensibilisation"
    assert resolved_rules["language"] == "fr"
    assert "funnel_alignment" in resolved_rules
    assert "messages" in resolved_rules


def test_resolve_cta_rules_normalizes_funnel_stage() -> None:
    context = {
        "content_type": "articles",
        "funnel_stage": "awareness",
        "expected_cta": "Read more",
    }

    resolved_rules = resolve_cta_rules(context)

    assert resolved_rules["funnel_stage"] == "AWARENESS"


def test_resolve_cta_rules_raises_error_without_content_type() -> None:
    context = {
        "funnel_stage": "AWARENESS",
        "expected_cta": "Read more",
    }

    with pytest.raises(ValueError, match="Missing context.content_type"):
        resolve_cta_rules(context)


def test_resolve_cta_rules_raises_error_without_funnel_stage() -> None:
    context = {
        "content_type": "articles",
        "expected_cta": "Read more",
    }

    with pytest.raises(ValueError, match="Missing context.funnel_stage"):
        resolve_cta_rules(context)


def test_resolve_cta_rules_raises_error_for_unknown_funnel_stage() -> None:
    context = {
        "content_type": "articles",
        "funnel_stage": "UNKNOWN",
        "expected_cta": "Read more",
    }

    with pytest.raises(ValueError, match="Unknown funnel_stage"):
        resolve_cta_rules(context)
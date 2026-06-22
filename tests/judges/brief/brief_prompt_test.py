"""Tests for the Brief Judge prompt builder."""

from __future__ import annotations

from contentcreajudge.judges.brief.brief_prompt import build_brief_prompt


def test_build_brief_prompt_injects_brief() -> None:
    prompt = build_brief_prompt(
        brief="Mon brief de test",
        article="Mon article",
    )

    assert "Mon brief de test" in prompt


def test_build_brief_prompt_injects_article() -> None:
    prompt = build_brief_prompt(
        brief="Mon brief",
        article="Mon article de test",
    )

    assert "Mon article de test" in prompt


def test_build_brief_prompt_replaces_placeholders() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert "{{BRIEF}}" not in prompt
    assert "{{ARTICLE}}" not in prompt


def test_build_brief_prompt_contains_all_criteria() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert "angle_alignment" in prompt
    assert "axis_development" in prompt
    assert "intended_understanding" in prompt
    assert "scope_adherence" in prompt
    assert "specific_element_integration" in prompt


def test_build_brief_prompt_forbids_global_score_and_status() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert "Ne calcule jamais de score global" in prompt
    assert "statut final" in prompt


def test_build_brief_prompt_contains_expected_output_schema() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert '"brief_decomposition"' in prompt
    assert '"evaluation"' in prompt
    assert '"global_summary"' in prompt


def test_build_brief_prompt_mentions_conditional_specific_element() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert '"applicable": false' in prompt
    assert '"applicable": true' in prompt


def test_build_brief_prompt_mentions_confidence() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert "confidence" in prompt


def test_build_brief_prompt_requests_valid_json_only() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert "Réponds uniquement avec un objet JSON valide" in prompt


def test_build_brief_prompt_is_not_empty() -> None:
    prompt = build_brief_prompt(
        brief="Brief",
        article="Article",
    )

    assert prompt.strip()

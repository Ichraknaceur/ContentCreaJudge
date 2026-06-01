from __future__ import annotations

from contentcreajudge.judges.tone.tone_prompt import build_tone_judge_prompt


def test_build_tone_judge_prompt_includes_content() -> None:
    prompt = build_tone_judge_prompt(
        content="<p>Texte à évaluer.</p>",
        judge_rules={
            "context": {
                "expected_tone": "Didactique",
                "locale": "fr-FR",
            }
        },
    )

    assert "<p>Texte à évaluer.</p>" in prompt


def test_build_tone_judge_prompt_includes_expected_tone() -> None:
    prompt = build_tone_judge_prompt(
        content="Texte à évaluer.",
        judge_rules={
            "context": {
                "expected_tone": "Didactique",
                "locale": "fr-FR",
            }
        },
    )

    assert "Ton attendu :" in prompt
    assert "Didactique" in prompt


def test_build_tone_judge_prompt_includes_contextual_fields() -> None:
    prompt = build_tone_judge_prompt(
        content="Texte à évaluer.",
        judge_rules={
            "context": {
                "expected_tone": "Didactique",
                "organization_voice": "structurée, accessible",
                "organization_voice_description": "Voix claire et mesurée.",
                "writing_style": "Phrases progressives.",
                "funnel_stage": "Awareness",
                "persona": "Consultant indépendant",
                "content_type": "articles",
                "brief": "Expliquer une tension éditoriale.",
                "locale": "fr-FR",
            }
        },
    )

    assert "structurée, accessible" in prompt
    assert "Awareness" in prompt
    assert "Consultant indépendant" in prompt
    assert "Expliquer une tension éditoriale." in prompt


def test_build_tone_judge_prompt_contains_required_json_schema() -> None:
    prompt = build_tone_judge_prompt(
        content="Texte à évaluer.",
        judge_rules={
            "context": {
                "expected_tone": "Didactique",
            }
        },
    )

    assert '"dimension": "tone"' in prompt
    assert '"criterion_scores"' in prompt
    assert '"tone.expected_tone_match"' in prompt
    assert '"tone.contextual_alignment"' in prompt
    assert '"tone.natural_expression"' in prompt

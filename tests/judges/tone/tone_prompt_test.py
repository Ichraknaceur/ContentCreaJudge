from __future__ import annotations

from contentcreajudge.judges.tone.tone_prompt import build_tone_judge_prompt


def test_build_tone_judge_prompt_includes_content() -> None:
    prompt = build_tone_judge_prompt(
        content="<p>Texte à évaluer.</p>",
        judge_rules={
            "context": {
                "expected_tone": "Pédagogique",
                "org_tones": ["posé", "pédagogique"],
            }
        },
    )

    assert "<p>Texte à évaluer.</p>" in prompt


def test_build_tone_judge_prompt_includes_expected_tone() -> None:
    prompt = build_tone_judge_prompt(
        content="Texte à évaluer.",
        judge_rules={
            "context": {
                "expected_tone": "Pédagogique",
                "org_tones": ["posé", "pédagogique"],
            }
        },
    )

    assert "Pédagogique" in prompt


def test_build_tone_judge_prompt_includes_org_tones_as_json_list() -> None:
    prompt = build_tone_judge_prompt(
        content="Texte à évaluer.",
        judge_rules={
            "context": {
                "expected_tone": "Pédagogique",
                "org_tones": ["posé", "pédagogique", "convaincant"],
            }
        },
    )

    assert '["posé", "pédagogique", "convaincant"]' in prompt


def test_build_tone_judge_prompt_uses_empty_org_tones_list_when_missing() -> None:
    prompt = build_tone_judge_prompt(
        content="Texte à évaluer.",
        judge_rules={
            "context": {
                "expected_tone": "Pédagogique",
            }
        },
    )

    assert "[]" in prompt


def test_build_tone_judge_prompt_contains_new_strategy_sections() -> None:
    prompt = build_tone_judge_prompt(
        content="Texte à évaluer.",
        judge_rules={
            "context": {
                "expected_tone": "Pédagogique",
                "org_tones": ["pédagogique"],
            }
        },
    )

    assert "PHASE 1 — OBSERVATION AVEUGLE" in prompt
    assert "PHASE 2 — DISTRIBUTION DES SCORES ORG" in prompt
    assert "PHASE 3 — ÉVALUATION PAR CRITÈRES" in prompt
    assert "blind_observation" in prompt
    assert "ton_distribution" in prompt

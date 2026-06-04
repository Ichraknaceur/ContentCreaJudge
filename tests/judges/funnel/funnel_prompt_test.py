"""Tests for the funnel prompt builder."""

from __future__ import annotations

from contentcreajudge.judges.funnel.funnel_prompt import build_funnel_prompt


def test_build_funnel_prompt_contains_expected_funnel() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "awareness",
            "criteria": {},
        },
    )

    assert "Funnel attendu :" in prompt
    assert "awareness" in prompt


def test_build_funnel_prompt_contains_content() -> None:
    content = "Ceci est un contenu pédagogique sur un sujet éditorial."

    prompt = build_funnel_prompt(
        content=content,
        judge_rules={
            "expected_funnel": "awareness",
            "criteria": {},
        },
    )

    assert "CONTENU À ÉVALUER" in prompt
    assert content in prompt


def test_build_funnel_prompt_contains_all_allowed_funnels() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "consideration",
            "criteria": {},
        },
    )

    assert "awareness" in prompt
    assert "consideration" in prompt
    assert "decision" in prompt
    assert "loyalty" in prompt


def test_build_funnel_prompt_contains_phase_1_and_phase_2() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "decision",
            "criteria": {},
        },
    )

    assert "PHASE 1 — DÉTECTION AVEUGLE DU FUNNEL" in prompt
    assert "PHASE 2 — ÉVALUATION DU FUNNEL ATTENDU" in prompt


def test_build_funnel_prompt_requires_blind_phase_1() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "loyalty",
            "criteria": {},
        },
    )

    assert "Le funnel attendu ne doit jamais influencer la Phase 1." in prompt
    assert "ignore totalement le funnel attendu" in prompt


def test_build_funnel_prompt_prevents_llm_global_score_calculation() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "awareness",
            "criteria": {},
        },
    )

    assert "Tu ne dois pas calculer de score global." in prompt
    assert "Tu ne dois pas calculer expected_funnel_score." in prompt
    assert "Tu ne dois pas calculer funnel_alignment_score." in prompt
    assert "Tu ne dois pas calculer final_score." in prompt
    assert "Tu ne dois pas déterminer le status du juge." in prompt


def test_build_funnel_prompt_contains_expected_criteria() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "awareness",
            "criteria": {
                "pedagogie": {
                    "weight": 0.30,
                    "label": "Pédagogie",
                    "description": "Mesure la pédagogie.",
                },
                "clarification_concepts": {
                    "weight": 0.25,
                    "label": "Clarification des concepts",
                    "description": "Mesure la clarification.",
                },
            },
        },
    )

    assert "Critères attendus pour ce funnel" in prompt
    assert '"pedagogie"' in prompt
    assert '"clarification_concepts"' in prompt
    assert '"weight": 0.3' in prompt
    assert '"weight": 0.25' in prompt


def test_build_funnel_prompt_contains_all_awareness_criteria_definitions() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "awareness",
            "criteria": {},
        },
    )

    assert "pedagogie (30%)" in prompt
    assert "clarification_concepts (25%)" in prompt
    assert "absence_argumentaire_commercial (20%)" in prompt
    assert "absence_orientation_conversion (15%)" in prompt
    assert "purete_funnel_awareness (10%)" in prompt


def test_build_funnel_prompt_contains_all_consideration_criteria_definitions() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "consideration",
            "criteria": {},
        },
    )

    assert "criteres_evaluation (30%)" in prompt
    assert "arbitrages (25%)" in prompt
    assert "comparaison_options (20%)" in prompt
    assert "neutralite_analytique (15%)" in prompt
    assert "purete_funnel_consideration (10%)" in prompt


def test_build_funnel_prompt_contains_all_decision_criteria_definitions() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "decision",
            "criteria": {},
        },
    )

    assert "aide_decision (30%)" in prompt
    assert "elements_reassurance (25%)" in prompt
    assert "preuves_justifications (20%)" in prompt
    assert "valeur_solution (15%)" in prompt
    assert "purete_funnel_decision (10%)" in prompt


def test_build_funnel_prompt_contains_all_loyalty_criteria_definitions() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "loyalty",
            "criteria": {},
        },
    )

    assert "approfondissement_usage (30%)" in prompt
    assert "continuite_usage (25%)" in prompt
    assert "clarifications_avancees (20%)" in prompt
    assert "valeur_long_terme (15%)" in prompt
    assert "purete_funnel_loyalty (10%)" in prompt


def test_build_funnel_prompt_output_format_does_not_include_final_scores() -> None:
    prompt = build_funnel_prompt(
        content="Contenu à évaluer.",
        judge_rules={
            "expected_funnel": "awareness",
            "criteria": {},
        },
    )

    assert '"criteria_scores": {}' in prompt
    assert '"expected_funnel_score"' not in prompt
    assert '"funnel_alignment_score"' not in prompt
    assert '"final_score"' not in prompt
    assert '"judge_status"' not in prompt

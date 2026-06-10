"""Tests for the funnel judge."""

from __future__ import annotations

import json

import pytest

from contentcreajudge.judges.funnel.funnel_judge import (
    FunnelJudgeError,
    _compute_expected_funnel_score,
    _compute_final_score,
    _compute_funnel_alignment_score,
    _parse_llm_json,
    _resolve_detected_funnel,
    run_funnel_judge,
)


def _awareness_rules() -> dict[str, object]:
    return {
        "expected_funnel": "awareness",
        "allowed_funnels": ["awareness", "consideration", "decision", "loyalty"],
        "criteria": {
            "pedagogie": {"weight": 0.30},
            "clarification_concepts": {"weight": 0.25},
            "absence_argumentaire_commercial": {"weight": 0.20},
            "absence_orientation_conversion": {"weight": 0.15},
            "purete_funnel_awareness": {"weight": 0.10},
        },
        "score_calculation": {
            "expected_funnel_weight": 0.80,
            "funnel_alignment_weight": 0.20,
            "min_score": 0,
            "max_score": 100,
        },
        "funnel_alignment": {
            "exact_match_score": 100,
            "neighbor_match_score": 50,
            "mismatch_score": 0,
            "neighbor_pairs": [
                ["awareness", "consideration"],
                ["consideration", "decision"],
                ["decision", "loyalty"],
            ],
        },
        "status_thresholds": {
            "pass_min_score": 80,
            "warning_min_score": 60,
            "fail_below_score": 60,
        },
    }


def test_parse_llm_json_returns_dict() -> None:
    result = _parse_llm_json('{"dimension": "funnel"}')

    assert result == {"dimension": "funnel"}


def test_parse_llm_json_raises_for_invalid_json() -> None:
    with pytest.raises(FunnelJudgeError):
        _parse_llm_json("not-json")


def test_resolve_detected_funnel_returns_valid_detected_funnel() -> None:
    result = _resolve_detected_funnel(
        phase_1={
            "detected_funnel": "awareness",
            "scores_by_funnel": {
                "awareness": 90,
                "consideration": 20,
                "decision": 0,
                "loyalty": 0,
            },
        },
        allowed_funnels=["awareness", "consideration", "decision", "loyalty"],
    )

    assert result == "awareness"


def test_resolve_detected_funnel_falls_back_to_highest_score() -> None:
    result = _resolve_detected_funnel(
        phase_1={
            "detected_funnel": "invalid",
            "scores_by_funnel": {
                "awareness": 40,
                "consideration": 80,
                "decision": 20,
                "loyalty": 0,
            },
        },
        allowed_funnels=["awareness", "consideration", "decision", "loyalty"],
    )

    assert result == "consideration"


def test_compute_expected_funnel_score() -> None:
    result = _compute_expected_funnel_score(
        criteria_scores={
            "pedagogie": 90,
            "clarification_concepts": 80,
            "absence_argumentaire_commercial": 100,
            "absence_orientation_conversion": 100,
            "purete_funnel_awareness": 90,
        },
        criteria_rules=_awareness_rules()["criteria"],  # type: ignore[arg-type]
    )

    assert result == 91


def test_compute_funnel_alignment_score_exact_match() -> None:
    result = _compute_funnel_alignment_score(
        detected_funnel="awareness",
        expected_funnel="awareness",
        funnel_alignment_rules=_awareness_rules()["funnel_alignment"],  # type: ignore[arg-type]
    )

    assert result == 100


def test_compute_funnel_alignment_score_neighbor_match() -> None:
    result = _compute_funnel_alignment_score(
        detected_funnel="consideration",
        expected_funnel="awareness",
        funnel_alignment_rules=_awareness_rules()["funnel_alignment"],  # type: ignore[arg-type]
    )

    assert result == 50


def test_compute_funnel_alignment_score_mismatch() -> None:
    result = _compute_funnel_alignment_score(
        detected_funnel="decision",
        expected_funnel="awareness",
        funnel_alignment_rules=_awareness_rules()["funnel_alignment"],  # type: ignore[arg-type]
    )

    assert result == 0


def test_compute_final_score() -> None:
    result = _compute_final_score(
        expected_funnel_score=80,
        funnel_alignment_score=50,
        score_calculation_rules=_awareness_rules()["score_calculation"],  # type: ignore[arg-type]
    )

    assert result == 74


def test_run_funnel_judge_with_openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_llm_response = {
        "dimension": "funnel",
        "phase_1": {
            "detected_funnel": "awareness",
            "scores_by_funnel": {
                "awareness": 90,
                "consideration": 20,
                "decision": 5,
                "loyalty": 0,
            },
            "dominant_signals": ["Le contenu explique une notion."],
            "secondary_signals": [],
        },
        "phase_2": {
            "expected_funnel": "awareness",
            "criteria_scores": {
                "pedagogie": 90,
                "clarification_concepts": 80,
                "absence_argumentaire_commercial": 100,
                "absence_orientation_conversion": 100,
                "purete_funnel_awareness": 90,
            },
            "strengths": [],
            "weaknesses": [],
        },
        "findings": [],
    }

    def fake_call_openai_json(**_: object) -> str:
        return json.dumps(fake_llm_response)

    monkeypatch.setattr(
        "contentcreajudge.judges.funnel.funnel_judge.call_openai_json",
        fake_call_openai_json,
    )

    result = run_funnel_judge(
        content="Contenu pédagogique.",
        judge_rules=_awareness_rules(),
        provider="openai",
    )

    assert result["dimension"] == "funnel"
    assert result["status"] == "pass"
    assert result["score"] == 93
    assert result["phase_1"]["detected_funnel"] == "awareness"
    assert result["phase_2"]["expected_funnel_score"] == 91
    assert result["phase_2"]["funnel_alignment_score"] == 100
    assert result["phase_2"]["final_score"] == 93

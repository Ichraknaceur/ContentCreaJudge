"""Tests for the Brief judge."""

from __future__ import annotations

import pytest

from contentcreajudge.judges.brief.brief_judge import (
    _apply_score_caps,
    _average_confidence,
    _normalize_distinctive_elements_review,
    _normalize_evaluation,
    _recalculate_score,
    _resolve_status,
    _safe_int,
)


@pytest.fixture
def brief_rules() -> dict[str, object]:
    return {
        "score_thresholds": {
            "pass": 80,
            "warn": 60,
            "fail": 0,
        },
        "criteria": {
            "angle_alignment": {"enabled": True, "weight": 0.22},
            "axis_development": {"enabled": True, "weight": 0.22},
            "intended_understanding": {"enabled": True, "weight": 0.20},
            "scope_adherence": {"enabled": True, "weight": 0.16},
            "specific_element_integration": {"enabled": True, "weight": 0.20},
        },
        "aggregation": {
            "score_caps": {
                "enabled": True,
                "specific_element_low_score_cap": {
                    "enabled": True,
                    "applies_only_when_applicable": True,
                    "threshold": 40,
                    "max_final_score": 69,
                },
            },
        },
    }


def test_safe_int_clamps_values() -> None:
    assert _safe_int(120) == 100
    assert _safe_int(-10) == 0
    assert _safe_int("75") == 75
    assert _safe_int(None) == 0
    assert _safe_int("bad") == 0


def test_resolve_status_returns_pass_warn_fail_unknown(
    brief_rules: dict[str, object],
) -> None:
    assert _resolve_status(85, brief_rules) == "pass"
    assert _resolve_status(60, brief_rules) == "warn"
    assert _resolve_status(20, brief_rules) == "fail"
    assert _resolve_status(None, brief_rules) == "unknown"


def test_resolve_status_handles_invalid_thresholds() -> None:
    rules = {
        "score_thresholds": {
            "pass": "bad",
            "warn": "bad",
        },
    }

    assert _resolve_status(85, rules) == "pass"
    assert _resolve_status(70, rules) == "warn"
    assert _resolve_status(20, rules) == "fail"


def test_normalize_evaluation_returns_required_criteria() -> None:
    parsed_response = {
        "evaluation": {
            "angle_alignment": {"score": 90, "confidence": 80},
            "axis_development": {"score": 70, "confidence": 75},
            "intended_understanding": {"score": 60, "confidence": 70},
            "scope_adherence": {"score": 50, "confidence": 65},
            "specific_element_integration": {
                "applicable": False,
            },
        }
    }

    evaluation = _normalize_evaluation(parsed_response)

    assert "angle_alignment" in evaluation
    assert "axis_development" in evaluation
    assert "intended_understanding" in evaluation
    assert "scope_adherence" in evaluation
    assert "specific_element_integration" in evaluation


def test_normalize_distinctive_elements_review() -> None:
    result = _normalize_distinctive_elements_review(
        {
            "elements": [
                {
                    "element": "part humaine du terrain",
                    "presence_in_article": "partial",
                    "evidence": "Le texte parle d'interaction, mais peu du terrain humain.",
                    "impact_on_score": "Réduit angle_alignment.",
                },
                {
                    "element": "cognition",
                    "presence_in_article": "absent",
                    "evidence": "Aucun passage ne traite la cognition.",
                    "impact_on_score": "Réduit specific_element_integration.",
                },
            ]
        }
    )

    assert result["elements"][0]["element"] == "part humaine du terrain"
    assert result["elements"][0]["presence_in_article"] == "partial"
    assert result["elements"][1]["presence_in_article"] == "absent"


def test_normalize_distinctive_elements_review_handles_invalid_input() -> None:
    assert _normalize_distinctive_elements_review(None) == {"elements": []}
    assert _normalize_distinctive_elements_review({"elements": "bad"}) == {
        "elements": []
    }


def test_normalize_distinctive_elements_review_limits_to_three_items() -> None:
    result = _normalize_distinctive_elements_review(
        {
            "elements": [
                {"element": "a", "presence_in_article": "strong"},
                {"element": "b", "presence_in_article": "partial"},
                {"element": "c", "presence_in_article": "weak"},
                {"element": "d", "presence_in_article": "absent"},
            ]
        }
    )

    assert len(result["elements"]) == 3


def test_recalculate_score_ignores_specific_element_when_not_applicable(
    brief_rules: dict[str, object],
) -> None:
    evaluation = {
        "angle_alignment": {"score": 80},
        "axis_development": {"score": 80},
        "intended_understanding": {"score": 80},
        "scope_adherence": {"score": 80},
        "specific_element_integration": {
            "applicable": False,
            "score": None,
        },
    }

    score = _recalculate_score(evaluation, brief_rules)

    assert score == 80


def test_recalculate_score_includes_specific_element_when_applicable(
    brief_rules: dict[str, object],
) -> None:
    evaluation = {
        "angle_alignment": {"score": 80},
        "axis_development": {"score": 80},
        "intended_understanding": {"score": 80},
        "scope_adherence": {"score": 80},
        "specific_element_integration": {
            "applicable": True,
            "score": 40,
        },
    }

    score = _recalculate_score(evaluation, brief_rules)

    assert score == 72


def test_recalculate_score_handles_invalid_weights() -> None:
    rules = {
        "criteria": {
            "angle_alignment": {"enabled": True, "weight": "bad"},
            "axis_development": {"enabled": True, "weight": 1},
            "intended_understanding": {"enabled": True, "weight": 0},
            "scope_adherence": {"enabled": True, "weight": 0},
        }
    }

    evaluation = {
        "angle_alignment": {"score": 90},
        "axis_development": {"score": 70},
        "intended_understanding": {"score": 60},
        "scope_adherence": {"score": 50},
    }

    score = _recalculate_score(evaluation, rules)

    assert score == 70


def test_apply_score_caps_limits_score_when_specific_element_is_low(
    brief_rules: dict[str, object],
) -> None:
    evaluation = {
        "specific_element_integration": {
            "applicable": True,
            "score": 22,
        },
    }

    capped_score = _apply_score_caps(
        score=84,
        evaluation=evaluation,
        judge_rules=brief_rules,
    )

    assert capped_score == 69


def test_apply_score_caps_does_not_apply_when_specific_element_not_applicable(
    brief_rules: dict[str, object],
) -> None:
    evaluation = {
        "specific_element_integration": {
            "applicable": False,
            "score": None,
        },
    }

    capped_score = _apply_score_caps(
        score=84,
        evaluation=evaluation,
        judge_rules=brief_rules,
    )

    assert capped_score == 84


def test_apply_score_caps_does_not_apply_when_specific_score_is_high_enough(
    brief_rules: dict[str, object],
) -> None:
    evaluation = {
        "specific_element_integration": {
            "applicable": True,
            "score": 55,
        },
    }

    capped_score = _apply_score_caps(
        score=84,
        evaluation=evaluation,
        judge_rules=brief_rules,
    )

    assert capped_score == 84


def test_average_confidence_ignores_specific_element_when_not_applicable() -> None:
    evaluation = {
        "angle_alignment": {"confidence": 80},
        "axis_development": {"confidence": 70},
        "intended_understanding": {"confidence": 60},
        "scope_adherence": {"confidence": 50},
        "specific_element_integration": {
            "applicable": False,
            "confidence": None,
        },
    }

    confidence = _average_confidence(evaluation)

    assert confidence == 65


def test_average_confidence_includes_specific_element_when_applicable() -> None:
    evaluation = {
        "angle_alignment": {"confidence": 80},
        "axis_development": {"confidence": 70},
        "intended_understanding": {"confidence": 60},
        "scope_adherence": {"confidence": 50},
        "specific_element_integration": {
            "applicable": True,
            "confidence": 40,
        },
    }

    confidence = _average_confidence(evaluation)

    assert confidence == 60

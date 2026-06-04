"""Tests for the funnel rule resolver."""

from __future__ import annotations

import pytest

from contentcreajudge.judges.funnel.exceptions import (
    MissingFunnelContextError,
    UnsupportedFunnelValueError,
)
from contentcreajudge.rules.judges.funnel.funnel_resolver import resolve_funnel_rules


def test_resolve_funnel_rules_returns_awareness_rules() -> None:
    result = resolve_funnel_rules({"expected_funnel": "awareness"})

    assert result["judge_id"] == "funnel"
    assert result["expected_funnel"] == "awareness"
    assert "criteria" in result

    criteria = result["criteria"]

    assert set(criteria.keys()) == {
        "pedagogie",
        "clarification_concepts",
        "absence_argumentaire_commercial",
        "absence_orientation_conversion",
        "purete_funnel_awareness",
    }


def test_resolve_funnel_rules_normalizes_expected_funnel() -> None:
    result = resolve_funnel_rules({"expected_funnel": " AWARENESS "})

    assert result["expected_funnel"] == "awareness"


def test_resolve_funnel_rules_raises_missing_context_error() -> None:
    with pytest.raises(MissingFunnelContextError) as exc_info:
        resolve_funnel_rules({})

    assert exc_info.value.code == "missing_funnel_context"
    assert exc_info.value.details == {"field_name": "expected_funnel"}


def test_resolve_funnel_rules_raises_unsupported_value_error() -> None:
    with pytest.raises(UnsupportedFunnelValueError) as exc_info:
        resolve_funnel_rules({"expected_funnel": "purchase"})

    assert exc_info.value.code == "unsupported_funnel_value"
    assert exc_info.value.details["field_name"] == "expected_funnel"
    assert exc_info.value.details["value"] == "purchase"
    assert exc_info.value.details["allowed_values"] == [
        "awareness",
        "consideration",
        "decision",
        "loyalty",
    ]


def test_resolve_funnel_rules_returns_score_calculation_config() -> None:
    result = resolve_funnel_rules({"expected_funnel": "consideration"})

    score_calculation = result["score_calculation"]

    assert score_calculation["expected_funnel_weight"] == 0.80
    assert score_calculation["funnel_alignment_weight"] == 0.20
    assert score_calculation["rounding"] == "nearest_integer"
    assert score_calculation["min_score"] == 0
    assert score_calculation["max_score"] == 100


def test_resolve_funnel_rules_returns_funnel_alignment_config() -> None:
    result = resolve_funnel_rules({"expected_funnel": "decision"})

    funnel_alignment = result["funnel_alignment"]

    assert funnel_alignment["exact_match_score"] == 100
    assert funnel_alignment["neighbor_match_score"] == 50
    assert funnel_alignment["mismatch_score"] == 0
    assert ["awareness", "consideration"] in funnel_alignment["neighbor_pairs"]
    assert ["consideration", "decision"] in funnel_alignment["neighbor_pairs"]
    assert ["decision", "loyalty"] in funnel_alignment["neighbor_pairs"]


def test_resolve_funnel_rules_returns_only_expected_funnel_criteria() -> None:
    result = resolve_funnel_rules({"expected_funnel": "loyalty"})

    criteria = result["criteria"]

    assert set(criteria.keys()) == {
        "approfondissement_usage",
        "continuite_usage",
        "clarifications_avancees",
        "valeur_long_terme",
        "purete_funnel_loyalty",
    }

    assert "pedagogie" not in criteria
    assert "aide_decision" not in criteria
    assert "criteres_evaluation" not in criteria


def test_resolve_funnel_rules_criteria_weights_sum_to_one() -> None:
    result = resolve_funnel_rules({"expected_funnel": "awareness"})

    criteria = result["criteria"]
    weight_sum = sum(float(rule["weight"]) for rule in criteria.values())

    assert weight_sum == pytest.approx(1.0)

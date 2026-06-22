"""Tests for the editorial style rule resolver."""

from __future__ import annotations


from contentcreajudge.rules.judges.editorial_style.editorial_style_resolver import (
    resolve_editorial_style_rules,
)


def test_resolve_editorial_style_rules_returns_expected_rules() -> None:
    """It should resolve the editorial style YAML rules."""
    rules = resolve_editorial_style_rules({})

    assert rules["judge_id"] == "editorial_style"
    assert rules["version"] == 1
    assert rules["thresholds"]["pass_score"] == 80
    assert rules["thresholds"]["warn_score"] == 60

    criteria = rules["criteria"]

    assert set(criteria.keys()) == {
        "style_alignment",
        "reasoning_alignment",
        "concept_handling",
        "expression_control",
        "writing_conventions",
        "example_alignment",
    }

    assert criteria["style_alignment"]["weight"] == 0.20
    assert criteria["reasoning_alignment"]["weight"] == 0.20
    assert criteria["concept_handling"]["weight"] == 0.15
    assert criteria["expression_control"]["weight"] == 0.15
    assert criteria["writing_conventions"]["weight"] == 0.15
    assert criteria["example_alignment"]["weight"] == 0.15


def test_resolve_editorial_style_rules_weights_sum_to_one() -> None:
    """It should resolve weights whose total equals 1.0."""
    rules = resolve_editorial_style_rules({})

    total_weight = sum(criterion["weight"] for criterion in rules["criteria"].values())

    assert round(total_weight, 6) == 1.0


def test_resolve_editorial_style_rules_returns_required_style_fields() -> None:
    """It should expose the editorial style fields expected by the judge."""
    rules = resolve_editorial_style_rules({})

    assert rules["required_style_fields"] == [
        "writingStyle",
        "writeLikeThis",
        "notLikeThis",
    ]


def test_resolve_editorial_style_rules_returns_scoring_policy() -> None:
    """It should expose scoring and severity policy."""
    rules = resolve_editorial_style_rules({})

    assert rules["severity_policy"]["critical_forces_status"] == "fail"
    assert rules["severity_policy"]["major_max_status"] == "warn"

    assert rules["scoring_caps"]["max_score_with_major_finding"] == 90
    assert rules["scoring_caps"]["max_score_with_multiple_major_findings"] == 75


def test_resolve_editorial_style_rules_ignores_context_for_now() -> None:
    """It should accept context without changing the resolved static rules."""
    rules_without_context = resolve_editorial_style_rules({})
    rules_with_context = resolve_editorial_style_rules(
        {
            "content_type": "articles",
            "locale": "fr-FR",
        }
    )

    assert rules_with_context == rules_without_context

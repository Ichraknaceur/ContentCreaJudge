from __future__ import annotations

import pytest

from contentcreajudge.rules.judges.seo.seo_resolver import resolve_seo_rules


def make_context(**overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "content_type": "articles",
        "expected_length": "MEDIUM",
        "funnel_stage": "AWARENESS",
        "locale": "fr-FR",
        "main_keyword": "différenciation éditoriale en milieu saturé",
        "secondary_keywords": [
            "singularite de la ligne editoriale",
            "coherence de la voix editoriale",
        ],
        "long_tail_keywords": [
            "selection d angles originaux pour des thematiques marketing tres concurrentielles",
        ],
    }
    context.update(overrides)
    return context


def test_resolve_seo_rules_with_medium_length() -> None:
    result = resolve_seo_rules(make_context())

    assert result["judge_id"] == "seo"
    assert result["content_type"] == "articles"
    assert result["expected_length"] == "MEDIUM"
    assert result["funnel_stage"] == "AWARENESS"
    assert result["locale"] == "fr-FR"
    assert result["main_keyword"] == "différenciation éditoriale en milieu saturé"
    assert result["secondary_keywords"] == [
        "singularite de la ligne editoriale",
        "coherence de la voix editoriale",
    ]
    assert result["long_tail_keywords"] == [
        "selection d angles originaux pour des thematiques marketing tres concurrentielles",
    ]

    assert result["keyword_occurrence_rules"] == {
        "enforce_minimum_occurrences": True,
        "min_total": 7,
        "max_total": 10,
        "min_main": None,
    }
    assert result["long_tail_keyword_rules"]["allow_long_tail_keywords"] is True
    assert (
        result["long_tail_keyword_rules"]["awareness_simple_exception_applied"] is False
    )
    assert result["main_keyword_rules"]["require_presence"] is True
    assert result["secondary_keyword_rules"]["forbid_artificial_grouping"] is True
    assert result["keyword_integrity_rules"]["forbid_rephrasing"] is True
    assert (
        result["keyword_distribution_rules"][
            "require_at_least_one_secondary_or_long_tail_per_h2_section"
        ]
        is True
    )
    assert (
        result["readability_priority_rules"]["coherence_over_forced_insertion"] is True
    )
    assert result["over_optimization_rules"]["max_identical_long_tail_occurrences"] == 2
    assert result["formatting_constraints_rules"][
        "forbid_emphasis_tags_on_keywords"
    ] == [
        "em",
        "strong",
    ]
    assert len(result["rules"]) == 10
    assert "main_keyword_presence" in result["messages"]


def test_resolve_seo_rules_applies_awareness_simple_exception() -> None:
    result = resolve_seo_rules(
        make_context(
            expected_length="SIMPLE",
            long_tail_keywords=[
                "repetition strategique du message sans impression de deja vu en b2b",
            ],
        ),
    )

    assert result["expected_length"] == "SIMPLE"
    assert result["funnel_stage"] == "AWARENESS"
    assert result["long_tail_keywords"] == []
    assert result["keyword_occurrence_rules"] == {
        "enforce_minimum_occurrences": True,
        "min_total": 5,
        "max_total": None,
        "min_main": 3,
    }
    assert result["long_tail_keyword_rules"]["allow_long_tail_keywords"] is False
    assert (
        result["long_tail_keyword_rules"]["awareness_simple_exception_applied"] is True
    )


def test_resolve_seo_rules_with_long_length_keeps_long_tail_keywords() -> None:
    result = resolve_seo_rules(
        make_context(
            expected_length="LONG",
            funnel_stage="DECISION",
            long_tail_keywords=["comparatif detaille de solutions editoriales b2b"],
        ),
    )

    assert result["expected_length"] == "LONG"
    assert result["funnel_stage"] == "DECISION"
    assert result["long_tail_keywords"] == [
        "comparatif detaille de solutions editoriales b2b",
    ]
    assert result["keyword_occurrence_rules"] == {
        "enforce_minimum_occurrences": True,
        "min_total": 10,
        "max_total": 15,
        "min_main": None,
    }
    assert result["long_tail_keyword_rules"]["allow_long_tail_keywords"] is True
    assert (
        result["long_tail_keyword_rules"]["awareness_simple_exception_applied"] is False
    )


@pytest.mark.parametrize(
    ("context_overrides", "message"),
    [
        ({"content_type": None}, "Missing context.content_type for SEO evaluation."),
        (
            {"expected_length": None},
            "Missing context.expected_length for SEO evaluation.",
        ),
        ({"expected_length": "SHORT"}, "Unknown expected_length: SHORT"),
        ({"funnel_stage": None}, "Missing context.funnel_stage for SEO evaluation."),
        ({"funnel_stage": "RETENTION"}, "Unknown funnel_stage: RETENTION"),
        ({"main_keyword": None}, "Missing context.main_keyword for SEO evaluation."),
        (
            {"secondary_keywords": "not-a-list"},
            "context.secondary_keywords must be a list.",
        ),
        (
            {"long_tail_keywords": "not-a-list"},
            "context.long_tail_keywords must be a list.",
        ),
    ],
)
def test_resolve_seo_rules_validation_errors(
    context_overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=f"^{message}$"):
        resolve_seo_rules(make_context(**context_overrides))

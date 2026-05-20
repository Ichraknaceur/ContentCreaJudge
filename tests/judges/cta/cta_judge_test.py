"""Tests for CTA judge logic."""

from __future__ import annotations

from contentcreajudge.judges.cta.cta_judge import (
    _get_allowed_labels,
    _get_forbidden_labels,
    _get_message,
    _is_cta_after_quiz_correction,
    _is_cta_at_end,
    _is_cta_before_complementary_reading,
    _is_educational_purpose,
    _is_language_consistent,
    _looks_like_awareness_cta,
    _looks_like_decision_cta,
    run_cta_judge,
)
from contentcreajudge.preprocessing.cta_preprocessor import preprocess_cta_content
from contentcreajudge.rules.judges.cta.cta_resolver import resolve_cta_rules


def _rules(
    expected_cta: str | None = "Read more",
    funnel_stage: str = "AWARENESS",
    content_type: str = "articles",
    content_purpose: str | None = "Sensibilisation",
    language: str = "en",
) -> dict[str, object]:
    return resolve_cta_rules(
        {
            "expected_cta": expected_cta,
            "funnel_stage": funnel_stage,
            "content_type": content_type,
            "content_purpose": content_purpose,
            "language": language,
        }
    )


def test_cta_judge_passes_valid_cta_at_end() -> None:
    content = '<p>Intro</p><p class="cta"><strong>Read more</strong></p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(),
    )

    assert result["status"] == "pass"
    assert result["score"] == 100


def test_get_message_returns_key_when_messages_is_not_a_dict() -> None:
    assert _get_message({"messages": "invalid"}, "position") == "position"


def test_get_allowed_labels_accepts_language_agnostic_list() -> None:
    judge_rules = _rules()
    judge_rules["funnel_alignment"]["expected_by_funnel"]["AWARENESS"][
        "allowed_cta_labels"
    ] = ["Read more"]

    assert _get_allowed_labels(judge_rules) == ["Read more"]


def test_get_forbidden_labels_accepts_language_agnostic_list() -> None:
    judge_rules = _rules()
    judge_rules["funnel_alignment"]["expected_by_funnel"]["AWARENESS"][
        "forbidden_cta_labels"
    ] = ["Buy"]

    assert _get_forbidden_labels(judge_rules) == ["Buy"]


def test_is_cta_at_end_returns_false_without_cta() -> None:
    preprocessed_content = preprocess_cta_content("<p>Intro</p><p>Conclusion</p>")

    assert _is_cta_at_end(preprocessed_content) is False


def test_is_cta_before_complementary_reading_returns_false_without_indexes() -> None:
    preprocessed_content = preprocess_cta_content(
        '<p>Intro</p><p class="cta"><strong>Read more</strong></p>'
    )

    assert _is_cta_before_complementary_reading(preprocessed_content) is False


def test_is_cta_after_quiz_correction_returns_false_without_quiz_indexes() -> None:
    preprocessed_content = preprocess_cta_content(
        '<p>Intro</p><p class="cta"><strong>Read more</strong></p>'
    )

    assert _is_cta_after_quiz_correction(preprocessed_content) is False


def test_is_educational_purpose_returns_false_when_purpose_is_missing() -> None:
    assert _is_educational_purpose(_rules(content_purpose=None)) is False


def test_is_language_consistent_returns_true_when_no_allowed_labels_exist() -> None:
    judge_rules = _rules()
    judge_rules["funnel_alignment"]["expected_by_funnel"]["AWARENESS"][
        "allowed_cta_labels"
    ] = []

    assert _is_language_consistent(judge_rules, "Any CTA") is True


def test_cta_judge_fails_when_cta_is_missing() -> None:
    content = "<p>Intro</p><p>Conclusion</p>"

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(),
    )

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["findings"][0]["rule_id"] == "cta.presence_when_required"


def test_cta_judge_fails_when_cta_text_mismatches() -> None:
    content = '<p>Intro</p><p class="cta"><strong>Discover</strong></p>'
    judge_rules = _rules(expected_cta="Read more")
    judge_rules["semantic_fallback"][
        "allow_semantic_check_for_unknown_or_custom_cta"
    ] = False

    result = run_cta_judge(
        preprocess_cta_content(content),
        judge_rules,
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.exact_text_match" in rule_ids


def test_cta_judge_is_not_applicable_without_expected_cta_and_without_cta() -> None:
    content = "<p>Intro</p><p>Conclusion</p>"

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta=None),
    )

    assert result["status"] == "not_applicable"
    assert result["score"] == 100
    assert result["findings"][0]["rule_id"] == "cta.not_applicable"


def test_cta_judge_fails_when_multiple_ctas_exist() -> None:
    content = (
        "<p>Intro</p>"
        '<p class="cta"><strong>Read more</strong></p>'
        '<p class="cta"><strong>Read more</strong></p>'
    )

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.single_main_cta" in rule_ids


def test_cta_judge_fails_when_cta_has_bad_html_format() -> None:
    content = '<p>Intro</p><p class="cta">Read more</p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.html_format" in rule_ids


def test_cta_judge_fails_when_cta_is_not_at_end() -> None:
    content = (
        "<p>Intro</p>"
        '<p class="cta"><strong>Read more</strong></p>'
        "<p>Conclusion after CTA</p>"
    )

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.position" in rule_ids


def test_cta_judge_passes_when_read_more_is_omitted_with_complementary_reading() -> (
    None
):
    content = "<p>Intro</p><h2>Lecture complémentaire</h2><ul><li>Article</li></ul>"

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta="Read more"),
    )

    assert result["status"] == "pass"
    assert result["score"] == 100


def test_cta_judge_fails_when_read_more_exists_with_complementary_reading() -> None:
    content = (
        "<p>Intro</p>"
        '<p class="cta"><strong>Read more</strong></p>'
        "<h2>Lecture complémentaire</h2>"
        "<ul><li>Article</li></ul>"
    )

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta="Read more"),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.complementary_reading_conflict" in rule_ids


def test_cta_judge_fails_for_sales_cta_in_awareness() -> None:
    content = '<p>Intro</p><p class="cta"><strong>Buy</strong></p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta="Buy", funnel_stage="AWARENESS", language="en"),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.funnel_alignment" in rule_ids


def test_cta_judge_rejects_decision_like_cta_in_awareness_before_semantic_fallback() -> (
    None
):
    content = '<p>Intro</p><p class="cta"><strong>Demander une démo</strong></p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta="Demander une démo", funnel_stage="AWARENESS"),
    )

    funnel_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "cta.funnel_alignment"
    )

    assert result["status"] == "fail"
    assert funnel_finding["evidence"]["reason"] == (
        "CTA intent is incompatible with this funnel stage."
    )


def test_cta_judge_passes_decision_cta() -> None:
    content = '<p>Intro</p><p class="cta"><strong>Contact us</strong></p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(
            expected_cta="Contact us",
            funnel_stage="DECISION",
            content_purpose="Conversion",
            language="en",
        ),
    )

    assert result["status"] == "pass"
    assert result["score"] == 100


def test_cta_judge_rejects_awareness_like_cta_in_decision_before_semantic_fallback() -> (
    None
):
    content = '<p>Intro</p><p class="cta"><strong>Learn more</strong></p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(
            expected_cta="Learn more",
            funnel_stage="DECISION",
            content_purpose="Conversion",
        ),
    )

    funnel_finding = next(
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "cta.funnel_alignment"
    )

    assert result["status"] == "fail"
    assert funnel_finding["evidence"]["reason"] == (
        "CTA intent is incompatible with this funnel stage."
    )


def test_cta_judge_validates_quiz_position() -> None:
    content = (
        "<ol><li><p><strong>Q1 - Question</strong></p></li></ol>"
        "<h2>Corrigé du quiz</h2>"
        "<ol><li><p>Réponse correcte : A</p></li></ol>"
        '<p class="cta"><strong>Read more</strong></p>'
    )

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(content_type="quiz"),
    )

    assert result["status"] == "pass"
    assert result["score"] == 100


def test_cta_judge_fails_when_quiz_cta_is_not_after_correction_at_end() -> None:
    content = (
        "<ol><li><p><strong>Q1 â€“ Question</strong></p></li></ol>"
        '<p class="cta"><strong>Read more</strong></p>'
        "<h2>CorrigÃ© du quiz</h2>"
        "<ol><li><p>RÃ©ponse correcte : A</p></li></ol>"
    )

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(content_type="quiz"),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.quiz_position" in rule_ids


def test_cta_judge_fails_when_cta_is_not_immediately_before_complementary_reading() -> (
    None
):
    content = (
        "<p>Intro</p>"
        '<p class="cta"><strong>Explore</strong></p>'
        "<p>Bridge paragraph</p>"
        "<h2>Learn more</h2>"
        "<ul><li>Related article</li></ul>"
    )

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta="Explore"),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.position" in rule_ids


def test_cta_judge_fails_when_cta_is_not_in_allowed_labels() -> None:
    content = '<p>Intro</p><p class="cta"><strong>Keep reading</strong></p>'
    judge_rules = _rules(expected_cta="Keep reading")
    judge_rules["semantic_fallback"]["enabled"] = False

    result = run_cta_judge(
        preprocess_cta_content(content),
        judge_rules,
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert result["status"] == "fail"
    assert "cta.funnel_alignment" in rule_ids


def test_cta_judge_flags_empty_anchor() -> None:
    content = '<p>Intro</p><p class="cta"><strong> </strong></p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta=None),
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "cta.anchor_quality" in rule_ids


def test_cta_judge_flags_vague_anchor_when_it_differs_from_expected_cta() -> None:
    content = '<p>Intro</p><p class="cta"><strong>More</strong></p>'

    result = run_cta_judge(
        preprocess_cta_content(content),
        _rules(expected_cta="Read more"),
    )

    anchor_findings = [
        finding
        for finding in result["findings"]
        if finding["rule_id"] == "cta.anchor_quality"
    ]

    assert anchor_findings
    assert anchor_findings[0]["evidence"]["observed_cta"] == "More"


def test_cta_judge_flags_language_inconsistency_when_override_is_disabled() -> None:
    content = '<p>Intro</p><p class="cta"><strong>Read more</strong></p>'
    judge_rules = _rules(expected_cta="Read more", language="fr")
    judge_rules["language_policy"][
        "allow_input_language_to_override_output_language"
    ] = False

    result = run_cta_judge(
        preprocess_cta_content(content),
        judge_rules,
    )

    rule_ids = [finding["rule_id"] for finding in result["findings"]]

    assert "cta.language_consistency" in rule_ids


def test_looks_like_decision_cta_uses_configured_markers() -> None:
    assert _looks_like_decision_cta("Planifier un appel", _rules()) is True


def test_looks_like_awareness_cta_uses_configured_markers() -> None:
    assert _looks_like_awareness_cta("Read more", _rules()) is True


def test_cta_judge_returns_warn_when_only_minor_findings_exist() -> None:
    content = '<p>Intro</p><p class="cta"><strong> </strong></p>'
    judge_rules = _rules(expected_cta=None)
    judge_rules["funnel_alignment"]["expected_by_funnel"]["AWARENESS"][
        "allowed_cta_labels"
    ] = []
    judge_rules["funnel_alignment"]["expected_by_funnel"]["AWARENESS"][
        "forbidden_cta_labels"
    ] = []

    result = run_cta_judge(
        preprocess_cta_content(content),
        judge_rules,
    )

    assert result["status"] == "warn"
    assert result["score"] == 80

from __future__ import annotations

from contentcreajudge.judges.length.length_judge import run_length_judge

BASE_RULES = {
    "min_words": 1000,
    "max_words": 2000,
    "tolerance_pct": 10,
}


def test_run_length_judge_passes_when_word_count_is_inside_expected_range() -> None:
    """Pass when the word count is within the expected range."""
    result = run_length_judge(
        preprocessed_content={"word_count": 1500},
        judge_rules=BASE_RULES,
    )

    assert result["dimension"] == "length"
    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["applied_rule"] == {
        "content_type": None,
        "expected_length": None,
        "min_words": 1000,
        "max_words": 2000,
        "tolerance_pct": 10.0,
        "tolerated_min": 900,
        "tolerated_max": 2200,
    }
    assert result["findings"][0]["rule_id"] == "length.valid"
    assert result["findings"][0]["severity"] == "info"


def test_run_length_judge_passes_when_word_count_is_on_tolerated_min_boundary() -> None:
    """Pass when the word count equals the tolerated minimum."""
    result = run_length_judge(
        preprocessed_content={"word_count": 900},
        judge_rules=BASE_RULES,
    )

    assert result["status"] == "pass"
    assert result["findings"][0]["rule_id"] == "length.valid"
    assert result["findings"][0]["evidence"]["tolerated_min"] == 900


def test_run_length_judge_passes_when_word_count_is_on_tolerated_max_boundary() -> None:
    """Pass when the word count equals the tolerated maximum."""
    result = run_length_judge(
        preprocessed_content={"word_count": 2200},
        judge_rules=BASE_RULES,
    )

    assert result["status"] == "pass"
    assert result["findings"][0]["rule_id"] == "length.valid"
    assert result["findings"][0]["evidence"]["tolerated_max"] == 2200


def test_run_length_judge_fails_when_word_count_is_below_tolerated_min() -> None:
    """Fail when the word count is below the tolerated minimum."""
    result = run_length_judge(
        preprocessed_content={"word_count": 899},
        judge_rules=BASE_RULES,
    )

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["findings"][0]["rule_id"] == "length.too_short"
    assert result["findings"][0]["severity"] == "major"
    assert result["findings"][0]["message"] == (
        "Word count is below the tolerated expected range."
    )


def test_run_length_judge_fails_when_word_count_is_above_tolerated_max() -> None:
    """Fail when the word count is above the tolerated maximum."""
    result = run_length_judge(
        preprocessed_content={"word_count": 2201},
        judge_rules=BASE_RULES,
    )

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["findings"][0]["rule_id"] == "length.too_long"
    assert result["findings"][0]["severity"] == "major"
    assert result["findings"][0]["message"] == (
        "Word count is above the tolerated expected range."
    )


def test_run_length_judge_passes_without_max_words_above_min() -> None:
    """Pass when no maximum word count is configured."""
    rules = {
        "min_words": 1500,
        "max_words": None,
        "tolerance_pct": 10,
    }

    result = run_length_judge(
        preprocessed_content={"word_count": 5000},
        judge_rules=rules,
    )

    assert result["status"] == "pass"
    assert result["findings"][0]["rule_id"] == "length.valid"
    assert result["findings"][0]["evidence"]["tolerated_max"] is None


def test_run_length_judge_uses_zero_tolerance_when_missing() -> None:
    """Use zero tolerance when no tolerance value is provided."""
    rules = {
        "min_words": 1000,
        "max_words": 2000,
    }

    result = run_length_judge(
        preprocessed_content={"word_count": 999},
        judge_rules=rules,
    )

    assert result["status"] == "fail"
    assert result["findings"][0]["rule_id"] == "length.too_short"
    assert result["findings"][0]["evidence"]["tolerance_pct"] == 0.0
    assert result["findings"][0]["evidence"]["tolerated_min"] == 1000
    assert result["findings"][0]["evidence"]["tolerated_max"] == 2000


def test_run_length_judge_accepts_numeric_values_as_strings() -> None:
    """Accept numeric rule and word-count values provided as strings."""
    rules = {
        "min_words": "1000",
        "max_words": "2000",
        "tolerance_pct": "10",
    }

    result = run_length_judge(
        preprocessed_content={"word_count": "1500"},
        judge_rules=rules,
    )

    assert result["status"] == "pass"
    assert result["findings"][0]["evidence"] == {
        "word_count": 1500,
        "expected_min": 1000,
        "expected_max": "2000",
        "tolerance_pct": 10.0,
        "tolerated_min": 900,
        "tolerated_max": 2200,
    }

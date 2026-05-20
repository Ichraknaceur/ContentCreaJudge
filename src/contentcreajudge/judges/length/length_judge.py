"""Judge logic for content length evaluation."""

from __future__ import annotations


def run_length_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate content length using the expected range and tolerance."""
    messages = judge_rules.get("messages", {})
    word_count = int(preprocessed_content["word_count"])
    min_words = int(judge_rules["min_words"])
    max_words = judge_rules["max_words"]
    tolerance_pct = float(judge_rules.get("tolerance_pct", 0))

    tolerated_min_words = int(min_words * (1 - tolerance_pct / 100))

    tolerated_max_words = None
    if max_words is not None:
        tolerated_max_words = int(int(max_words) * (1 + tolerance_pct / 100))

    applied_rule = {
        "content_type": judge_rules.get("content_type"),
        "expected_length": judge_rules.get("expected_length"),
        "min_words": min_words,
        "max_words": max_words,
        "tolerance_pct": tolerance_pct,
        "tolerated_min": tolerated_min_words,
        "tolerated_max": tolerated_max_words,
    }

    evidence = {
        "word_count": word_count,
        "expected_min": min_words,
        "expected_max": max_words,
        "tolerance_pct": tolerance_pct,
        "tolerated_min": tolerated_min_words,
        "tolerated_max": tolerated_max_words,
    }

    if word_count < tolerated_min_words:
        return {
            "dimension": "length",
            "status": "fail",
            "score": 0,
            "applied_rule": applied_rule,
            "findings": [
                {
                    "rule_id": "length.too_short",
                    "severity": "major",
                    "message": messages.get(
                        "too_short", "Word count is below the tolerated expected range."
                    ),
                    "evidence": evidence,
                },
            ],
        }

    if tolerated_max_words is not None and word_count > tolerated_max_words:
        return {
            "dimension": "length",
            "status": "fail",
            "score": 0,
            "applied_rule": applied_rule,
            "findings": [
                {
                    "rule_id": "length.too_long",
                    "severity": "major",
                    "message": messages.get(
                        "too_long", "Word count is above the tolerated expected range."
                    ),
                    "evidence": evidence,
                },
            ],
        }

    return {
        "dimension": "length",
        "status": "pass",
        "score": 100,
        "applied_rule": applied_rule,
        "findings": [
            {
                "rule_id": "length.valid",
                "severity": "info",
                "message": messages.get(
                    "valid", "Word count is within the tolerated expected range."
                ),
                "evidence": evidence,
            },
        ],
    }

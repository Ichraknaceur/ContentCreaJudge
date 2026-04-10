"""Judge logic for content length evaluation."""

from __future__ import annotations


def run_length_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Receives the preprocessed text and the YAML rules, then evaluates the content against those rules"""
    word_count = int(preprocessed_content["word_count"])
    min_words = int(judge_rules["min_words"])
    max_words = judge_rules["max_words"]
    
    # Cas 1 : si c'est trop court
    if word_count < min_words:
        return {
            "dimension": "length",
            "status": "fail",
            "score": 0,
            "applied_rule": judge_rules,
            "findings": [
                {
                    "rule_id": "length.too_short",
                    "severity": "major",
                    "message": "Word count is below the expected range.",
                    "evidence": {
                        "word_count": word_count,
                        "expected_min": min_words,
                        "expected_max": max_words,
                    },
                }
            ],
        }

    # Cas 2 : si c'est trop long
    if max_words is not None and word_count > int(max_words):
        return {
            "dimension": "length",
            "status": "fail",
            "score": 0,
            "applied_rule": judge_rules,
            "findings": [
                {
                    "rule_id": "length.too_long",
                    "severity": "major",
                    "message": "Word count is above the expected range.",
                    "evidence": {
                        "word_count": word_count,
                        "expected_min": min_words,
                        "expected_max": max_words,
                    },
                }
            ],
        }

    # Cas 3 : si la longueur est dans la borne 
    return {
        "dimension": "length",
        "status": "pass",
        "score": 100,
        "applied_rule": judge_rules,
        "findings": [
            {
                "rule_id": "length.valid",
                "severity": "info",
                "message": "Word count is within the expected range.",
                "evidence": {
                    "word_count": word_count,
                    "expected_min": min_words,
                    "expected_max": max_words,
                },
            }
        ],
    }
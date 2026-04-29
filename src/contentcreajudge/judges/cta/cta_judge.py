"""Judge logic for CTA evaluation."""

from __future__ import annotations

import unicodedata


def _normalize(value: object) -> str:
    """Normalize text for comparison."""
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())


def _get_message(judge_rules: dict[str, object], key: str) -> str:
    messages = judge_rules.get("messages", {})
    if isinstance(messages, dict):
        return str(messages.get(key, key))
    return key


def _finding(
    rule_id: str,
    severity: str,
    message: str,
    evidence: dict[str, object],
) -> dict[str, object]:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def _is_read_more(value: object) -> bool:
    return _normalize(value) in {"read more", "learn more", "lire la suite"}


def _get_allowed_labels(judge_rules: dict[str, object]) -> list[str]:
    funnel_alignment = judge_rules["funnel_alignment"]
    funnel_stage = str(judge_rules["funnel_stage"])
    language = str(judge_rules.get("language", "fr"))

    expected_by_funnel = funnel_alignment["expected_by_funnel"]
    funnel_rules = expected_by_funnel[funnel_stage]
    allowed_labels = funnel_rules.get("allowed_cta_labels", {})

    if isinstance(allowed_labels, dict):
        labels = allowed_labels.get(language, [])
        return [str(label) for label in labels]

    return []


def _get_forbidden_labels(judge_rules: dict[str, object]) -> list[str]:
    funnel_alignment = judge_rules["funnel_alignment"]
    funnel_stage = str(judge_rules["funnel_stage"])
    language = str(judge_rules.get("language", "fr"))

    expected_by_funnel = funnel_alignment["expected_by_funnel"]
    funnel_rules = expected_by_funnel[funnel_stage]
    forbidden_labels = funnel_rules.get("forbidden_cta_labels", {})

    if isinstance(forbidden_labels, dict):
        labels = forbidden_labels.get(language, [])
        return [str(label) for label in labels]

    return []


def _is_cta_at_end(preprocessed_content: dict[str, object]) -> bool:
    cta_blocks = preprocessed_content["cta_blocks"]
    top_level_tag_count = int(preprocessed_content["top_level_tag_count"])

    if not cta_blocks:
        return False

    last_cta = cta_blocks[-1]
    return int(last_cta["index"]) == top_level_tag_count - 1


def _is_cta_before_complementary_reading(
    preprocessed_content: dict[str, object],
) -> bool:
    cta_blocks = preprocessed_content["cta_blocks"]
    complementary_indexes = preprocessed_content["complementary_reading_indexes"]

    if not cta_blocks or not complementary_indexes:
        return False

    last_cta_index = int(cta_blocks[-1]["index"])
    first_complementary_index = int(complementary_indexes[0])

    return last_cta_index == first_complementary_index - 1


def _is_cta_after_quiz_correction(preprocessed_content: dict[str, object]) -> bool:
    cta_blocks = preprocessed_content["cta_blocks"]
    quiz_indexes = preprocessed_content["quiz_correction_indexes"]

    if not cta_blocks or not quiz_indexes:
        return False

    last_cta_index = int(cta_blocks[-1]["index"])
    last_quiz_index = int(quiz_indexes[-1])

    return last_cta_index > last_quiz_index and _is_cta_at_end(preprocessed_content)


def _is_educational_purpose(judge_rules: dict[str, object]) -> bool:
    content_purpose = judge_rules.get("content_purpose")
    if not content_purpose:
        return False

    purpose_rules = judge_rules["content_purpose_alignment"]
    educational_purposes = purpose_rules.get("educational_purposes", [])

    normalized_purpose = _normalize(content_purpose)
    return normalized_purpose in {_normalize(purpose) for purpose in educational_purposes}


def _is_language_consistent(judge_rules: dict[str, object], cta_text: str) -> bool:
    language = str(judge_rules.get("language", "fr"))
    allowed_labels = _get_allowed_labels(judge_rules)

    if not allowed_labels:
        return True

    normalized_cta = _normalize(cta_text)
    normalized_allowed = {_normalize(label) for label in allowed_labels}

    if normalized_cta in normalized_allowed:
        return True

    language_policy = judge_rules["language_policy"]
    return bool(language_policy.get("allow_input_language_to_override_output_language", True))


def run_cta_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate CTA compliance from preprocessed content and resolved rules."""

    findings: list[dict[str, object]] = []

    expected_cta = judge_rules.get("expected_cta")
    expected_cta_text = str(expected_cta).strip() if expected_cta else None

    cta_blocks = preprocessed_content["cta_blocks"]
    cta_count = int(preprocessed_content["cta_count"])
    has_cta = bool(preprocessed_content["has_cta"])
    has_complementary_reading = bool(
        preprocessed_content["has_complementary_reading"]
    )
    content_type = str(judge_rules["content_type"])
    funnel_stage = str(judge_rules["funnel_stage"])

    should_omit_read_more = (
        has_complementary_reading
        and expected_cta_text is not None
        and _is_read_more(expected_cta_text)
    )

    if not expected_cta_text and not has_cta:
        return {
            "dimension": "cta",
            "status": "not_applicable",
            "score": 100,
            "applied_rule": judge_rules,
            "findings": [
                _finding(
                    "cta.not_applicable",
                    "info",
                    _get_message(judge_rules, "not_applicable"),
                    {"reason": "No expected CTA was provided."},
                )
            ],
        }

    if should_omit_read_more:
        if has_cta:
            findings.append(
                _finding(
                    "cta.absence_when_forbidden",
                    "major",
                    _get_message(judge_rules, "absence_when_forbidden"),
                    {
                        "expected_cta": expected_cta_text,
                        "reason": "Read more CTA must be omitted when complementary reading exists.",
                    },
                )
            )

            findings.append(
                _finding(
                    "cta.complementary_reading_conflict",
                    "major",
                    _get_message(judge_rules, "complementary_reading_conflict"),
                    {
                        "has_complementary_reading": has_complementary_reading,
                        "cta_texts": preprocessed_content["cta_texts"],
                    },
                )
            )
        else:
            return {
                "dimension": "cta",
                "status": "pass",
                "score": 100,
                "applied_rule": judge_rules,
                "findings": [
                    _finding(
                        "cta.absence_when_forbidden",
                        "info",
                        "The Read more CTA was correctly omitted.",
                        {
                            "expected_cta": expected_cta_text,
                            "has_complementary_reading": True,
                        },
                    )
                ],
            }

    if expected_cta_text and not has_cta and not should_omit_read_more:
        findings.append(
            _finding(
                "cta.presence_when_required",
                "major",
                _get_message(judge_rules, "presence_when_required"),
                {"expected_cta": expected_cta_text},
            )
        )

    if cta_count > 1:
        findings.append(
            _finding(
                "cta.single_main_cta",
                "major",
                _get_message(judge_rules, "single_main_cta"),
                {"cta_count": cta_count},
            )
        )

    if has_cta:
        first_cta = cta_blocks[0]
        cta_text = str(first_cta["text"])
        strong_text = first_cta.get("strong_text")

        if expected_cta_text and _normalize(cta_text) != _normalize(expected_cta_text):
            findings.append(
                _finding(
                    "cta.exact_text_match",
                    "major",
                    _get_message(judge_rules, "exact_text_match"),
                    {
                        "expected_cta": expected_cta_text,
                        "observed_cta": cta_text,
                    },
                )
            )

        if (
            first_cta.get("tag_name") != "p"
            or "cta" not in first_cta.get("classes", [])
            or not first_cta.get("has_strong")
            or _normalize(strong_text) != _normalize(cta_text)
        ):
            findings.append(
                _finding(
                    "cta.html_format",
                    "major",
                    _get_message(judge_rules, "html_format"),
                    {
                        "observed_html": first_cta.get("html"),
                        "expected_format": judge_rules["html_format"].get(
                            "expected_format"
                        ),
                    },
                )
            )

        if content_type == "quiz":
            if not _is_cta_after_quiz_correction(preprocessed_content):
                findings.append(
                    _finding(
                        "cta.quiz_position",
                        "major",
                        _get_message(judge_rules, "quiz_position"),
                        {
                            "cta_index": first_cta["index"],
                            "quiz_correction_indexes": preprocessed_content[
                                "quiz_correction_indexes"
                            ],
                        },
                    )
                )
        elif has_complementary_reading:
            if not _is_cta_before_complementary_reading(preprocessed_content):
                findings.append(
                    _finding(
                        "cta.position",
                        "major",
                        _get_message(judge_rules, "position"),
                        {
                            "cta_index": first_cta["index"],
                            "complementary_reading_indexes": preprocessed_content[
                                "complementary_reading_indexes"
                            ],
                        },
                    )
                )
        elif not _is_cta_at_end(preprocessed_content):
            findings.append(
                _finding(
                    "cta.position",
                    "major",
                    _get_message(judge_rules, "position"),
                    {
                        "cta_index": first_cta["index"],
                        "top_level_tag_count": preprocessed_content[
                            "top_level_tag_count"
                        ],
                    },
                )
            )

        allowed_labels = {_normalize(label) for label in _get_allowed_labels(judge_rules)}
        forbidden_labels = {
            _normalize(label) for label in _get_forbidden_labels(judge_rules)
        }
        normalized_cta = _normalize(cta_text)

        if normalized_cta in forbidden_labels:
            findings.append(
                _finding(
                    "cta.funnel_alignment",
                    "major",
                    _get_message(judge_rules, "funnel_alignment"),
                    {
                        "funnel_stage": funnel_stage,
                        "observed_cta": cta_text,
                        "reason": "CTA is forbidden for this funnel stage.",
                    },
                )
            )
        elif allowed_labels and normalized_cta not in allowed_labels:
            findings.append(
                _finding(
                    "cta.funnel_alignment",
                    "major",
                    _get_message(judge_rules, "funnel_alignment"),
                    {
                        "funnel_stage": funnel_stage,
                        "observed_cta": cta_text,
                        "allowed_labels": _get_allowed_labels(judge_rules),
                    },
                )
            )

        if _is_educational_purpose(judge_rules):
            forbidden_for_purpose = forbidden_labels
            if normalized_cta in forbidden_for_purpose:
                findings.append(
                    _finding(
                        "cta.content_purpose_alignment",
                        "major",
                        _get_message(judge_rules, "content_purpose_alignment"),
                        {
                            "content_purpose": judge_rules.get("content_purpose"),
                            "observed_cta": cta_text,
                        },
                    )
                )

        vague_anchors = judge_rules["anchor_quality"].get("vague_anchors", {})
        language = str(judge_rules.get("language", "fr"))
        vague_labels = vague_anchors.get(language, []) if isinstance(vague_anchors, dict) else []

        if not cta_text.strip():
            findings.append(
                _finding(
                    "cta.anchor_quality",
                    "minor",
                    _get_message(judge_rules, "anchor_quality"),
                    {"reason": "CTA anchor is empty."},
                )
            )
        elif _normalize(cta_text) in {_normalize(label) for label in vague_labels}:
            if expected_cta_text and _normalize(cta_text) != _normalize(expected_cta_text):
                findings.append(
                    _finding(
                        "cta.anchor_quality",
                        "minor",
                        _get_message(judge_rules, "anchor_quality"),
                        {"observed_cta": cta_text},
                    )
                )

        if not _is_language_consistent(judge_rules, cta_text):
            findings.append(
                _finding(
                    "cta.language_consistency",
                    "minor",
                    _get_message(judge_rules, "language_consistency"),
                    {
                        "language": language,
                        "observed_cta": cta_text,
                    },
                )
            )

    major_findings = [
        finding for finding in findings if finding["severity"] == "major"
    ]
    minor_findings = [
        finding for finding in findings if finding["severity"] == "minor"
    ]

    if major_findings:
        status = "fail"
        score = 0
    elif minor_findings:
        status = "warn"
        score = 80
    else:
        status = "pass"
        score = 100
        findings.append(
            _finding(
                "cta.valid",
                "info",
                _get_message(judge_rules, "pass"),
                {
                    "expected_cta": expected_cta_text,
                    "cta_count": cta_count,
                    "funnel_stage": funnel_stage,
                },
            )
        )

    return {
        "dimension": "cta",
        "status": status,
        "score": score,
        "applied_rule": judge_rules,
        "findings": findings,
    }
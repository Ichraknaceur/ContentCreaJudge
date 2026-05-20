"""Judge logic for CTA evaluation."""

from __future__ import annotations

import unicodedata

from contentcreajudge.judges.cta.cta_semantic import (
    is_semantically_aligned_with_funnel,
)


def _normalize(value: object) -> str:
    """Normalize text for comparison."""
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return " ".join(text.split())


def _safe_int(value: object, default: int = 0) -> int:
    """Convert a value to int with a safe fallback."""
    try:
        return int(value)
    except TypeError, ValueError:
        return default


def _safe_list(value: object) -> list[object]:
    """Return value if it is a list, otherwise an empty list."""
    return value if isinstance(value, list) else []


def _safe_dict(value: object) -> dict[str, object]:
    """Return value if it is a dict, otherwise an empty dict."""
    return value if isinstance(value, dict) else {}


def _get_message(judge_rules: dict[str, object], key: str) -> str:
    """Return a configured message or a safe fallback."""
    messages = _safe_dict(judge_rules.get("messages"))
    return str(messages.get(key, key))


def _finding(
    rule_id: str,
    severity: str,
    message: str,
    evidence: dict[str, object],
) -> dict[str, object]:
    """Build a structured CTA finding."""
    return {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def _is_read_more(value: object) -> bool:
    """Return True when the CTA is a read-more style CTA."""
    return _normalize(value) in {"read more", "learn more", "lire la suite"}


def _get_funnel_rules(judge_rules: dict[str, object]) -> dict[str, object]:
    """Return rules configured for the current funnel stage."""
    funnel_alignment = _safe_dict(judge_rules.get("funnel_alignment"))
    funnel_stage = str(judge_rules.get("funnel_stage", ""))

    expected_by_funnel = _safe_dict(funnel_alignment.get("expected_by_funnel"))
    return _safe_dict(expected_by_funnel.get(funnel_stage))


def _get_allowed_labels(judge_rules: dict[str, object]) -> list[str]:
    """Return allowed CTA labels for the current funnel and language."""
    language = str(judge_rules.get("language", "fr"))
    funnel_rules = _get_funnel_rules(judge_rules)
    allowed_labels = funnel_rules.get("allowed_cta_labels", {})

    if isinstance(allowed_labels, dict):
        return [str(label) for label in _safe_list(allowed_labels.get(language))]

    if isinstance(allowed_labels, list):
        return [str(label) for label in allowed_labels]

    return []


def _get_forbidden_labels(judge_rules: dict[str, object]) -> list[str]:
    """Return forbidden CTA labels for the current funnel and language."""
    language = str(judge_rules.get("language", "fr"))
    funnel_rules = _get_funnel_rules(judge_rules)
    forbidden_labels = funnel_rules.get("forbidden_cta_labels", {})

    if isinstance(forbidden_labels, dict):
        return [str(label) for label in _safe_list(forbidden_labels.get(language))]

    if isinstance(forbidden_labels, list):
        return [str(label) for label in forbidden_labels]

    return []


def _get_expected_intents(judge_rules: dict[str, object]) -> list[str]:
    """Return semantic CTA intents for the current funnel and language."""
    language = str(judge_rules.get("language", "fr"))
    funnel_rules = _get_funnel_rules(judge_rules)
    expected_intents = funnel_rules.get("expected_intents", {})

    if isinstance(expected_intents, dict):
        return [str(intent) for intent in _safe_list(expected_intents.get(language))]

    if isinstance(expected_intents, list):
        return [str(intent) for intent in expected_intents]

    return []


def _get_decision_intent_markers(judge_rules: dict[str, object]) -> list[str]:
    """Return configured lexical markers for direct conversion intent."""
    funnel_alignment = _safe_dict(judge_rules.get("funnel_alignment"))
    return [
        str(marker)
        for marker in _safe_list(funnel_alignment.get("decision_intent_markers"))
    ]


def _get_awareness_intent_markers(judge_rules: dict[str, object]) -> list[str]:
    """Return configured lexical markers for informational intent."""
    funnel_alignment = _safe_dict(judge_rules.get("funnel_alignment"))
    return [
        str(marker)
        for marker in _safe_list(funnel_alignment.get("awareness_intent_markers"))
    ]


def _looks_like_decision_cta(cta_text: str, judge_rules: dict[str, object]) -> bool:
    """Return True when CTA contains direct conversion intent."""
    normalized_cta = _normalize(cta_text)
    decision_markers = {
        _normalize(marker) for marker in _get_decision_intent_markers(judge_rules)
    }

    return any(marker in normalized_cta for marker in decision_markers if marker)


def _looks_like_awareness_cta(cta_text: str, judge_rules: dict[str, object]) -> bool:
    """Return True when CTA contains informational or weak awareness intent."""
    normalized_cta = _normalize(cta_text)
    awareness_markers = {
        _normalize(marker) for marker in _get_awareness_intent_markers(judge_rules)
    }

    return any(marker in normalized_cta for marker in awareness_markers if marker)


def _is_semantic_fallback_enabled(judge_rules: dict[str, object]) -> bool:
    """Return True when semantic fallback is enabled."""
    semantic_rules = _safe_dict(judge_rules.get("semantic_fallback"))
    return bool(semantic_rules.get("enabled", False))


def _allow_custom_cta(judge_rules: dict[str, object]) -> bool:
    """Return True when exact CTA mismatch can be checked semantically."""
    semantic_rules = _safe_dict(judge_rules.get("semantic_fallback"))
    return bool(
        semantic_rules.get(
            "allow_semantic_check_for_unknown_or_custom_cta",
            False,
        )
    )


def _is_cta_at_end(preprocessed_content: dict[str, object]) -> bool:
    """Return True when the last CTA block is the last top-level tag."""
    cta_blocks = _safe_list(preprocessed_content.get("cta_blocks"))
    top_level_tag_count = _safe_int(preprocessed_content.get("top_level_tag_count"))

    if not cta_blocks:
        return False

    last_cta = _safe_dict(cta_blocks[-1])
    return _safe_int(last_cta.get("index"), -1) == top_level_tag_count - 1


def _is_cta_before_complementary_reading(
    preprocessed_content: dict[str, object],
) -> bool:
    """Return True when CTA is right before complementary reading."""
    cta_blocks = _safe_list(preprocessed_content.get("cta_blocks"))
    complementary_indexes = _safe_list(
        preprocessed_content.get("complementary_reading_indexes")
    )

    if not cta_blocks or not complementary_indexes:
        return False

    last_cta = _safe_dict(cta_blocks[-1])
    last_cta_index = _safe_int(last_cta.get("index"), -1)
    first_complementary_index = _safe_int(complementary_indexes[0], -1)

    return last_cta_index == first_complementary_index - 1


def _is_cta_after_quiz_correction(preprocessed_content: dict[str, object]) -> bool:
    """Return True when quiz CTA is after correction and at the end."""
    cta_blocks = _safe_list(preprocessed_content.get("cta_blocks"))
    quiz_indexes = _safe_list(preprocessed_content.get("quiz_correction_indexes"))

    if not cta_blocks or not quiz_indexes:
        return False

    last_cta = _safe_dict(cta_blocks[-1])
    last_cta_index = _safe_int(last_cta.get("index"), -1)
    last_quiz_index = _safe_int(quiz_indexes[-1], -1)

    return last_cta_index > last_quiz_index and _is_cta_at_end(preprocessed_content)


def _is_educational_purpose(judge_rules: dict[str, object]) -> bool:
    """Return True when the content purpose is educational."""
    content_purpose = judge_rules.get("content_purpose")
    if not content_purpose:
        return False

    purpose_rules = _safe_dict(judge_rules.get("content_purpose_alignment"))
    educational_purposes = _safe_list(purpose_rules.get("educational_purposes"))

    normalized_purpose = _normalize(content_purpose)
    return normalized_purpose in {
        _normalize(purpose) for purpose in educational_purposes
    }


def _is_language_consistent(judge_rules: dict[str, object], cta_text: str) -> bool:
    """Return True when CTA language is consistent with configured language policy."""
    allowed_labels = _get_allowed_labels(judge_rules)

    if not allowed_labels:
        return True

    normalized_cta = _normalize(cta_text)
    normalized_allowed = {_normalize(label) for label in allowed_labels}

    if normalized_cta in normalized_allowed:
        return True

    language_policy = _safe_dict(judge_rules.get("language_policy"))
    return bool(
        language_policy.get("allow_input_language_to_override_output_language", True),
    )


def _is_semantically_valid_cta(
    cta_text: str,
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Run semantic CTA validation against funnel-compatible intents."""
    semantic_rules = _safe_dict(judge_rules.get("semantic_fallback"))
    if not semantic_rules:
        return {"is_aligned": False, "reason": "Semantic rules are not configured."}

    return is_semantically_aligned_with_funnel(
        cta_text=cta_text,
        allowed_labels=_get_allowed_labels(judge_rules),
        forbidden_labels=_get_forbidden_labels(judge_rules),
        expected_intents=_get_expected_intents(judge_rules),
        semantic_rules=semantic_rules,
    )


def run_cta_judge(  # noqa: C901, PLR0912, PLR0915
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate CTA compliance from preprocessed content and resolved rules."""
    findings: list[dict[str, object]] = []

    expected_cta = judge_rules.get("expected_cta")
    expected_cta_text = str(expected_cta).strip() if expected_cta else None

    cta_blocks = _safe_list(preprocessed_content.get("cta_blocks"))
    cta_count = _safe_int(preprocessed_content.get("cta_count"), 0)
    has_cta = bool(preprocessed_content.get("has_cta", False))
    has_complementary_reading = bool(
        preprocessed_content.get("has_complementary_reading", False)
    )

    content_type = str(judge_rules.get("content_type", ""))
    funnel_stage = str(judge_rules.get("funnel_stage", ""))

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
                        "reason": (
                            "Read more CTA must be omitted when complementary "
                            "reading exists."
                        ),
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
                        "cta_texts": preprocessed_content.get("cta_texts", []),
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
        first_cta = cta_blocks[0] if cta_blocks else {}
        first_cta = _safe_dict(first_cta)

        if not first_cta:
            findings.append(
                _finding(
                    "cta.invalid_preprocessing",
                    "major",
                    "CTA preprocessing output is invalid.",
                    {"reason": "First CTA block is missing or invalid."},
                )
            )
        else:
            cta_text = str(first_cta.get("text", ""))
            strong_text = first_cta.get("strong_text")
            normalized_cta = _normalize(cta_text)

            allowed_labels = {
                _normalize(label) for label in _get_allowed_labels(judge_rules)
            }
            forbidden_labels = {
                _normalize(label) for label in _get_forbidden_labels(judge_rules)
            }

            semantic_enabled = _is_semantic_fallback_enabled(judge_rules)
            allow_custom_cta = _allow_custom_cta(judge_rules)

            if (
                expected_cta_text
                and normalized_cta != _normalize(expected_cta_text)
                and not allow_custom_cta
            ):
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
                or "cta" not in _safe_list(first_cta.get("classes"))
                or not first_cta.get("has_strong")
                or _normalize(strong_text) != normalized_cta
            ):
                html_format = _safe_dict(judge_rules.get("html_format"))

                findings.append(
                    _finding(
                        "cta.html_format",
                        "major",
                        _get_message(judge_rules, "html_format"),
                        {
                            "observed_html": first_cta.get("html"),
                            "expected_format": html_format.get("expected_format"),
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
                                "cta_index": first_cta.get("index"),
                                "quiz_correction_indexes": preprocessed_content.get(
                                    "quiz_correction_indexes",
                                    [],
                                ),
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
                                "cta_index": first_cta.get("index"),
                                "complementary_reading_indexes": (
                                    preprocessed_content.get(
                                        "complementary_reading_indexes",
                                        [],
                                    )
                                ),
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
                            "cta_index": first_cta.get("index"),
                            "top_level_tag_count": preprocessed_content.get(
                                "top_level_tag_count",
                                0,
                            ),
                        },
                    )
                )

            is_decision_like_in_awareness = (
                funnel_stage == "AWARENESS"
                and _looks_like_decision_cta(cta_text, judge_rules)
            )
            is_awareness_like_in_decision = (
                funnel_stage == "DECISION"
                and _looks_like_awareness_cta(cta_text, judge_rules)
            )

            if (
                normalized_cta in forbidden_labels
                or is_decision_like_in_awareness
                or is_awareness_like_in_decision
            ):
                reason = (
                    "CTA intent is incompatible with this funnel stage."
                    if is_decision_like_in_awareness or is_awareness_like_in_decision
                    else "CTA is forbidden for this funnel stage."
                )
                findings.append(
                    _finding(
                        "cta.funnel_alignment",
                        "major",
                        _get_message(judge_rules, "funnel_alignment"),
                        {
                            "funnel_stage": funnel_stage,
                            "observed_cta": cta_text,
                            "reason": reason,
                        },
                    )
                )
            elif allowed_labels and normalized_cta not in allowed_labels:
                if semantic_enabled:
                    semantic_result = _is_semantically_valid_cta(
                        cta_text=cta_text,
                        judge_rules=judge_rules,
                    )

                    if not bool(semantic_result.get("is_aligned", False)):
                        findings.append(
                            _finding(
                                "cta.funnel_alignment",
                                "major",
                                _get_message(judge_rules, "funnel_alignment"),
                                {
                                    "funnel_stage": funnel_stage,
                                    "observed_cta": cta_text,
                                    "allowed_labels": _get_allowed_labels(
                                        judge_rules,
                                    ),
                                    "semantic_result": semantic_result,
                                },
                            )
                        )
                else:
                    findings.append(
                        _finding(
                            "cta.funnel_alignment",
                            "major",
                            _get_message(judge_rules, "funnel_alignment"),
                            {
                                "funnel_stage": funnel_stage,
                                "observed_cta": cta_text,
                                "allowed_labels": _get_allowed_labels(
                                    judge_rules,
                                ),
                            },
                        )
                    )

            if (
                _is_educational_purpose(judge_rules)
                and normalized_cta in forbidden_labels
            ):
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

            anchor_quality = _safe_dict(judge_rules.get("anchor_quality"))
            vague_anchors = _safe_dict(anchor_quality.get("vague_anchors"))
            language = str(judge_rules.get("language", "fr"))
            vague_labels = _safe_list(vague_anchors.get(language))

            if not cta_text.strip():
                findings.append(
                    _finding(
                        "cta.anchor_quality",
                        "minor",
                        _get_message(judge_rules, "anchor_quality"),
                        {"reason": "CTA anchor is empty."},
                    )
                )
            elif (
                normalized_cta in {_normalize(label) for label in vague_labels}
                and expected_cta_text
                and normalized_cta != _normalize(expected_cta_text)
            ):
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
        finding for finding in findings if finding.get("severity") == "major"
    ]
    minor_findings = [
        finding for finding in findings if finding.get("severity") == "minor"
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

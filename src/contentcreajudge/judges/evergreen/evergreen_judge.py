"""Judge logic for evergreen evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypedDict

if TYPE_CHECKING:
    from contentcreajudge.preprocessing.evergreen_preprocessor import (
        EvergreenPreprocessingResult,
        EvergreenTemporalReference,
    )

JudgeStatus = Literal["pass", "warn", "fail"]
FindingSeverity = Literal["info", "minor", "major"]


class EvergreenFinding(TypedDict):
    """Finding emitted by the evergreen judge."""

    rule_id: str
    severity: FindingSeverity
    message: str
    evidence: EvergreenTemporalReference


class EvergreenJudgeResult(TypedDict):
    """Result returned by the evergreen judge."""

    dimension: str
    status: JudgeStatus
    score: int
    applied_rule: dict[str, object]
    findings: list[EvergreenFinding]


def _get_message(judge_rules: dict[str, object], key: str, fallback: str) -> str:
    messages = judge_rules.get("messages")

    if not isinstance(messages, dict):
        return fallback

    value = messages.get(key)

    if not isinstance(value, str):
        return fallback

    return value


def _is_reference_allowed(ref: EvergreenTemporalReference) -> bool:
    return (
        ref["is_in_input"]
        or ref["is_in_source_context"]
        or ref["is_historical_context"]
    )


def _rule_id_for_reference(reference_type: str) -> str:
    if reference_type in {"year", "full_date", "month_year"}:
        return "evergreen.unprovided_dates"

    if reference_type == "relative_date":
        return "evergreen.relative_temporal_references"

    if reference_type == "news_reference":
        return "evergreen.news_references"

    if reference_type == "version_reference":
        return "evergreen.version_references"

    return "evergreen.current_trend_references"


def _message_key_for_reference(reference_type: str) -> str:
    if reference_type in {"year", "full_date", "month_year"}:
        return "unprovided_dates"

    if reference_type == "relative_date":
        return "relative_temporal_references"

    if reference_type == "news_reference":
        return "news_references"

    if reference_type == "version_reference":
        return "version_references"

    return "current_trend_references"


def _severity_for_reference(
    *,
    evergreen_required: bool,
    reference_type: str,
) -> FindingSeverity:
    if not evergreen_required:
        return "minor"

    if reference_type == "current_trend_reference":
        return "minor"

    return "major"


def _build_finding(
    ref: EvergreenTemporalReference,
    judge_rules: dict[str, object],
    *,
    evergreen_required: bool,
) -> EvergreenFinding:
    reference_type = ref["type"]
    message_key = _message_key_for_reference(reference_type)

    return {
        "rule_id": _rule_id_for_reference(reference_type),
        "severity": _severity_for_reference(
            evergreen_required=evergreen_required,
            reference_type=reference_type,
        ),
        "message": _get_message(
            judge_rules=judge_rules,
            key=message_key,
            fallback="The content contains a temporal reference.",
        ),
        "evidence": ref,
    }


def run_evergreen_judge(
    preprocessed_content: EvergreenPreprocessingResult,
    judge_rules: dict[str, object],
) -> EvergreenJudgeResult:
    """Evaluate evergreen compliance from preprocessed temporal references."""
    evergreen_required = bool(judge_rules.get("evergreen_required", False))
    temporal_references = preprocessed_content.get("temporal_references", [])

    findings: list[EvergreenFinding] = []

    for ref in temporal_references:
        if _is_reference_allowed(ref):
            continue

        findings.append(
            _build_finding(
                ref=ref,
                judge_rules=judge_rules,
                evergreen_required=evergreen_required,
            ),
        )

    if not findings:
        return {
            "dimension": "evergreen",
            "status": "pass",
            "score": 100,
            "applied_rule": judge_rules,
            "findings": [],
        }

    if evergreen_required:
        return {
            "dimension": "evergreen",
            "status": "fail",
            "score": 0,
            "applied_rule": judge_rules,
            "findings": findings,
        }

    return {
        "dimension": "evergreen",
        "status": "warn",
        "score": 90,
        "applied_rule": judge_rules,
        "findings": findings,
    }

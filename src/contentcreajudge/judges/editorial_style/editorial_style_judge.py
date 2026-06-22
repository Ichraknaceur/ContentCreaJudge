"""Judge logic for editorial style evaluation."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from contentcreajudge.adapters.llm.client import call_openai_json
from contentcreajudge.adapters.llm.mistral_client import call_mistral_json
from contentcreajudge.judges.editorial_style.editorial_style_prompt import (
    build_editorial_style_prompt,
)

LLMCallable = Callable[..., str]

_REQUIRED_CRITERIA = (
    "style_alignment",
    "reasoning_alignment",
    "concept_handling",
    "expression_control",
    "writing_conventions",
    "example_alignment",
)
_MAX_PROVIDER_SCORE_GAP_FOR_AGREEMENT = 10
_STATUS_RANKS = {
    "pass": 0,
    "warn": 1,
    "fail": 2,
    "unknown": 3,
}


def _safe_json_loads(raw_response: str) -> dict[str, Any]:
    """Parse a JSON response returned by the LLM."""
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError:
        return {
            "criteria_scores": {},
            "findings": [
                {
                    "rule_id": "editorial_style.invalid_json",
                    "severity": "critical",
                    "message": "The LLM response is not valid JSON.",
                    "evidence": raw_response[:300],
                }
            ],
            "summary": "The editorial style judge could not parse the LLM response.",
        }

    if not isinstance(parsed, dict):
        return {
            "criteria_scores": {},
            "findings": [
                {
                    "rule_id": "editorial_style.invalid_json_shape",
                    "severity": "critical",
                    "message": "The LLM response JSON is not an object.",
                    "evidence": str(parsed)[:300],
                }
            ],
            "summary": "The editorial style judge received an invalid JSON shape.",
        }

    return parsed


def _normalize_criteria_scores(raw_scores: object) -> dict[str, int]:
    """Normalize criteria scores to integers between 0 and 100."""
    if not isinstance(raw_scores, dict):
        raw_scores = {}

    normalized_scores: dict[str, int] = {}

    for criterion in _REQUIRED_CRITERIA:
        value = raw_scores.get(criterion, 0)

        try:
            score = int(value)
        except TypeError, ValueError:
            score = 0

        normalized_scores[criterion] = max(0, min(100, score))

    return normalized_scores


def _normalize_findings(raw_findings: object) -> list[dict[str, object]]:
    """Normalize LLM findings."""
    if not isinstance(raw_findings, list):
        return []

    findings: list[dict[str, object]] = []

    for finding in raw_findings:
        if not isinstance(finding, dict):
            continue

        severity = str(finding.get("severity", "minor")).lower()

        if severity not in {"minor", "major", "critical"}:
            severity = "minor"

        findings.append(
            {
                "rule_id": str(finding.get("rule_id", "editorial_style.unknown")),
                "severity": severity,
                "message": str(finding.get("message", "")).strip(),
                "evidence": str(finding.get("evidence", "")).strip(),
            }
        )

    return findings


def _compute_weighted_score(
    criteria_scores: dict[str, int],
    judge_rules: dict[str, object],
) -> int:
    """Compute weighted editorial style score."""
    criteria_rules = judge_rules.get("criteria") or {}

    if not isinstance(criteria_rules, dict):
        return 0

    total = 0.0

    for criterion in _REQUIRED_CRITERIA:
        criterion_rules = criteria_rules.get(criterion) or {}

        if not isinstance(criterion_rules, dict):
            continue

        try:
            weight = float(criterion_rules.get("weight", 0))
        except TypeError, ValueError:
            weight = 0.0

        total += criteria_scores.get(criterion, 0) * weight

    return round(total)


def _resolve_status(
    score: int,
    findings: list[dict[str, object]],
    judge_rules: dict[str, object],
) -> str:
    """Resolve editorial style judge status."""
    thresholds = judge_rules.get("thresholds") or {}
    severity_policy = judge_rules.get("severity_policy") or {}

    pass_score = int(thresholds.get("pass_score", 80))
    warn_score = int(thresholds.get("warn_score", 60))

    severities = {str(finding.get("severity", "")).lower() for finding in findings}

    if "critical" in severities:
        return str(severity_policy.get("critical_forces_status", "fail"))

    if score < warn_score:
        return "fail"

    if score < pass_score:
        return "warn"

    if "major" in severities:
        return str(severity_policy.get("major_max_status", "warn"))

    return "pass"


def _run_single_provider(
    *,
    provider_name: str,
    call_provider: LLMCallable,
    prompt: str,
) -> dict[str, object]:
    """Run one LLM provider and normalize the result."""
    try:
        raw_response = call_provider(prompt=prompt, temperature=0.0)
    except RuntimeError as exc:
        raw_response = ""
        parsed_response = {
            "criteria_scores": {},
            "findings": [
                {
                    "rule_id": f"editorial_style.{provider_name}.provider_error",
                    "severity": "critical",
                    "message": f"{provider_name} call failed.",
                    "evidence": str(exc)[:300],
                }
            ],
            "summary": f"{provider_name} could not evaluate editorial style.",
        }
    else:
        parsed_response = _safe_json_loads(str(raw_response))

    criteria_scores = _normalize_criteria_scores(parsed_response.get("criteria_scores"))
    findings = _normalize_findings(parsed_response.get("findings"))
    summary = str(parsed_response.get("summary", "")).strip()

    return {
        "provider": provider_name,
        "criteria_scores": criteria_scores,
        "findings": findings,
        "summary": summary,
        "raw_response": raw_response,
    }


def _average_criteria_scores(
    openai_scores: dict[str, int],
    mistral_scores: dict[str, int],
) -> dict[str, int]:
    """Average criteria scores from both providers."""
    return {
        criterion: round(
            (openai_scores.get(criterion, 0) + mistral_scores.get(criterion, 0)) / 2
        )
        for criterion in _REQUIRED_CRITERIA
    }


def _merge_findings(
    openai_result: dict[str, object],
    mistral_result: dict[str, object],
) -> list[dict[str, object]]:
    """Merge findings from both providers."""
    merged: list[dict[str, object]] = []

    for provider_result in (openai_result, mistral_result):
        provider_name = str(provider_result.get("provider", "unknown"))
        findings = provider_result.get("findings", [])

        if not isinstance(findings, list):
            continue

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            merged.append(
                {
                    "provider": provider_name,
                    "rule_id": finding.get("rule_id", "editorial_style.unknown"),
                    "severity": finding.get("severity", "minor"),
                    "message": finding.get("message", ""),
                    "evidence": finding.get("evidence", ""),
                }
            )

    return merged


def _compute_provider_score_gap(
    openai_result: dict[str, object],
    mistral_result: dict[str, object],
    judge_rules: dict[str, object],
) -> int:
    """Compute score gap between provider criteria scores."""
    openai_scores = openai_result.get("criteria_scores")
    mistral_scores = mistral_result.get("criteria_scores")

    if not isinstance(openai_scores, dict):
        openai_scores = {}

    if not isinstance(mistral_scores, dict):
        mistral_scores = {}

    openai_score = _compute_weighted_score(openai_scores, judge_rules)
    mistral_score = _compute_weighted_score(mistral_scores, judge_rules)

    return abs(openai_score - mistral_score)


def _provider_status(
    provider_result: dict[str, object],
    judge_rules: dict[str, object],
) -> str:
    """Resolve one provider status from its scores and findings."""
    criteria_scores = provider_result.get("criteria_scores")
    findings = provider_result.get("findings")

    if not isinstance(criteria_scores, dict):
        criteria_scores = {}

    if not isinstance(findings, list):
        findings = []

    score = _compute_weighted_score(criteria_scores, judge_rules)

    return _resolve_status(
        score=score,
        findings=[finding for finding in findings if isinstance(finding, dict)],
        judge_rules=judge_rules,
    )


def _worst_status(*statuses: str) -> str:
    """Return the most severe status."""
    return max(statuses, key=lambda status: _STATUS_RANKS.get(status, 3))


def run_editorial_style_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Run the editorial style judge and return a final normalized result."""
    prompt = build_editorial_style_prompt(preprocessed_content)

    openai_result = _run_single_provider(
        provider_name="openai",
        call_provider=call_openai_json,
        prompt=prompt,
    )
    mistral_result = _run_single_provider(
        provider_name="mistral",
        call_provider=call_mistral_json,
        prompt=prompt,
    )

    criteria_scores = _average_criteria_scores(
        openai_scores=openai_result["criteria_scores"],  # type: ignore[arg-type]
        mistral_scores=mistral_result["criteria_scores"],  # type: ignore[arg-type]
    )

    score = _compute_weighted_score(
        criteria_scores=criteria_scores,
        judge_rules=judge_rules,
    )

    findings = _merge_findings(
        openai_result=openai_result,
        mistral_result=mistral_result,
    )

    average_status = _resolve_status(
        score=score,
        findings=findings,
        judge_rules=judge_rules,
    )
    openai_status = _provider_status(openai_result, judge_rules)
    mistral_status = _provider_status(mistral_result, judge_rules)
    score_gap = _compute_provider_score_gap(
        openai_result=openai_result,
        mistral_result=mistral_result,
        judge_rules=judge_rules,
    )
    status = _worst_status(average_status, openai_status, mistral_status)

    return {
        "dimension": "editorial_style",
        "status": status,
        "score": score,
        "criteria_scores": criteria_scores,
        "findings": findings,
        "summary": "Editorial style judge completed with OpenAI and Mistral.",
        "agreement": score_gap <= _MAX_PROVIDER_SCORE_GAP_FOR_AGREEMENT,
        "score_gap": score_gap,
        "providers": {
            "openai": openai_result,
            "mistral": mistral_result,
        },
        "applied_rule": judge_rules,
    }

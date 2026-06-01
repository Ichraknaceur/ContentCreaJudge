"""Judge logic for tone evaluation."""

from __future__ import annotations

import json
from typing import Any

from contentcreajudge.adapters.llm.client import LLMClientError, call_openai_json
from contentcreajudge.adapters.llm.mistral_client import (
    MistralClientError,
    call_mistral_json,
)
from contentcreajudge.judges.tone.tone_prompt import build_tone_judge_prompt

_PROVIDER_OPENAI = "openai"
_PROVIDER_MISTRAL = "mistral"
_PASS_SCORE_THRESHOLD = 80
_WARN_SCORE_THRESHOLD = 60


def _safe_json_loads(raw_response: str) -> dict[str, Any]:
    """Parse a raw JSON response and return a dictionary."""
    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError:
        return {
            "dimension": "tone",
            "status": "unknown",
            "score": 0,
            "expected_tone": "",
            "detected_tone": "",
            "confidence": 0.0,
            "summary": "LLM response is not valid JSON.",
            "criterion_scores": {},
            "findings": [
                {
                    "rule_id": "tone.invalid_llm_response",
                    "severity": "critical",
                    "message": "The LLM response could not be parsed as JSON.",
                    "evidence": {
                        "excerpt": raw_response[:500],
                        "explanation": "The response is not valid JSON.",
                    },
                }
            ],
        }

    if not isinstance(parsed_response, dict):
        return {
            "dimension": "tone",
            "status": "unknown",
            "score": 0,
            "expected_tone": "",
            "detected_tone": "",
            "confidence": 0.0,
            "summary": "LLM response is not a JSON object.",
            "criterion_scores": {},
            "findings": [
                {
                    "rule_id": "tone.invalid_llm_response",
                    "severity": "critical",
                    "message": "The LLM response is not a JSON object.",
                    "evidence": {
                        "excerpt": raw_response[:500],
                        "explanation": "The response must be a JSON object.",
                    },
                }
            ],
        }

    return parsed_response


def _safe_int(value: object, default: int = 0) -> int:
    """Convert a value to an integer within the 0-100 range."""
    try:
        number = int(float(str(value)))
    except TypeError, ValueError:
        return default

    return max(0, min(100, number))


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert a value to a float within the 0-1 range."""
    try:
        number = float(str(value))
    except TypeError, ValueError:
        return default

    return max(0.0, min(1.0, number))


def _resolve_status(score: int) -> str:
    """Resolve the tone status from the numeric score."""
    if score >= _PASS_SCORE_THRESHOLD:
        return "pass"

    if score >= _WARN_SCORE_THRESHOLD:
        return "warn"

    return "fail"


def _criterion_weights(judge_rules: dict[str, object]) -> dict[str, int]:
    """Return criterion weights from resolved judge rules."""
    criteria = judge_rules.get("criteria") or []

    if not isinstance(criteria, list):
        return {}

    weights: dict[str, int] = {}

    for criterion in criteria:
        if not isinstance(criterion, dict):
            continue

        criterion_id = criterion.get("criterion_id")
        if not criterion_id:
            continue

        weights[str(criterion_id)] = int(criterion.get("weight", 0))

    return weights


def _normalize_findings(
    findings: object,
    allowed_rule_ids: set[str],
) -> list[dict[str, object]]:
    """Normalize LLM findings and keep only usable entries."""
    if not isinstance(findings, list):
        return []

    normalized_findings: list[dict[str, object]] = []

    for finding in findings:
        if not isinstance(finding, dict):
            continue

        rule_id = str(finding.get("rule_id", "")).strip()
        if rule_id not in allowed_rule_ids:
            continue

        severity = str(finding.get("severity", "minor")).strip()
        if severity not in {"info", "minor", "major", "critical"}:
            severity = "minor"

        evidence = finding.get("evidence") or {}
        if not isinstance(evidence, dict):
            evidence = {}

        normalized_findings.append(
            {
                "rule_id": rule_id,
                "severity": severity,
                "message": str(finding.get("message", "")).strip(),
                "evidence": {
                    "excerpt": str(evidence.get("excerpt", "")).strip(),
                    "explanation": str(evidence.get("explanation", "")).strip(),
                },
            }
        )

    return normalized_findings


def _normalize_provider_result(
    *,
    provider: str,
    parsed_response: dict[str, Any],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Normalize one provider response and recalculate its score."""
    weights = _criterion_weights(judge_rules)
    expected_criterion_ids = set(weights.keys())

    raw_criterion_scores = parsed_response.get("criterion_scores") or {}
    if not isinstance(raw_criterion_scores, dict):
        raw_criterion_scores = {}

    criterion_scores = {
        criterion_id: _safe_int(raw_criterion_scores.get(criterion_id, 0))
        for criterion_id in expected_criterion_ids
    }

    recalculated_score = round(
        sum(
            (criterion_scores[criterion_id] * weights[criterion_id]) / 100
            for criterion_id in expected_criterion_ids
        )
    )

    findings = _normalize_findings(
        parsed_response.get("findings"),
        expected_criterion_ids,
    )

    status = _resolve_status(recalculated_score)

    if not criterion_scores:
        status = "unknown"

    return {
        "provider": provider,
        "dimension": "tone",
        "status": status,
        "score": recalculated_score,
        "expected_tone": str(parsed_response.get("expected_tone", "")).strip(),
        "detected_tone": str(parsed_response.get("detected_tone", "")).strip(),
        "confidence": _safe_float(parsed_response.get("confidence", 0.0)),
        "summary": str(parsed_response.get("summary", "")).strip(),
        "criterion_scores": criterion_scores,
        "findings": findings,
    }


def _provider_error_result(
    *,
    provider: str,
    error: Exception,
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Return a normalized unknown result when one provider fails."""
    weights = _criterion_weights(judge_rules)

    return {
        "provider": provider,
        "dimension": "tone",
        "status": "unknown",
        "score": 0,
        "expected_tone": str(
            (judge_rules.get("context") or {}).get("expected_tone", "")
        ),
        "detected_tone": "",
        "confidence": 0.0,
        "summary": f"{provider} tone evaluation failed.",
        "criterion_scores": dict.fromkeys(weights, 0),
        "findings": [
            {
                "rule_id": "tone.provider_error",
                "severity": "critical",
                "message": f"{provider} failed during tone evaluation.",
                "evidence": {
                    "excerpt": "",
                    "explanation": str(error),
                },
            }
        ],
    }


def _compute_agreement(
    openai_result: dict[str, object],
    mistral_result: dict[str, object],
) -> dict[str, object]:
    """Compute agreement indicators between OpenAI and Mistral."""
    openai_score = _safe_int(openai_result.get("score", 0))
    mistral_score = _safe_int(mistral_result.get("score", 0))

    openai_status = str(openai_result.get("status", "unknown"))
    mistral_status = str(mistral_result.get("status", "unknown"))

    return {
        "status_match": openai_status == mistral_status,
        "score_gap": abs(openai_score - mistral_score),
        "openai_status": openai_status,
        "mistral_status": mistral_status,
        "openai_score": openai_score,
        "mistral_score": mistral_score,
    }


def _merge_findings(
    openai_result: dict[str, object],
    mistral_result: dict[str, object],
) -> list[dict[str, object]]:
    """Merge findings from both providers and keep provider information."""
    merged_findings: list[dict[str, object]] = []

    for provider_result in (openai_result, mistral_result):
        provider = str(provider_result.get("provider", "unknown"))
        findings = provider_result.get("findings") or []

        if not isinstance(findings, list):
            continue

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            copied_finding = dict(finding)
            copied_finding["provider"] = provider
            merged_findings.append(copied_finding)

    return merged_findings


def _build_final_result(
    *,
    openai_result: dict[str, object],
    mistral_result: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Build the final tone judge result from provider results."""
    agreement = _compute_agreement(openai_result, mistral_result)

    provider_scores = [
        _safe_int(result.get("score", 0))
        for result in (openai_result, mistral_result)
        if str(result.get("status", "unknown")) != "unknown"
    ]

    if provider_scores:
        final_score = round(sum(provider_scores) / len(provider_scores))
        final_status = _resolve_status(final_score)
    else:
        final_score = 0
        final_status = "unknown"

    findings = _merge_findings(openai_result, mistral_result)

    messages = judge_rules.get("messages") or {}
    if not isinstance(messages, dict):
        messages = {}

    return {
        "dimension": "tone",
        "status": final_status,
        "score": final_score,
        "summary": messages.get(
            final_status,
            "Tone evaluation completed.",
        ),
        "provider_results": {
            "openai": openai_result,
            "mistral": mistral_result,
        },
        "agreement": agreement,
        "findings": findings,
        "applied_rule": {
            "judge_id": judge_rules.get("judge_id", "tone"),
            "version": judge_rules.get("version", 1),
            "criteria": judge_rules.get("criteria", []),
        },
    }


def run_tone_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate tone compliance with OpenAI and Mistral."""
    content = str(preprocessed_content.get("content", ""))

    prompt = build_tone_judge_prompt(
        content=content,
        judge_rules=judge_rules,
    )

    try:
        openai_raw_response = call_openai_json(prompt=prompt)
        openai_result = _normalize_provider_result(
            provider=_PROVIDER_OPENAI,
            parsed_response=_safe_json_loads(openai_raw_response),
            judge_rules=judge_rules,
        )
    except LLMClientError as exc:
        openai_result = _provider_error_result(
            provider=_PROVIDER_OPENAI,
            error=exc,
            judge_rules=judge_rules,
        )

    try:
        mistral_raw_response = call_mistral_json(prompt=prompt)
        mistral_result = _normalize_provider_result(
            provider=_PROVIDER_MISTRAL,
            parsed_response=_safe_json_loads(mistral_raw_response),
            judge_rules=judge_rules,
        )
    except MistralClientError as exc:
        mistral_result = _provider_error_result(
            provider=_PROVIDER_MISTRAL,
            error=exc,
            judge_rules=judge_rules,
        )

    return _build_final_result(
        openai_result=openai_result,
        mistral_result=mistral_result,
        judge_rules=judge_rules,
    )

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

_UNKNOWN_RESULT = {
    "dimension": "tone",
    "status": "unknown",
    "score": None,
    "confidence": None,
    "blind_observation": None,
    "ton_distribution": None,
    "expected_tone": "",
    "detected_tone": "",
    "summary": "Tone evaluation could not be completed reliably.",
    "criterion_scores": None,
    "findings": [],
}


def _safe_json_loads(raw_response: str) -> dict[str, Any]:
    """Parse a raw JSON response and return a dictionary."""
    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError:
        return {
            **_UNKNOWN_RESULT,
            "summary": "LLM response is not valid JSON.",
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
            **_UNKNOWN_RESULT,
            "summary": "LLM response is not a JSON object.",
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
    if value is None:
        return default

    try:
        number = int(float(str(value)))
    except TypeError, ValueError:
        return default

    return max(0, min(100, number))


def _safe_nullable_int(value: object) -> int | None:
    """Convert a nullable value to an integer within the 0-100 range."""
    if value is None:
        return None

    return _safe_int(value)


def _safe_float(value: object, default: float = 0.0) -> float:
    """Convert a value to a float within the 0-1 range."""
    if value is None:
        return default

    try:
        number = float(str(value))
    except TypeError, ValueError:
        return default

    return max(0.0, min(1.0, number))


def _safe_nullable_float(value: object) -> float | None:
    """Convert a nullable value to a float within the 0-1 range."""
    if value is None:
        return None

    return _safe_float(value)


def _resolve_status(score: int | None) -> str:
    """Resolve the tone status from the numeric score."""
    if score is None:
        return "unknown"

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


def _allowed_rule_ids(judge_rules: dict[str, object]) -> set[str]:
    """Return allowed finding rule ids."""
    weights = _criterion_weights(judge_rules)
    allowed = set(weights.keys())
    allowed.add("tone.invalid_llm_response")
    allowed.add("tone.invalid_tone_presence")
    allowed.add("tone.provider_error")
    return allowed


def _normalize_lexical_evidence(value: object) -> list[str]:
    """Normalize lexical evidence list."""
    if not isinstance(value, list):
        return []

    return [str(item).strip() for item in value if str(item).strip()][:4]


def _normalize_tone_presence(value: object) -> dict[str, int]:
    """Normalize tone presence percentages."""
    if not isinstance(value, dict):
        return {}

    normalized_presence: dict[str, int] = {}

    for tone, percentage in value.items():
        tone_name = str(tone).strip()
        if not tone_name:
            continue

        normalized_presence[tone_name] = _safe_int(percentage)

    return normalized_presence


def _normalize_blind_observation(value: object) -> dict[str, object] | None:
    """Normalize blind observation data."""
    if value is None:
        return None

    if not isinstance(value, dict):
        return None

    return {
        "perceived_tone": str(value.get("perceived_tone", "")).strip(),
        "tone_presence": _normalize_tone_presence(value.get("tone_presence")),
        "lexical_evidence": _normalize_lexical_evidence(value.get("lexical_evidence")),
    }


def _split_perceived_tones(perceived_tone: str) -> set[str]:
    """Split perceived tone into normalized tone labels."""
    return {tone.strip().lower() for tone in perceived_tone.split(",") if tone.strip()}


def _is_tone_presence_consistent(
    blind_observation: dict[str, object] | None,
) -> bool:
    """Check perceived_tone and tone_presence consistency."""
    if not isinstance(blind_observation, dict):
        return False

    perceived_tone = str(blind_observation.get("perceived_tone", ""))
    tone_presence = blind_observation.get("tone_presence")

    if not isinstance(tone_presence, dict):
        return False

    perceived_tones = _split_perceived_tones(perceived_tone)
    presence_tones = {str(tone).strip().lower() for tone in tone_presence}

    return perceived_tones == presence_tones


def _normalize_distribution_items(value: object) -> list[dict[str, object]]:
    """Normalize one source tone distribution list."""
    if not isinstance(value, list):
        return []

    normalized_distribution: list[dict[str, object]] = []

    for item in value:
        if not isinstance(item, dict):
            continue

        tone = str(item.get("tone", "")).strip()
        if not tone:
            continue

        normalized_distribution.append(
            {
                "tone": tone,
                "score": _safe_int(item.get("score", 0)),
                "justification": str(item.get("justification", "")).strip(),
            }
        )

    return normalized_distribution


def _normalize_ton_distribution(value: object) -> list[dict[str, object]] | None:
    """Normalize tone distribution information."""
    if value is None:
        return None

    if not isinstance(value, list):
        return []

    normalized_entries: list[dict[str, object]] = []

    for entry in value:
        if not isinstance(entry, dict):
            continue

        source_tone = str(entry.get("source_tone", "")).strip()
        source_score = _safe_int(entry.get("source_score", 0))
        in_org_list = bool(entry.get("in_org_list", False))
        distribution = _normalize_distribution_items(entry.get("distribution"))
        distribution_sum = sum(int(item.get("score", 0)) for item in distribution)

        normalized_entries.append(
            {
                "source_tone": source_tone,
                "source_score": source_score,
                "in_org_list": in_org_list,
                "distribution": distribution if in_org_list else [],
                "sum_check": distribution_sum if in_org_list else source_score,
            }
        )

    return normalized_entries


def _normalize_findings(
    findings: object,
    allowed_rule_ids: set[str],
) -> list[dict[str, object]]:
    """Normalize LLM findings and keep only usable entries."""
    if not isinstance(findings, list):
        return []

    normalized_findings: list[dict[str, object]] = []

    for finding in findings[:8]:
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


def _normalize_score_block(
    value: object,
    judge_rules: dict[str, object],
) -> dict[str, int] | None:
    """Normalize one criterion score block."""
    if not isinstance(value, dict):
        return None

    weights = _criterion_weights(judge_rules)
    if not weights:
        return None

    return {
        criterion_id: _safe_int(value.get(criterion_id, 0)) for criterion_id in weights
    }


def _normalize_criterion_scores(
    raw_criterion_scores: object,
    judge_rules: dict[str, object],
) -> dict[str, dict[str, int]] | None:
    """Normalize detected and expected tone criterion scores."""
    if not isinstance(raw_criterion_scores, dict):
        return None

    detected_scores = _normalize_score_block(
        raw_criterion_scores.get("detected_tone"),
        judge_rules,
    )
    expected_scores = _normalize_score_block(
        raw_criterion_scores.get("expected_tone"),
        judge_rules,
    )

    if detected_scores is None or expected_scores is None:
        return None

    return {
        "detected_tone": detected_scores,
        "expected_tone": expected_scores,
    }


def _recalculate_score(
    criterion_scores: dict[str, dict[str, int]] | None,
    judge_rules: dict[str, object],
) -> int | None:
    """Recalculate global score from detected tone criterion scores."""
    if criterion_scores is None:
        return None

    expected_scores = criterion_scores.get("expected_tone")

    if not isinstance(expected_scores, dict):
        return None

    weights = _criterion_weights(judge_rules)
    if not weights:
        return None

    return round(
        sum(
            (expected_scores.get(criterion_id, 0) * weight) / 100
            for criterion_id, weight in weights.items()
        )
    )


def _normalize_provider_result(
    *,
    provider: str,
    parsed_response: dict[str, Any],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Normalize one provider response and recalculate its score."""
    criterion_scores = _normalize_criterion_scores(
        parsed_response.get("criterion_scores"),
        judge_rules,
    )
    recalculated_score = _recalculate_score(criterion_scores, judge_rules)
    status = _resolve_status(recalculated_score)

    findings = _normalize_findings(
        parsed_response.get("findings"),
        _allowed_rule_ids(judge_rules),
    )

    context = judge_rules.get("context") or {}
    if not isinstance(context, dict):
        context = {}

    blind_observation = _normalize_blind_observation(
        parsed_response.get("blind_observation")
    )

    if not _is_tone_presence_consistent(blind_observation):
        findings.append(
            {
                "rule_id": "tone.invalid_tone_presence",
                "severity": "critical",
                "message": (
                    "The LLM response is inconsistent: perceived_tone and "
                    "tone_presence do not describe the same tones."
                ),
                "evidence": {
                    "excerpt": "",
                    "explanation": (
                        "All tones listed in perceived_tone must also appear in "
                        "tone_presence with a percentage."
                    ),
                },
            }
        )

    return {
        "provider": provider,
        "dimension": "tone",
        "status": status,
        "score": recalculated_score,
        "confidence": _safe_nullable_float(parsed_response.get("confidence")),
        "blind_observation": blind_observation,
        "ton_distribution": _normalize_ton_distribution(
            parsed_response.get("ton_distribution")
        ),
        "expected_tone": str(
            parsed_response.get(
                "expected_tone",
                context.get("expected_tone", ""),
            )
        ).strip(),
        "detected_tone": (
            blind_observation.get("perceived_tone", "")
            if isinstance(blind_observation, dict)
            else ""
        ),
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
    context = judge_rules.get("context") or {}
    if not isinstance(context, dict):
        context = {}

    return {
        "provider": provider,
        "dimension": "tone",
        "status": "unknown",
        "score": None,
        "confidence": None,
        "blind_observation": None,
        "ton_distribution": None,
        "expected_tone": str(context.get("expected_tone", "")),
        "detected_tone": "",
        "summary": f"{provider} tone evaluation failed.",
        "criterion_scores": None,
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
    openai_score = openai_result.get("score")
    mistral_score = mistral_result.get("score")

    openai_status = str(openai_result.get("status", "unknown"))
    mistral_status = str(mistral_result.get("status", "unknown"))

    score_gap = None
    if isinstance(openai_score, int) and isinstance(mistral_score, int):
        score_gap = abs(openai_score - mistral_score)

    return {
        "status_match": openai_status == mistral_status,
        "score_gap": score_gap,
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

    return merged_findings[:16]


def _build_final_result(
    *,
    openai_result: dict[str, object],
    mistral_result: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Build the final tone judge result from provider results."""
    agreement = _compute_agreement(openai_result, mistral_result)

    provider_scores = [
        score
        for score in (
            openai_result.get("score"),
            mistral_result.get("score"),
        )
        if isinstance(score, int)
    ]

    if provider_scores:
        final_score = round(sum(provider_scores) / len(provider_scores))
        final_status = _resolve_status(final_score)
    else:
        final_score = None
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
            "guards": judge_rules.get("guards", {}),
            "organization_tones": judge_rules.get("organization_tones", {}),
            "blind_observation": judge_rules.get("blind_observation", {}),
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

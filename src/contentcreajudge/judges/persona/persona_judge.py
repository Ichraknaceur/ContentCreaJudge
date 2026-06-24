"""Judge logic for persona detection and evaluation with OpenAI and Mistral."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable

from contentcreajudge.judges.persona.persona_llm_runner import call_persona_llm
from contentcreajudge.judges.persona.persona_prompt import (
    build_persona_judge_prompt,
)

LLMCaller = Callable[..., str]
logger = logging.getLogger(__name__)

_BLOCKING_SEVERITY = "blocking"
_PASS_SCORE_THRESHOLD = 80
_WARN_SCORE_THRESHOLD = 60


def _safe_json_loads(raw_response: str, provider: str) -> dict[str, object]:
    """Parse the LLM JSON response safely."""
    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError:
        return {
            "dimension": "persona",
            "status": "unknown",
            "score": 0,
            "provider": provider,
            "expected_persona_id": None,
            "detected_persona_id": None,
            "persona_match": False,
            "persona_distribution": [],
            "detected_persona_evaluation": {},
            "expected_persona_evaluation": {},
            "findings": [
                {
                    "rule_id": "persona.invalid_llm_json",
                    "severity": "major",
                    "persona_id": "",
                    "persona_element": "",
                    "message": "The LLM response is not valid JSON.",
                    "evidence": {
                        "excerpt": raw_response[:500],
                        "expected": "A valid JSON object.",
                        "observed": "Invalid JSON response.",
                    },
                }
            ],
            "summary": "Persona judge could not parse the LLM response.",
        }

    if not isinstance(parsed_response, dict):
        return {
            "dimension": "persona",
            "status": "unknown",
            "score": 0,
            "provider": provider,
            "expected_persona_id": None,
            "detected_persona_id": None,
            "persona_match": False,
            "persona_distribution": [],
            "detected_persona_evaluation": {},
            "expected_persona_evaluation": {},
            "findings": [
                {
                    "rule_id": "persona.invalid_llm_payload",
                    "severity": "major",
                    "persona_id": "",
                    "persona_element": "",
                    "message": "The LLM response is not a JSON object.",
                    "evidence": {
                        "excerpt": str(parsed_response)[:500],
                        "expected": "A JSON object.",
                        "observed": "A non-object JSON value.",
                    },
                }
            ],
            "summary": "Persona judge received an invalid LLM payload.",
        }

    return parsed_response


def _safe_score(result: dict[str, object]) -> int:
    """Return a safe score between 0 and 100."""
    try:
        score = int(result.get("score", 0) or 0)
    except (TypeError, ValueError):
        return 0

    return max(0, min(score, 100))


def _safe_status(result: dict[str, object]) -> str:
    """Return a supported status value."""
    status = str(result.get("status", "unknown"))
    if status not in {"pass", "warn", "fail", "unknown"}:
        return "unknown"

    return status


def _safe_eval_score(evaluation: object) -> int:
    """Return a safe score from a persona evaluation object."""
    if not isinstance(evaluation, dict):
        return 0

    return _safe_score(evaluation)


def _safe_criterion_score(value: object) -> float | None:
    """Return a safe criterion score between 0 and 3, or None."""
    if value is None:
        return None

    try:
        score = float(value)
    except (TypeError, ValueError):
        return None

    return max(0.0, min(score, 3.0))


def _get_criteria_weights(
    resolved_rules: dict[str, object],
) -> dict[str, float]:
    """Return criterion weights from resolved rules."""
    criteria = resolved_rules.get("criteria", [])

    if not isinstance(criteria, list):
        return {}

    weights: dict[str, float] = {}

    for criterion in criteria:
        if not isinstance(criterion, dict):
            continue

        criterion_id = criterion.get("criterion_id")
        weight = criterion.get("weight")

        if not criterion_id:
            continue

        try:
            weights[str(criterion_id)] = float(weight)
        except (TypeError, ValueError):
            logger.debug("Skipping invalid criterion weight.", exc_info=True)
            continue

    return weights


def _compute_evaluation_score(
    evaluation: dict[str, object],
    resolved_rules: dict[str, object],
) -> int | None:
    """Compute persona evaluation score from criterion scores."""
    criteria_scores = evaluation.get("criteria_scores", {})

    if not isinstance(criteria_scores, dict):
        return None

    weights = _get_criteria_weights(resolved_rules)

    weighted_sum = 0.0
    used_weight_sum = 0.0

    for criterion_id, weight in weights.items():
        criterion_score = _safe_criterion_score(criteria_scores.get(criterion_id))

        if criterion_score is None:
            continue

        weighted_sum += criterion_score * weight
        used_weight_sum += weight

    if used_weight_sum == 0:
        return None

    score = (weighted_sum / used_weight_sum) * 100 / 3
    return round(score)


def _compute_status_from_score(
    score: int,
    *,
    has_blocking: bool = False,
) -> str:
    """Compute status from score and blocking state."""
    if has_blocking:
        return "fail"

    if score >= _PASS_SCORE_THRESHOLD:
        return "pass"

    if score >= _WARN_SCORE_THRESHOLD:
        return "warn"

    return "fail"


def _normalize_distribution(distribution: object) -> list[dict[str, object]]:
    """Normalize persona distribution items."""
    if not isinstance(distribution, list):
        return []

    normalized_distribution: list[dict[str, object]] = []

    for item in distribution:
        if not isinstance(item, dict):
            continue

        persona_id = item.get("persona_id")
        if not persona_id:
            continue

        try:
            score = int(item.get("score", 0) or 0)
        except (TypeError, ValueError):
            score = 0

        normalized_distribution.append(
            {
                "persona_id": str(persona_id),
                "score": max(0, min(score, 100)),
                "reason": str(item.get("reason", "")),
            }
        )

    return normalized_distribution


def _normalize_evaluation(evaluation: object) -> dict[str, object]:
    """Normalize detected or expected persona evaluation."""
    if not isinstance(evaluation, dict):
        return {
            "persona_id": None,
            "score": 0,
            "criteria_scores": {},
            "identified_persona_elements": {},
            "summary": "",
        }

    criteria_scores = evaluation.get("criteria_scores", {})
    if not isinstance(criteria_scores, dict):
        criteria_scores = {}

    identified_persona_elements = evaluation.get("identified_persona_elements", {})
    if not isinstance(identified_persona_elements, dict):
        identified_persona_elements = {}

    return {
        "persona_id": evaluation.get("persona_id"),
        "score": _safe_eval_score(evaluation),
        "criteria_scores": criteria_scores,
        "identified_persona_elements": identified_persona_elements,
        "summary": str(evaluation.get("summary", "")),
    }


def _normalize_findings(
    findings: object,
    provider: str,
) -> list[dict[str, object]]:
    """Normalize findings and attach the provider name."""
    if not isinstance(findings, list):
        return []

    normalized_findings: list[dict[str, object]] = []

    for finding in findings:
        if not isinstance(finding, dict):
            continue

        normalized_finding = dict(finding)
        rule_id = normalized_finding.get("rule_id")
        severity = normalized_finding.get("severity")

        if not rule_id or not severity:
            continue

        normalized_finding["provider"] = provider
        normalized_findings.append(normalized_finding)

    return normalized_findings


def _has_blocking_finding(result: dict[str, object]) -> bool:
    """Return True when a provider result contains a blocking finding."""
    findings = result.get("findings", [])

    if not isinstance(findings, list):
        return False

    return any(
        isinstance(finding, dict)
        and str(finding.get("severity", "")).lower() == _BLOCKING_SEVERITY
        for finding in findings
    )


def _normalize_persona_result(
    parsed_response: dict[str, object],
    provider: str,
    resolved_rules: dict[str, object],
) -> dict[str, object]:
    """Normalize one LLM persona result."""
    status = _safe_status(parsed_response)
    expected_persona_id = parsed_response.get(
        "expected_persona_id",
        resolved_rules.get("expected_persona_id"),
    )
    detected_persona_id = parsed_response.get("detected_persona_id")

    detected_persona_evaluation = _normalize_evaluation(
        parsed_response.get("detected_persona_evaluation", {})
    )
    expected_persona_evaluation = _normalize_evaluation(
        parsed_response.get("expected_persona_evaluation", {})
    )

    detected_score = _compute_evaluation_score(
        detected_persona_evaluation,
        resolved_rules,
    )
    if detected_score is not None:
        detected_persona_evaluation["score"] = detected_score

    expected_score = _compute_evaluation_score(
        expected_persona_evaluation,
        resolved_rules,
    )
    if expected_score is not None:
        expected_persona_evaluation["score"] = expected_score

    if expected_score is not None:
        normalized_score = expected_score
    else:
        normalized_score = _safe_score(parsed_response)
        if normalized_score == 0 and expected_persona_evaluation.get("score"):
            normalized_score = _safe_eval_score(expected_persona_evaluation)

    persona_match = parsed_response.get("persona_match")
    if not isinstance(persona_match, bool):
        persona_match = (
            bool(expected_persona_id)
            and bool(detected_persona_id)
            and str(expected_persona_id) == str(detected_persona_id)
        )

    findings = _normalize_findings(
        parsed_response.get("findings", []),
        provider,
    )

    has_blocking = any(
        isinstance(finding, dict)
        and str(finding.get("severity", "")).lower() == _BLOCKING_SEVERITY
        for finding in findings
    )

    if has_blocking:
        computed_status = "fail"
    elif status == "unknown":
        computed_status = status
    else:
        computed_status = status

    return {
        "dimension": "persona",
        "status": computed_status,
        "score": normalized_score,
        "provider": provider,
        "expected_persona_id": (
            str(expected_persona_id) if expected_persona_id else None
        ),
        "detected_persona_id": (
            str(detected_persona_id) if detected_persona_id else None
        ),
        "persona_match": persona_match,
        "persona_distribution": _normalize_distribution(
            parsed_response.get("persona_distribution", [])
        ),
        "detected_persona_evaluation": detected_persona_evaluation,
        "expected_persona_evaluation": expected_persona_evaluation,
        "findings": findings,
        "summary": str(
            parsed_response.get(
                "summary",
                resolved_rules.get("messages", {}).get(
                    "unknown",
                    "Persona evaluation completed.",
                ),
            )
        ),
    }


def _run_one_provider(
    *,
    content: str,
    resolved_rules: dict[str, object],
    provider: str,
    llm_caller: LLMCaller,
) -> dict[str, object]:
    """Run persona judge for one provider."""
    prompt = build_persona_judge_prompt(
        content=content,
        resolved_rules=resolved_rules,
    )

    raw_response = llm_caller(
        prompt=prompt,
        provider=provider,
    )

    parsed_response = _safe_json_loads(
        raw_response=raw_response,
        provider=provider,
    )

    return _normalize_persona_result(
        parsed_response=parsed_response,
        provider=provider,
        resolved_rules=resolved_rules,
    )


def _compute_final_status(
    *,
    final_score: int,
    provider_results: list[dict[str, object]],
) -> str:
    """Compute final persona status from expected persona score and blockers."""
    if any(_has_blocking_finding(result) for result in provider_results):
        return "fail"

    if final_score >= _PASS_SCORE_THRESHOLD:
        return "pass"

    if final_score >= _WARN_SCORE_THRESHOLD:
        return "warn"

    return "fail"


def _collect_all_findings(
    provider_results: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Collect all findings from provider results."""
    findings: list[dict[str, object]] = []

    for result in provider_results:
        result_findings = result.get("findings", [])

        if not isinstance(result_findings, list):
            continue

        findings.extend(
            finding for finding in result_findings if isinstance(finding, dict)
        )

    return findings


def _build_agreement(
    provider_results: list[dict[str, object]],
) -> dict[str, object]:
    """Build agreement information between providers."""
    provider_scores = {
        str(result.get("provider", f"provider_{index}")): _safe_score(result)
        for index, result in enumerate(provider_results)
    }

    provider_statuses = {
        str(result.get("provider", f"provider_{index}")): str(
            result.get("status", "unknown")
        )
        for index, result in enumerate(provider_results)
    }

    detected_personas = {
        str(result.get("provider", f"provider_{index}")): result.get(
            "detected_persona_id"
        )
        for index, result in enumerate(provider_results)
    }

    persona_matches = {
        str(result.get("provider", f"provider_{index}")): result.get("persona_match")
        for index, result in enumerate(provider_results)
    }

    scores = list(provider_scores.values())
    statuses = list(provider_statuses.values())
    detected_values = [
        str(persona_id)
        for persona_id in detected_personas.values()
        if persona_id is not None
    ]

    return {
        "status_agreement": len(set(statuses)) == 1 if statuses else False,
        "score_gap": max(scores) - min(scores) if scores else None,
        "detected_persona_agreement": (
            len(set(detected_values)) == 1 if detected_values else False
        ),
        "providers_count": len(provider_results),
        "provider_scores": provider_scores,
        "provider_statuses": provider_statuses,
        "detected_personas": detected_personas,
        "persona_matches": persona_matches,
    }


def run_persona_judge(
    content: str,
    resolved_rules: dict[str, object],
    provider: str | None = None,
    llm_caller: LLMCaller = call_persona_llm,
) -> dict[str, object]:
    """Run persona judge with one provider or all configured LLM providers."""
    if provider is not None:
        result = _run_one_provider(
            content=content,
            resolved_rules=resolved_rules,
            provider=provider,
            llm_caller=llm_caller,
        )
        result["applied_rule"] = {
            "judge_id": resolved_rules.get("judge_id", "persona"),
            "version": resolved_rules.get("version", 2),
            "detection": resolved_rules.get("detection", {}),
            "criteria": resolved_rules.get("criteria", []),
            "hard_rules": resolved_rules.get("hard_rules", []),
            "scoring": resolved_rules.get("scoring", {}),
            "provider": provider,
        }
        return result

    providers = resolved_rules.get("providers", ["openai", "mistral"])

    if not isinstance(providers, list) or not providers:
        providers = ["openai", "mistral"]

    provider_results = [
        _run_one_provider(
            content=content,
            resolved_rules=resolved_rules,
            provider=str(provider),
            llm_caller=llm_caller,
        )
        for provider in providers
    ]

    scores = [_safe_score(result) for result in provider_results]
    final_score = round(sum(scores) / len(scores)) if scores else 0

    findings = _collect_all_findings(provider_results)

    return {
        "dimension": "persona",
        "status": _compute_final_status(
            final_score=final_score,
            provider_results=provider_results,
        ),
        "score": final_score,
        "findings": findings,
        "provider_results": provider_results,
        "agreement": _build_agreement(provider_results),
        "applied_rule": {
            "judge_id": resolved_rules.get("judge_id", "persona"),
            "version": resolved_rules.get("version", 2),
            "detection": resolved_rules.get("detection", {}),
            "criteria": resolved_rules.get("criteria", []),
            "hard_rules": resolved_rules.get("hard_rules", []),
            "scoring": resolved_rules.get("scoring", {}),
            "providers": providers,
        },
    }

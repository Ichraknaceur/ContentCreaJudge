"""Judge logic for brief alignment evaluation."""

from __future__ import annotations

import json
from typing import Any

from contentcreajudge.adapters.llm.client import LLMClientError, call_openai_json
from contentcreajudge.adapters.llm.mistral_client import (
    MistralClientError,
    call_mistral_json,
)
from contentcreajudge.judges.brief.brief_prompt import build_brief_prompt

_PROVIDER_OPENAI = "openai"
_PROVIDER_MISTRAL = "mistral"

_DEFAULT_PASS_THRESHOLD = 80
_DEFAULT_WARN_THRESHOLD = 60

_REQUIRED_CRITERIA = [
    "angle_alignment",
    "axis_development",
    "intended_understanding",
    "scope_adherence",
]

_OPTIONAL_CRITERION = "specific_element_integration"


def _safe_json_loads(raw_response: str) -> dict[str, Any]:
    """Parse a raw JSON response safely."""
    try:
        parsed_response = json.loads(raw_response)
    except json.JSONDecodeError:
        return {
            "error": "invalid_json",
            "raw_response": raw_response[:500],
        }

    if not isinstance(parsed_response, dict):
        return {
            "error": "invalid_json_object",
            "raw_response": raw_response[:500],
        }

    return parsed_response


def _safe_int(value: object, default: int = 0) -> int:
    """Convert a value to an integer between 0 and 100."""
    if value is None:
        return default

    try:
        number = int(float(str(value)))
    except TypeError, ValueError:
        return default

    return max(0, min(100, number))


def _safe_threshold(
    value: object,
    default: int,
) -> int:
    try:
        return int(value)
    except TypeError, ValueError:
        return default


def _resolve_status(score: int | None, judge_rules: dict[str, object]) -> str:
    """Resolve status from score and thresholds."""
    if score is None:
        return "unknown"

    thresholds = judge_rules.get("score_thresholds") or {}
    if not isinstance(thresholds, dict):
        thresholds = {}

    pass_threshold = _safe_threshold(
        thresholds.get("pass"),
        _DEFAULT_PASS_THRESHOLD,
    )
    warn_threshold = _safe_threshold(
        thresholds.get("warn"),
        _DEFAULT_WARN_THRESHOLD,
    )

    if score >= pass_threshold:
        return "pass"

    if score >= warn_threshold:
        return "warn"

    return "fail"


def _criterion_weights(judge_rules: dict[str, object]) -> dict[str, float]:
    """Return enabled criterion weights from judge rules."""
    criteria = judge_rules.get("criteria") or {}

    if not isinstance(criteria, dict):
        return {}

    weights: dict[str, float] = {}

    for criterion_id, criterion_config in criteria.items():
        if not isinstance(criterion_config, dict):
            continue

        if not bool(criterion_config.get("enabled", True)):
            continue

        try:
            weight = float(criterion_config.get("weight", 0))
        except TypeError, ValueError:
            weight = 0.0

        weights[str(criterion_id)] = weight

    return weights


def _normalize_evidence(value: object) -> list[str]:
    """Normalize evidence returned by the LLM."""
    if not isinstance(value, list):
        return []

    return [str(item).strip() for item in value if str(item).strip()][:5]


def _brief_contains_specific_element(brief: str) -> bool:
    """Return whether the original brief contains a specific element section."""
    normalized = brief.lower()

    return (
        "élément spécifique à intégrer" in normalized
        or "élément spécifique" in normalized
        or "element specifique a integrer" in normalized
        or "element specifique" in normalized
    )


def _normalize_criterion_result(
    raw_value: object,
) -> dict[str, object]:
    """Normalize one criterion result."""
    if not isinstance(raw_value, dict):
        return {
            "score": 0,
            "confidence": 0,
            "justification": "Criterion result is missing or invalid.",
            "evidence": [],
        }

    return {
        "score": _safe_int(raw_value.get("score")),
        "confidence": _safe_int(raw_value.get("confidence")),
        "justification": str(raw_value.get("justification", "")).strip(),
        "evidence": _normalize_evidence(raw_value.get("evidence")),
    }


def _normalize_specific_element(
    raw_value: object,
    *,
    has_specific_element: bool,
) -> dict[str, object]:
    """Normalize the optional specific element criterion."""
    if not isinstance(raw_value, dict):
        return {
            "applicable": has_specific_element,
            "score": 0 if has_specific_element else None,
            "confidence": 0 if has_specific_element else None,
            "justification": "Specific element criterion is missing or invalid.",
            "evidence": [],
        }

    if not has_specific_element:
        return {
            "applicable": False,
            "score": None,
            "confidence": None,
            "justification": str(raw_value.get("justification", "")).strip(),
            "evidence": _normalize_evidence(raw_value.get("evidence")),
        }

    return {
        "applicable": True,
        "score": _safe_int(raw_value.get("score")),
        "confidence": _safe_int(raw_value.get("confidence")),
        "justification": str(raw_value.get("justification", "")).strip(),
        "evidence": _normalize_evidence(raw_value.get("evidence")),
    }


def _normalize_evaluation(
    parsed_response: dict[str, Any],
    *,
    has_specific_element: bool = False,
) -> dict[str, object]:
    """Normalize the evaluation block returned by the LLM."""
    raw_evaluation = parsed_response.get("evaluation") or {}
    if not isinstance(raw_evaluation, dict):
        raw_evaluation = {}

    normalized: dict[str, object] = {}

    for criterion_id in _REQUIRED_CRITERIA:
        normalized[criterion_id] = _normalize_criterion_result(
            raw_evaluation.get(criterion_id),
        )

    normalized[_OPTIONAL_CRITERION] = _normalize_specific_element(
        raw_evaluation.get(_OPTIONAL_CRITERION),
        has_specific_element=has_specific_element,
    )

    return normalized


def _recalculate_score(
    evaluation: dict[str, object],
    judge_rules: dict[str, object],
) -> int | None:
    """Recalculate the brief score from criterion scores."""
    weights = _criterion_weights(judge_rules)

    weighted_sum = 0.0
    active_weight_sum = 0.0

    for criterion_id in _REQUIRED_CRITERIA:
        criterion_result = evaluation.get(criterion_id)
        if not isinstance(criterion_result, dict):
            continue

        weight = weights.get(criterion_id, 0)
        score = _safe_int(criterion_result.get("score"))

        weighted_sum += score * weight
        active_weight_sum += weight

    specific_result = evaluation.get(_OPTIONAL_CRITERION)
    if isinstance(specific_result, dict) and specific_result.get("applicable"):
        weight = weights.get(_OPTIONAL_CRITERION, 0)
        score = _safe_int(specific_result.get("score"))

        weighted_sum += score * weight
        active_weight_sum += weight

    if active_weight_sum <= 0:
        return None

    return round(weighted_sum / active_weight_sum)


def _average_confidence(evaluation: dict[str, object]) -> int | None:
    """Compute average provider confidence from applicable criteria."""
    confidence_values: list[int] = []

    for criterion_id in _REQUIRED_CRITERIA:
        criterion_result = evaluation.get(criterion_id)
        if isinstance(criterion_result, dict):
            confidence_values.append(_safe_int(criterion_result.get("confidence")))

    specific_result = evaluation.get(_OPTIONAL_CRITERION)
    if isinstance(specific_result, dict) and specific_result.get("applicable"):
        confidence_values.append(_safe_int(specific_result.get("confidence")))

    if not confidence_values:
        return None

    return round(sum(confidence_values) / len(confidence_values))


def _normalize_brief_decomposition(value: object) -> dict[str, object]:
    """Normalize brief decomposition block."""
    if not isinstance(value, dict):
        return {
            "angle_message_central": "",
            "axe_a_developper": "",
            "delimitation_traitement": None,
            "comprehension_cible": "",
            "element_specifique": None,
        }

    return {
        "angle_message_central": str(value.get("angle_message_central", "")).strip(),
        "axe_a_developper": str(value.get("axe_a_developper", "")).strip(),
        "delimitation_traitement": (
            str(value.get("delimitation_traitement")).strip()
            if value.get("delimitation_traitement") is not None
            else None
        ),
        "comprehension_cible": str(value.get("comprehension_cible", "")).strip(),
        "element_specifique": (
            str(value.get("element_specifique")).strip()
            if value.get("element_specifique") is not None
            else None
        ),
    }


def _normalize_distinctive_elements_review(value: object) -> dict[str, object]:
    """Normalize distinctive elements review returned by the LLM."""
    if not isinstance(value, dict):
        return {"elements": []}

    elements = value.get("elements")

    if not isinstance(elements, list):
        return {"elements": []}

    normalized_elements: list[dict[str, object]] = []

    for item in elements[:3]:
        if not isinstance(item, dict):
            continue

        presence = str(item.get("presence_in_article", "")).strip()
        if presence not in {"strong", "partial", "weak", "absent", "replaced"}:
            presence = "weak"

        normalized_elements.append(
            {
                "element": str(item.get("element", "")).strip(),
                "presence_in_article": presence,
                "evidence": str(item.get("evidence", "")).strip(),
                "impact_on_score": str(item.get("impact_on_score", "")).strip(),
            }
        )

    return {"elements": normalized_elements}


def _provider_error_result(
    *,
    provider: str,
    error: Exception,
) -> dict[str, object]:
    """Return an unknown result when a provider fails."""
    return {
        "provider": provider,
        "dimension": "brief",
        "status": "unknown",
        "score": None,
        "confidence": None,
        "brief_decomposition": None,
        "evaluation": None,
        "summary": f"{provider} brief evaluation failed.",
        "findings": [
            {
                "rule_id": "brief.provider_error",
                "severity": "critical",
                "message": f"{provider} failed during brief evaluation.",
                "evidence": {
                    "excerpt": "",
                    "explanation": str(error),
                },
            }
        ],
    }


def _invalid_response_result(
    *,
    provider: str,
    parsed_response: dict[str, Any],
) -> dict[str, object]:
    """Return an unknown result for invalid LLM JSON."""
    return {
        "provider": provider,
        "dimension": "brief",
        "status": "unknown",
        "score": None,
        "confidence": None,
        "brief_decomposition": None,
        "evaluation": None,
        "summary": "Brief evaluation could not be completed reliably.",
        "findings": [
            {
                "rule_id": "brief.invalid_llm_response",
                "severity": "critical",
                "message": "The LLM response is not valid for brief evaluation.",
                "evidence": {
                    "excerpt": str(parsed_response.get("raw_response", "")),
                    "explanation": str(parsed_response.get("error", "")),
                },
            }
        ],
    }


def _specific_element_low_score_cap(
    judge_rules: dict[str, object],
) -> dict[str, object] | None:
    """Return enabled specific element score cap configuration."""
    aggregation = judge_rules.get("aggregation") or {}
    if not isinstance(aggregation, dict):
        return None

    score_caps = aggregation.get("score_caps") or {}
    if not isinstance(score_caps, dict) or not score_caps.get("enabled", False):
        return None

    specific_cap = score_caps.get("specific_element_low_score_cap") or {}
    if not isinstance(specific_cap, dict) or not specific_cap.get("enabled", False):
        return None

    return specific_cap


def _apply_score_caps(
    score: int | None,
    evaluation: dict[str, object] | None,
    judge_rules: dict[str, object],
) -> int | None:
    """Apply backend score caps based on configured aggregation rules."""
    if score is None or not isinstance(evaluation, dict):
        return score

    specific_cap = _specific_element_low_score_cap(judge_rules)
    specific_result = evaluation.get(_OPTIONAL_CRITERION)
    if (
        specific_cap is None
        or not isinstance(specific_result, dict)
        or specific_result.get("applicable") is not True
    ):
        return score

    threshold = _safe_threshold(specific_cap.get("threshold"), 40)
    max_final_score = _safe_threshold(specific_cap.get("max_final_score"), 69)

    specific_score = specific_result.get("score")
    if specific_score is None:
        return score

    if _safe_int(specific_score) < threshold:
        return min(score, max_final_score)

    return score


def _normalize_provider_result(
    *,
    provider: str,
    parsed_response: dict[str, Any],
    judge_rules: dict[str, object],
    has_specific_element: bool,
) -> dict[str, object]:
    """Normalize one provider response and recalculate its score."""
    if "error" in parsed_response:
        return _invalid_response_result(
            provider=provider,
            parsed_response=parsed_response,
        )

    brief_decomposition = _normalize_brief_decomposition(
        parsed_response.get("brief_decomposition")
    )

    evaluation = _normalize_evaluation(
        parsed_response,
        has_specific_element=has_specific_element,
    )
    recalculated_score = _recalculate_score(evaluation, judge_rules)
    capped_score = _apply_score_caps(
        score=recalculated_score,
        evaluation=evaluation,
        judge_rules=judge_rules,
    )
    status = _resolve_status(capped_score, judge_rules)

    return {
        "provider": provider,
        "dimension": "brief",
        "status": status,
        "score": capped_score,
        "confidence": _average_confidence(evaluation),
        "brief_decomposition": brief_decomposition,
        "distinctive_elements_review": _normalize_distinctive_elements_review(
            parsed_response.get("distinctive_elements_review")
        ),
        "evaluation": evaluation,
        "summary": str(parsed_response.get("global_summary", "")).strip(),
        "findings": [],
    }


def _compute_agreement(
    openai_result: dict[str, object],
    mistral_result: dict[str, object],
) -> dict[str, object]:
    """Compute agreement between OpenAI and Mistral."""
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
    """Merge findings from provider results."""
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
    """Build the final Brief Judge result from provider results."""
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
        final_status = _resolve_status(final_score, judge_rules)
    else:
        final_score = None
        final_status = "unknown"

    provider_confidences = [
        confidence
        for confidence in (
            openai_result.get("confidence"),
            mistral_result.get("confidence"),
        )
        if isinstance(confidence, int)
    ]

    final_confidence = (
        round(sum(provider_confidences) / len(provider_confidences))
        if provider_confidences
        else None
    )

    messages = judge_rules.get("messages") or {}
    if not isinstance(messages, dict):
        messages = {}

    return {
        "dimension": "brief",
        "status": final_status,
        "score": final_score,
        "confidence": final_confidence,
        "summary": messages.get(
            final_status,
            "Brief evaluation completed.",
        ),
        "provider_results": {
            "openai": openai_result,
            "mistral": mistral_result,
        },
        "agreement": _compute_agreement(openai_result, mistral_result),
        "findings": _merge_findings(openai_result, mistral_result),
        "applied_rule": {
            "judge_id": judge_rules.get("judge_id", "brief"),
            "version": judge_rules.get("version", 1),
            "criteria": judge_rules.get("criteria", {}),
            "score_thresholds": judge_rules.get("score_thresholds", {}),
            "aggregation": judge_rules.get("aggregation", {}),
        },
    }


def run_brief_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate brief alignment with OpenAI and Mistral."""
    brief = str(preprocessed_content.get("normalized_brief", ""))
    article = str(preprocessed_content.get("article_text", ""))
    has_specific_element = _brief_contains_specific_element(brief)

    prompt = build_brief_prompt(
        brief=brief,
        article=article,
    )

    try:
        openai_raw_response = call_openai_json(prompt=prompt)
        openai_result = _normalize_provider_result(
            provider=_PROVIDER_OPENAI,
            parsed_response=_safe_json_loads(openai_raw_response),
            judge_rules=judge_rules,
            has_specific_element=has_specific_element,
        )
    except LLMClientError as exc:
        openai_result = _provider_error_result(
            provider=_PROVIDER_OPENAI,
            error=exc,
        )

    try:
        mistral_raw_response = call_mistral_json(prompt=prompt)
        mistral_result = _normalize_provider_result(
            provider=_PROVIDER_MISTRAL,
            parsed_response=_safe_json_loads(mistral_raw_response),
            judge_rules=judge_rules,
            has_specific_element=has_specific_element,
        )
    except MistralClientError as exc:
        mistral_result = _provider_error_result(
            provider=_PROVIDER_MISTRAL,
            error=exc,
        )

    return _build_final_result(
        openai_result=openai_result,
        mistral_result=mistral_result,
        judge_rules=judge_rules,
    )

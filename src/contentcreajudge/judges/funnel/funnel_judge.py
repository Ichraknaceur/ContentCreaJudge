"""Judge logic for funnel evaluation."""

from __future__ import annotations

import json
from typing import Any

from contentcreajudge.adapters.llm.client import call_openai_json
from contentcreajudge.adapters.llm.mistral_client import call_mistral_json
from contentcreajudge.judges.funnel.funnel_prompt import build_funnel_prompt

_ALLOWED_PROVIDERS = {"openai", "mistral"}
_DEFAULT_ALLOWED_FUNNELS = ["awareness", "consideration", "decision", "loyalty"]
_NEIGHBOR_PAIR_SIZE = 2


class FunnelJudgeError(RuntimeError):
    """Raised when the funnel judge cannot complete evaluation."""


def _call_llm_provider(
    *,
    prompt: str,
    provider: str,
    model: str | None,
    temperature: float,
) -> str:
    """Call the selected LLM provider."""
    normalized_provider = provider.strip().lower()

    if normalized_provider not in _ALLOWED_PROVIDERS:
        raise FunnelJudgeError(f"Unsupported LLM provider for funnel judge: {provider}")

    if normalized_provider == "mistral":
        return call_mistral_json(
            prompt=prompt,
            model=model,
            temperature=temperature,
        )

    return call_openai_json(
        prompt=prompt,
        model=model,
        temperature=temperature,
    )


def _parse_llm_json(raw_response: str) -> dict[str, Any]:
    """Parse the raw LLM response as JSON."""
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise FunnelJudgeError("Funnel judge LLM response is not valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise FunnelJudgeError("Funnel judge LLM response must be a JSON object.")

    return parsed


def _safe_dict(value: object) -> dict[str, Any]:
    """Return value as dict when possible, otherwise an empty dict."""
    if isinstance(value, dict):
        return value

    return {}


def _safe_list(value: object) -> list[object]:
    """Return value as list when possible, otherwise an empty list."""
    if isinstance(value, list):
        return value

    return []


def _safe_score(value: object) -> float:
    """Convert a score to a bounded numeric value."""
    try:
        score = float(value)
    except TypeError, ValueError:
        return 0.0

    return min(max(score, 0.0), 100.0)


def _resolve_detected_funnel(
    phase_1: dict[str, Any],
    allowed_funnels: list[str],
) -> str:
    """Resolve the detected funnel from phase 1 output."""
    detected_funnel = str(phase_1.get("detected_funnel", "")).strip().lower()

    if detected_funnel in allowed_funnels:
        return detected_funnel

    scores_by_funnel = _safe_dict(phase_1.get("scores_by_funnel"))

    if not scores_by_funnel:
        return ""

    valid_scores = {
        funnel: _safe_score(scores_by_funnel.get(funnel, 0))
        for funnel in allowed_funnels
    }

    return max(valid_scores, key=valid_scores.get)


def _compute_expected_funnel_score(
    *,
    criteria_scores: dict[str, object],
    criteria_rules: dict[str, object],
) -> int:
    """Compute the weighted score for the expected funnel."""
    weighted_score = 0.0

    for criterion_name, criterion_rule in criteria_rules.items():
        if not isinstance(criterion_rule, dict):
            continue

        weight = float(criterion_rule.get("weight", 0))
        criterion_score = _safe_score(criteria_scores.get(criterion_name, 0))

        weighted_score += criterion_score * weight

    return round(weighted_score)


def _is_neighbor_funnel(
    *,
    detected_funnel: str,
    expected_funnel: str,
    neighbor_pairs: list[object],
) -> bool:
    """Return True when detected and expected funnels are configured neighbors."""
    current_pair = {detected_funnel, expected_funnel}

    for neighbor_pair in neighbor_pairs:
        if not isinstance(neighbor_pair, list | tuple):
            continue

        if len(neighbor_pair) != _NEIGHBOR_PAIR_SIZE:
            continue

        configured_pair = {
            str(neighbor_pair[0]).strip().lower(),
            str(neighbor_pair[1]).strip().lower(),
        }

        if current_pair == configured_pair:
            return True

    return False


def _compute_funnel_alignment_score(
    *,
    detected_funnel: str,
    expected_funnel: str,
    funnel_alignment_rules: dict[str, object],
) -> int:
    """Compute the alignment score between detected and expected funnel."""
    if detected_funnel == expected_funnel:
        return int(funnel_alignment_rules.get("exact_match_score", 100))

    neighbor_pairs = funnel_alignment_rules.get("neighbor_pairs", [])

    if isinstance(neighbor_pairs, list) and _is_neighbor_funnel(
        detected_funnel=detected_funnel,
        expected_funnel=expected_funnel,
        neighbor_pairs=neighbor_pairs,
    ):
        return int(funnel_alignment_rules.get("neighbor_match_score", 50))

    return int(funnel_alignment_rules.get("mismatch_score", 0))


def _compute_final_score(
    *,
    expected_funnel_score: int,
    funnel_alignment_score: int,
    score_calculation_rules: dict[str, object],
) -> int:
    """Compute the final funnel score."""
    expected_funnel_weight = float(
        score_calculation_rules.get("expected_funnel_weight", 0.80)
    )
    funnel_alignment_weight = float(
        score_calculation_rules.get("funnel_alignment_weight", 0.20)
    )

    final_score = (
        expected_funnel_score * expected_funnel_weight
        + funnel_alignment_score * funnel_alignment_weight
    )

    min_score = int(score_calculation_rules.get("min_score", 0))
    max_score = int(score_calculation_rules.get("max_score", 100))

    return min(max(round(final_score), min_score), max_score)


def _resolve_status(final_score: int, status_thresholds: dict[str, object]) -> str:
    """Resolve the judge status from the final score."""
    pass_min_score = int(status_thresholds.get("pass_min_score", 80))
    warning_min_score = int(status_thresholds.get("warning_min_score", 60))

    if final_score >= pass_min_score:
        return "pass"

    if final_score >= warning_min_score:
        return "warning"

    return "fail"


def run_funnel_judge(
    content: str,
    judge_rules: dict[str, object],
    *,
    provider: str = "openai",
    model: str | None = None,
    temperature: float = 0.0,
) -> dict[str, object]:
    """Run the funnel judge and return a structured evaluation result."""
    prompt = build_funnel_prompt(content, judge_rules)

    raw_response = _call_llm_provider(
        prompt=prompt,
        provider=provider,
        model=model,
        temperature=temperature,
    )

    llm_result = _parse_llm_json(raw_response)

    phase_1 = _safe_dict(llm_result.get("phase_1"))
    phase_2 = _safe_dict(llm_result.get("phase_2"))

    expected_funnel = str(judge_rules.get("expected_funnel", "")).strip().lower()
    allowed_funnels = judge_rules.get("allowed_funnels") or _DEFAULT_ALLOWED_FUNNELS

    if not isinstance(allowed_funnels, list):
        allowed_funnels = _DEFAULT_ALLOWED_FUNNELS

    allowed_funnels = [str(funnel).strip().lower() for funnel in allowed_funnels]

    detected_funnel = _resolve_detected_funnel(
        phase_1=phase_1,
        allowed_funnels=allowed_funnels,
    )

    criteria_scores = _safe_dict(phase_2.get("criteria_scores"))

    criteria_rules = _safe_dict(judge_rules.get("criteria"))
    score_calculation_rules = _safe_dict(judge_rules.get("score_calculation"))
    funnel_alignment_rules = _safe_dict(judge_rules.get("funnel_alignment"))
    status_thresholds = _safe_dict(judge_rules.get("status_thresholds"))

    expected_funnel_score = _compute_expected_funnel_score(
        criteria_scores=criteria_scores,
        criteria_rules=criteria_rules,
    )

    funnel_alignment_score = _compute_funnel_alignment_score(
        detected_funnel=detected_funnel,
        expected_funnel=expected_funnel,
        funnel_alignment_rules=funnel_alignment_rules,
    )

    final_score = _compute_final_score(
        expected_funnel_score=expected_funnel_score,
        funnel_alignment_score=funnel_alignment_score,
        score_calculation_rules=score_calculation_rules,
    )

    status = _resolve_status(
        final_score=final_score,
        status_thresholds=status_thresholds,
    )

    phase_1["detected_funnel"] = detected_funnel
    phase_2["expected_funnel"] = expected_funnel
    phase_2["expected_funnel_score"] = expected_funnel_score
    phase_2["funnel_alignment_score"] = funnel_alignment_score
    phase_2["final_score"] = final_score

    return {
        "dimension": "funnel",
        "status": status,
        "score": final_score,
        "provider": provider,
        "model": model,
        "applied_rule": judge_rules,
        "phase_1": phase_1,
        "phase_2": phase_2,
        "findings": _safe_list(llm_result.get("findings")),
        "raw_llm_result": llm_result,
    }

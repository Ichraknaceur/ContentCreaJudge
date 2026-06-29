"""LLM-based judge logic for evergreen evaluation."""

from __future__ import annotations

import json
import os
from typing import Any

from contentcreajudge.adapters.llm.client import LLMClientError, call_openai_json


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _safe_int(value: object, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _safe_float(value: object, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _build_temporal_signals(preprocessed_content: dict[str, object]) -> str:
    temporal_references = _as_list(preprocessed_content.get("temporal_references"))

    signals = {
        "temporal_references_count": preprocessed_content.get(
            "temporal_references_count",
            0,
        ),
        "temporal_references": temporal_references,
    }

    return json.dumps(signals, ensure_ascii=False, indent=2)


def _build_prompt(
    *,
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> str:
    prompt_template = str(judge_rules.get("prompt_template", ""))
    content = str(
        preprocessed_content.get("normalized_text")
        or preprocessed_content.get("original_content")
        or "",
    )
    temporal_signals = _build_temporal_signals(preprocessed_content)

    return prompt_template.replace("{{CONTENT}}", content).replace(
        "{{TEMPORAL_SIGNALS}}",
        temporal_signals,
    )


def _parse_llm_json(raw_response: str) -> dict[str, Any]:
    """Parse a JSON object returned by the LLM, with light cleanup."""
    cleaned_response = raw_response.strip()

    if cleaned_response.startswith("```"):
        cleaned_response = cleaned_response.removeprefix("```json").removeprefix("```")
        cleaned_response = cleaned_response.removesuffix("```").strip()

    start_index = cleaned_response.find("{")
    end_index = cleaned_response.rfind("}")

    if start_index == -1 or end_index == -1 or end_index <= start_index:
        raise ValueError("LLM response is not valid JSON.")

    json_candidate = cleaned_response[start_index : end_index + 1]

    try:
        parsed = json.loads(json_candidate)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response is not valid JSON.") from exc

    if not isinstance(parsed, dict):
        raise TypeError("LLM response JSON must be an object.")

    return parsed


def _compute_status(score: int, judge_rules: dict[str, object]) -> str:
    scoring = _as_dict(judge_rules.get("scoring"))

    pass_min_score = _safe_int(scoring.get("pass_min_score"), 70)
    warn_min_score = _safe_int(scoring.get("warn_min_score"), 50)

    if score >= pass_min_score:
        return "pass"

    if score >= warn_min_score:
        return "warn"

    return "fail"


def _build_findings(llm_payload: dict[str, Any]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []

    passages = _as_list(llm_payload.get("passages_problematiques"))
    for passage in passages:
        if not isinstance(passage, dict):
            continue

        findings.append(
            {
                "rule_id": "evergreen.llm.problematic_passage",
                "severity": str(passage.get("gravite", "moyenne")),
                "message": str(passage.get("probleme", "")),
                "evidence": {
                    "extrait": str(passage.get("extrait", "")),
                },
            },
        )

    return findings


def _error_result(
    *,
    judge_rules: dict[str, object],
    error_message: str,
) -> dict[str, object]:
    llm_messages = _as_dict(judge_rules.get("llm_messages"))

    return {
        "dimension": "evergreen",
        "status": "fail",
        "score": 0,
        "applied_rule": judge_rules,
        "findings": [
            {
                "rule_id": "evergreen.llm_error",
                "severity": "major",
                "message": str(
                    llm_messages.get(
                        "llm_error",
                        "The evergreen evaluation could not be completed reliably.",
                    ),
                ),
                "evidence": {
                    "error": error_message,
                },
            },
        ],
        "llm_evaluation": {},
        "llm_raw_response": "",
    }


def run_evergreen_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate evergreen quality using an LLM."""
    prompt = _build_prompt(
        preprocessed_content=preprocessed_content,
        judge_rules=judge_rules,
    )

    if not prompt.strip():
        return _error_result(
            judge_rules=judge_rules,
            error_message="Missing prompt_template in evergreen rules.",
        )

    llm_config = _as_dict(judge_rules.get("llm"))
    model_env_var = str(llm_config.get("model_env_var", "OPENAI_EVERGREEN_MODEL"))
    model = os.getenv(model_env_var) or str(
        llm_config.get("default_model", "gpt-4.1-mini"),
    )
    temperature = _safe_float(llm_config.get("temperature"), 0.0)

    try:
        raw_response = call_openai_json(
            prompt=prompt,
            model=model,
            temperature=temperature,
        )
        llm_payload = _parse_llm_json(raw_response)

    except (LLMClientError, TypeError, ValueError) as exc:
        return _error_result(
            judge_rules=judge_rules,
            error_message=str(exc),
        )

    score = _safe_int(
        llm_payload.get("score_global_evergreen")
        or llm_payload.get("Score_global")
        or llm_payload.get("Score global")
        or llm_payload.get("score_global")
        or llm_payload.get("score"),
        0,
    )
    status = _compute_status(score, judge_rules)
    findings = _build_findings(llm_payload)

    return {
        "dimension": "evergreen",
        "status": status,
        "score": score,
        "applied_rule": judge_rules,
        "findings": findings,
        "llm_evaluation": llm_payload,
        "llm_raw_response": raw_response,
    }

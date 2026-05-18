"""Global orchestration for evaluation flows."""

from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING
from uuid import uuid4

from contentcreajudge.application.orchestration.judge_registry import (
    get_runnable_judges,
)
from contentcreajudge.preprocessing.orchestration.global_preprocessor import (
    preprocess_global_content,
)

if TYPE_CHECKING:
    from contentcreajudge.application.orchestration.judge_registry import JudgeFlow


async def _run_judge(
    judge_name: str,
    judge_flow: JudgeFlow,
    payload: dict[str, object],
) -> dict[str, object]:
    """Run one judge flow and protect the global evaluation from judge errors."""
    try:
        if inspect.iscoroutinefunction(judge_flow):
            result = await judge_flow(payload)
        else:
            result = await asyncio.to_thread(judge_flow, payload)
    except Exception as exc:  # noqa: BLE001
        return {
            "judge": judge_name,
            "status": "error",
            "result": None,
            "error": str(exc),
        }
    else:
        return {
            "judge": judge_name,
            "status": "completed",
            "result": result,
            "error": None,
        }


async def execute_global_evaluation(payload: dict[str, object]) -> dict[str, object]:
    """Execute enabled judges and return a first global evaluation report."""
    request_id = str(payload.get("request_id") or uuid4())
    profile = str(payload.get("profile", "default"))
    content = str(payload.get("content", ""))

    context = payload.get("context") or {}
    if not isinstance(context, dict):
        context = {}

    internal_domain = "https://contentcrea.com"

    if isinstance(context, dict):
        internal_domain = str(
            context.get("organization_domain") or "https://contentcrea.com"
        )

    global_preprocessing = preprocess_global_content(
        content=content,
        internal_domain=internal_domain,
    )

    enriched_payload = {
        **payload,
        "global_preprocessing": global_preprocessing,
    }

    runnable_judges = get_runnable_judges(payload.get("enabled_judges"))

    tasks = [
        _run_judge(
            judge_name=judge_name,
            judge_flow=judge_flow,
            payload=enriched_payload,
        )
        for judge_name, judge_flow in runnable_judges.items()
    ]

    judge_executions = await asyncio.gather(*tasks)

    dimension_results: list[dict[str, object]] = []
    technical_errors: list[dict[str, object]] = []

    for execution in judge_executions:
        if execution.get("status") == "error":
            technical_errors.append(execution)
            continue

        result = execution.get("result")

        if not isinstance(result, dict):
            technical_errors.append(
                {
                    "judge": execution.get("judge"),
                    "status": "error",
                    "result": None,
                    "error": "Judge returned an invalid result.",
                }
            )
            continue

        judge_result = result.get("judge_result")

        if not isinstance(judge_result, dict):
            technical_errors.append(
                {
                    "judge": execution.get("judge", "unknown"),
                    "status": "error",
                    "result": None,
                    "error": "Missing or invalid judge_result.",
                }
            )
            continue

        dimension_results.append(judge_result)

    judge_results = _build_judge_results(dimension_results)

    return {
        "evaluation_id": request_id,
        "status": "completed",
        "score": None,
        "summary": _build_global_summary(dimension_results, technical_errors),
        "global_preprocessing": global_preprocessing,
        "judge_results": judge_results,
        "dimension_results": dimension_results,
        "technical_errors": technical_errors,
        "metadata": {
            "profile": profile,
            "enabled_judges": list(runnable_judges.keys()),
        },
    }


def _build_judge_results(
    dimension_results: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Build a safe simplified per-judge report for the global evaluation."""
    judge_results: list[dict[str, object]] = []

    for result in dimension_results:
        findings = result.get("findings", [])
        if not isinstance(findings, list):
            findings = []

        subscores = result.get("subscores", {})
        if not isinstance(subscores, dict):
            subscores = {}

        judge_results.append(
            {
                "judge": result.get("dimension", "unknown"),
                "status": result.get("status", "unknown"),
                "score": result.get("score"),
                "subscores": subscores,
                "semantic_signals": result.get("semantic_signals", {}),
                "semantic_compensation": result.get("semantic_compensation", {}),
                "overoptimization_signals": result.get(
                    "overoptimization_signals",
                    {},
                ),
                "findings": findings,
            }
        )

    return judge_results


def _resolve_global_status(
    dimension_results: list[dict[str, object]],
    technical_errors: list[dict[str, object]],
) -> str:
    """Resolve the aggregate business status for the global evaluation."""
    if technical_errors and not dimension_results:
        return "error"

    if any(result.get("status") == "fail" for result in dimension_results):
        return "fail"

    if technical_errors:
        return "warn"

    return "pass"


def _compute_global_score(dimension_results: list[dict[str, object]]) -> int:
    """Compute a simple average score across completed judge dimensions."""
    scores = []

    for result in dimension_results:
        score = result.get("score")

        if isinstance(score, int | float):
            scores.append(float(score))

    if not scores:
        return 0

    return round(sum(scores) / len(scores))


def _build_global_summary(
    dimension_results: list[dict[str, object]],
    technical_errors: list[dict[str, object]],
) -> str:
    """Build a short readable summary for the global evaluation."""
    if technical_errors and not dimension_results:
        return "Global evaluation could not be completed."

    if technical_errors:
        return "Global evaluation completed with some technical errors."

    return f"Global evaluation completed with {len(dimension_results)} judge result(s)."

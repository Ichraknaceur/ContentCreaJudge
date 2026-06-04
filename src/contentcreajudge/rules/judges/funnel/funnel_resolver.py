"""Rule resolver for the funnel judge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from contentcreajudge.judges.funnel.exceptions import (
    InvalidFunnelRulesError,
    MissingFunnelContextError,
    UnsupportedFunnelValueError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config

_EXPECTED_WEIGHT_SUM = 1.0
_WEIGHT_TOLERANCE = 0.001


def _normalize_funnel(value: object) -> str:
    """Normalize a funnel value from the evaluation context."""
    return str(value).strip().lower()


def _validate_criteria_weights(
    expected_funnel: str,
    criteria: dict[str, Any],
) -> None:
    """Validate that criteria weights for one funnel sum to 1."""
    if not criteria:
        raise InvalidFunnelRulesError(
            f"No criteria configured for funnel: {expected_funnel}",
            details={"expected_funnel": expected_funnel},
        )

    weight_sum = sum(
        float(criterion_config.get("weight", 0))
        for criterion_config in criteria.values()
        if isinstance(criterion_config, dict)
    )

    if abs(weight_sum - _EXPECTED_WEIGHT_SUM) > _WEIGHT_TOLERANCE:
        raise InvalidFunnelRulesError(
            f"Invalid criteria weight sum for funnel: {expected_funnel}",
            details={
                "expected_funnel": expected_funnel,
                "weight_sum": weight_sum,
                "expected_weight_sum": _EXPECTED_WEIGHT_SUM,
            },
        )


def resolve_funnel_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the funnel rules defined in the YAML based on the evaluation context."""
    config_path = Path(__file__).with_name("funnel.yaml")

    config = load_yaml_config(config_path)

    rules = config.get("funnel_rules") or {}

    expected_funnel_raw = context.get("expected_funnel")

    if not expected_funnel_raw:
        raise MissingFunnelContextError("expected_funnel")

    expected_funnel = _normalize_funnel(expected_funnel_raw)

    allowed_funnels = rules.get("allowed_funnels") or []

    if expected_funnel not in allowed_funnels:
        raise UnsupportedFunnelValueError(
            "expected_funnel",
            expected_funnel,
            list(allowed_funnels),
        )

    criteria_by_funnel = rules.get("criteria_by_funnel") or {}
    expected_funnel_criteria = criteria_by_funnel.get(expected_funnel) or {}

    _validate_criteria_weights(expected_funnel, expected_funnel_criteria)

    return {
        "judge_id": rules.get("judge_id", "funnel"),
        "version": rules.get("version", 1),
        "label": rules.get("label", "Funnel judge"),
        "description": rules.get(
            "description",
            "Evaluate funnel stage compliance.",
        ),
        "expected_funnel": expected_funnel,
        "allowed_funnels": allowed_funnels,
        "criteria": expected_funnel_criteria,
        "score_calculation": rules.get("score_calculation", {}),
        "status_thresholds": rules.get("status_thresholds", {}),
        "funnel_alignment": rules.get("funnel_alignment", {}),
    }

from __future__ import annotations

from pathlib import Path

from contentcreajudge.judges.brief.exceptions import (
    MissingBriefCriterionError,
    MissingBriefRulesError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config

_REQUIRED_CRITERIA = [
    "angle_alignment",
    "axis_development",
    "intended_understanding",
    "scope_adherence",
]


def resolve_brief_rules() -> dict[str, object]:
    """Resolve the Brief Judge rules defined in the YAML configuration."""
    config_path = Path(__file__).with_name("brief.yaml")

    config = load_yaml_config(config_path)

    rules = config.get("brief_rules") or {}

    if not isinstance(rules, dict):
        raise MissingBriefRulesError

    criteria = rules.get("criteria") or {}

    if not isinstance(criteria, dict):
        criteria = {}

    for criterion_id in _REQUIRED_CRITERIA:
        if criterion_id not in criteria:
            raise MissingBriefCriterionError(criterion_id)

    return {
        "judge_id": rules.get("judge_id", "brief"),
        "version": rules.get("version", 1),
        "label": rules.get("label", "Brief alignment judge"),
        "description": rules.get(
            "description",
            "Evaluate whether the content respects the editorial brief.",
        ),
        "score_thresholds": rules.get(
            "score_thresholds",
            {
                "pass": 80,
                "warn": 60,
                "fail": 0,
            },
        ),
        "criteria": criteria,
        "aggregation": rules.get("aggregation", {}),
        "llm_output": rules.get("llm_output", {}),
        "messages": rules.get("messages", {}),
    }

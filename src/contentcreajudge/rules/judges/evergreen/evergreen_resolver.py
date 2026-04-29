from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from yaml import YAMLError


def resolve_evergreen_rules(context: dict[str, Any]) -> dict[str, Any]:
    """Resolve evergreen rules safely with fallbacks (no crash)."""
    config_path = Path(__file__).with_name("evergreen.yaml")

    try:
        with config_path.open(encoding="utf-8") as file:
            config = yaml.safe_load(file) or {}
    except OSError, RuntimeError, YAMLError:
        config = {}

    rules = config.get("evergreen_rules", {})

    evergreen_value = bool(context.get("evergreen", False))
    locale = str(context.get("locale", "fr-FR"))

    allowed_dates = context.get("allowed_dates") or []
    allowed_temporal_references = context.get("allowed_temporal_references") or []
    brief = str(context.get("brief", ""))

    return {
        "judge_id": config.get("judge_id", "evergreen"),
        "version": config.get("version", 1),
        "label": config.get("label", "Evergreen judge"),
        "description": config.get(
            "description",
            "Evaluate temporal references and evergreen compliance.",
        ),
        "evergreen_required": evergreen_value,
        "locale": locale,
        "allowed_dates": allowed_dates,
        "allowed_temporal_references": allowed_temporal_references,
        "brief": brief,
        "activation": rules.get("activation", {}),
        "forbidden_temporal_references": rules.get("forbidden_temporal_references", {}),
        "temporal_expression_categories": rules.get(
            "temporal_expression_categories",
            {},
        ),
        "context_detection": rules.get("context_detection", {}),
        "exceptions": rules.get("exceptions", {}),
        "post_creation_checks": rules.get("post_creation_checks", {}),
        "rules": rules.get("rules", []),
        "messages": rules.get("messages", {}),
    }

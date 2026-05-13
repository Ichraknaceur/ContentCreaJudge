"""Resolve the structure judge rules from YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from contentcreajudge.rules.shared.config_loader import load_yaml_config


def resolve_structure_rules(context: dict[str, object]) -> dict[str, Any]:
    """Resolve structure rules from YAML for the current evaluation context."""
    config_path = Path(__file__).with_name("structure.yaml")

    config = load_yaml_config(config_path)

    expected_outline_html = context.get("expected_outline_html")
    locale = context.get("locale")

    if not expected_outline_html:
        raise ValueError(
            "Missing context.expected_outline_html for structure evaluation.",
        )

    return {
        "judge_id": config.get("judge_id", "structure"),
        "version": config.get("version", 1),
        "label": config.get("label", "Structure judge"),
        "description": config.get(
            "description",
            "Evaluate content structure compliance.",
        ),
        "structure_rules": config.get("structure_rules", {}),
        "rules": config.get("rules", []),
        "messages": config.get("messages", {}),
        "expected_outline_html": str(expected_outline_html),
        "locale": str(locale) if locale is not None else None,
    }

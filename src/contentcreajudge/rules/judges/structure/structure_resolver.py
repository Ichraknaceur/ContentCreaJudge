"""Resolve the structure judge rules from YAML configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def resolve_structure_rules(context: dict[str, object]) -> dict[str, Any]:
    """Resolve the structure rules defined in YAML for the current evaluation context."""
    config_path = Path(__file__).with_name("structure.yaml")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    expected_outline_html = context.get("expected_outline_html")
    locale = context.get("locale")

    if not expected_outline_html:
        raise ValueError(
            "Missing context.expected_outline_html for structure evaluation."
        )

    return {
        "judge_id": config["judge_id"],
        "version": config["version"],
        "label": config["label"],
        "description": config["description"],
        "structure_rules": config["structure_rules"],
        "rules": config["rules"],
        "messages": config["messages"],
        "expected_outline_html": str(expected_outline_html),
        "locale": str(locale) if locale is not None else None,
    }
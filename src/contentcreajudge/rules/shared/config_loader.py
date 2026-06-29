"""Shared helpers for loading rule configuration files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


def load_yaml_config(config_path: Path) -> dict[str, Any]:
    """Load a YAML configuration file as a dictionary."""
    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}

    if not isinstance(config, dict):
        return {}

    return config

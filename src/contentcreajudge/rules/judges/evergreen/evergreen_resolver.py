from __future__ import annotations

from pathlib import Path
from typing import Any

from contentcreajudge.judges.evergreen.exceptions import (
    MissingEvergreenContextError,
    UnsupportedEvergreenValueError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config

SUPPORTED_LOCALES = ["fr-FR", "en-US"]


def _as_dict(value: object) -> dict[str, Any]:
    """Return value as dict or an empty fallback."""
    return value if isinstance(value, dict) else {}


def resolve_evergreen_rules(context: dict[str, Any]) -> dict[str, Any]:
    """Resolve evergreen rules with typed context validation."""
    config_path = Path(__file__).with_name("evergreen.yaml")
    config = load_yaml_config(config_path)

    rules = config.get("evergreen_rules") or {}

    evergreen_value = context.get("evergreen")
    locale = context.get("locale")

    if evergreen_value is None:
        raise MissingEvergreenContextError("evergreen")

    if not locale:
        raise MissingEvergreenContextError("locale")

    locale_value = str(locale)
    if locale_value not in SUPPORTED_LOCALES:
        raise UnsupportedEvergreenValueError(
            "locale",
            locale_value,
            SUPPORTED_LOCALES,
        )

    llm_config = _as_dict(rules.get("llm"))
    scoring = _as_dict(rules.get("scoring"))
    llm_messages = _as_dict(rules.get("llm_messages"))

    allowed_dates = context.get("allowed_dates") or []
    allowed_temporal_references = context.get("allowed_temporal_references") or []

    return {
        "judge_id": config.get("judge_id", "evergreen"),
        "version": config.get("version", 1),
        "label": config.get("label", "Evergreen judge"),
        "description": config.get(
            "description",
            "Evaluate temporal references and evergreen compliance.",
        ),
        "mode": str(rules.get("mode", "llm")),
        "is_blocking_rule": bool(rules.get("is_blocking_rule", False)),
        "evergreen_required": bool(evergreen_value),
        "locale": locale_value,
        "allowed_dates": allowed_dates,
        "allowed_temporal_references": allowed_temporal_references,
        "llm": {
            "provider": str(llm_config.get("provider", "openai")),
            "model_env_var": str(
                llm_config.get("model_env_var", "OPENAI_EVERGREEN_MODEL"),
            ),
            "default_model": str(llm_config.get("default_model", "gpt-4.1-mini")),
            "temperature": float(llm_config.get("temperature", 0.0)),
            "max_tokens": int(llm_config.get("max_tokens", 2000)),
        },
        "scoring": {
            "pass_min_score": int(scoring.get("pass_min_score", 70)),
            "warn_min_score": int(scoring.get("warn_min_score", 50)),
        },
        "prompt_template": str(rules.get("prompt_template", "")),
        "llm_messages": {
            "pass": str(
                llm_messages.get(
                    "pass",
                    "The content demonstrates strong evergreen characteristics.",
                ),
            ),
            "warn": str(
                llm_messages.get(
                    "warn",
                    "The content contains some time-sensitive elements.",
                ),
            ),
            "fail": str(
                llm_messages.get(
                    "fail",
                    "The content has low evergreen value.",
                ),
            ),
            "llm_error": str(
                llm_messages.get(
                    "llm_error",
                    "The evergreen evaluation could not be completed reliably.",
                ),
            ),
        },
        "activation": _as_dict(rules.get("activation")),
        "temporal_expression_categories": _as_dict(
            rules.get("temporal_expression_categories"),
        ),
        "context_detection": _as_dict(rules.get("context_detection")),
    }

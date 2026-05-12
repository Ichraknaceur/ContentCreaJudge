from __future__ import annotations

from pathlib import Path

from contentcreajudge.judges.typography.exceptions import (
    MissingTypographyContextError,
    UnsupportedTypographyLocaleError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config


def resolve_typography_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve typography rules from YAML using the evaluation context."""
    config_path = Path(__file__).with_name("typography.yaml")

    config = load_yaml_config(config_path)

    judge_id = config["judge_id"]
    version = config["version"]
    rules_config = config["typography_rules"]

    locale = context.get("locale")

    if not locale:
        raise MissingTypographyContextError("locale")

    locale_support = rules_config.get("locale_support", {})
    supported_locales = locale_support.get("supported_locales", [])

    if locale not in supported_locales:
        raise UnsupportedTypographyLocaleError(
            str(locale),
            [str(item) for item in supported_locales],
        )

    return {
        "judge_id": judge_id,
        "version": version,
        "locale": locale,
        "enforce_typography_rules": rules_config["enforce_typography_rules"],
        "spacing": rules_config["spacing"],
        "punctuation": rules_config["punctuation"],
        "capitalization": rules_config["capitalization"],
        "cleanliness": rules_config["cleanliness"],
        "html_cleanliness": rules_config["html_cleanliness"],
        "rules": rules_config["rules"],
        "messages": rules_config["messages"],
    }

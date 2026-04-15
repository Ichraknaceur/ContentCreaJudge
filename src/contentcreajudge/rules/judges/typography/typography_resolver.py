from __future__ import annotations

from pathlib import Path

import yaml


def resolve_typography_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the typography rules defined in the YAML based on the evaluation context."""

    config_path = Path(__file__).with_name("typography.yaml")

    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    judge_id = config["judge_id"]
    version = config["version"]
    rules_config = config["typography_rules"]

    locale = context.get("locale")

    if not locale:
        raise ValueError("Missing context.locale for typography evaluation.")

    locale_support = rules_config.get("locale_support", {})
    supported_locales = locale_support.get("supported_locales", [])

    if locale not in supported_locales:
        raise ValueError(f"Unsupported locale for typography evaluation: {locale}")

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
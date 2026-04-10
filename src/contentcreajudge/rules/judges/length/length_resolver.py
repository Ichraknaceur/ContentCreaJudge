from __future__ import annotations

from pathlib import Path

import yaml


def resolve_length_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the length rules defined in the YAML based on the evaluation context"""

    config_path = Path(__file__).with_name("length.yaml")

    # Lecture du YAML
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    rules = config["length_rules"]
    
    # Lecture des infos envoyées par l'UI
    content_type = context.get("content_type")
    expected_length = context.get("expected_length")

    if not content_type:
        raise ValueError("Missing context.content_type for length evaluation.")

    if not expected_length:
        raise ValueError("Missing context.expected_length for length evaluation.")

   
    ranges = rules["ranges_by_content_type"]

    if content_type not in ranges:
        raise ValueError(f"Unknown content_type: {content_type}")

    if expected_length not in ranges[content_type]:
        raise ValueError(f"Unknown expected_length: {expected_length}")

    selected_range = ranges[content_type][expected_length]

    # Envoi de la règle définie pour ce contexte d'évaluation
    return {
        "judge_id": "length",
        "is_blocking_rule": rules["is_blocking_rule"],
        "measurement_unit": rules["measurement_unit"],
        "count_scope": rules["count_scope"],
        "exclude_html_tags": rules["exclude_html_tags"],
        "tolerance_pct": rules["tolerance_pct"],
        "min_words": selected_range["min_words"],
        "max_words": selected_range["max_words"],
        "content_type": content_type,
        "expected_length": expected_length,
    }

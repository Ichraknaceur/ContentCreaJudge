from __future__ import annotations

from pathlib import Path

from contentcreajudge.judges.length.exceptions import (
    MissingLengthContextError,
    UnsupportedLengthValueError,
)
from contentcreajudge.rules.shared.config_loader import load_yaml_config


def resolve_length_rules(context: dict[str, object]) -> dict[str, object]:
    """Resolve the length rules defined in the YAML based on the evaluation context."""
    config_path = Path(__file__).with_name("length.yaml")

    config = load_yaml_config(config_path)

    rules = config.get("length_rules") or {}

    content_type = context.get("content_type")
    expected_length = context.get("expected_length")

    if not content_type:
        raise MissingLengthContextError("content_type")

    if not expected_length:
        raise MissingLengthContextError("expected_length")

    ranges_by_content_type = rules.get("ranges_by_content_type") or {}

    if content_type not in ranges_by_content_type:
        raise UnsupportedLengthValueError(
            "content_type",
            str(content_type),
            list(ranges_by_content_type.keys()),
        )

    ranges_for_content_type = ranges_by_content_type.get(content_type) or {}

    if expected_length not in ranges_for_content_type:
        raise UnsupportedLengthValueError(
            "expected_length",
            str(expected_length),
            list(ranges_for_content_type.keys()),
        )

    selected_range = ranges_for_content_type.get(expected_length) or {}

    return {
        "judge_id": config.get("judge_id", "length"),
        "version": config.get("version", 1),
        "label": config.get("label", "Length judge"),
        "description": config.get(
            "description",
            "Evaluate content length compliance.",
        ),
        "is_blocking_rule": rules.get("is_blocking_rule", True),
        "measurement_unit": rules.get("measurement_unit", "words"),
        "count_scope": rules.get("count_scope", "body_text_only"),
        "exclude_html_tags": rules.get("exclude_html_tags", True),
        "tolerance_pct": rules.get("tolerance_pct", 10),
        "min_words": selected_range.get("min_words", 0),
        "max_words": selected_range.get("max_words"),
        "content_type": content_type,
        "expected_length": expected_length,
        "messages": config.get("messages", {}),
    }

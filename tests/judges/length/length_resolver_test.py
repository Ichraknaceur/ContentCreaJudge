from __future__ import annotations

import pytest

from contentcreajudge.judges.length.exceptions import (
    MissingLengthContextError,
    UnsupportedLengthValueError,
)
from contentcreajudge.rules.judges.length.length_resolver import resolve_length_rules

BASE_CONFIG = {
    "judge_id": "length",
    "version": 1,
    "label": "Length judge",
    "description": "Evaluate content length compliance.",
    "length_rules": {
        "is_blocking_rule": True,
        "measurement_unit": "words",
        "count_scope": "body_text_only",
        "exclude_html_tags": True,
        "tolerance_pct": 10,
        "ranges_by_content_type": {
            "articles": {
                "SIMPLE": {"min_words": 800, "max_words": 1000},
                "MEDIUM": {"min_words": 1000, "max_words": 1999},
                "LONG": {"min_words": 2000, "max_words": 3000},
            },
            "quiz": {
                "SIMPLE": {"min_words": 0, "max_words": 999},
                "MEDIUM": {"min_words": 1000, "max_words": 1500},
                "LONG": {"min_words": 1501, "max_words": None},
            },
        },
    },
}


def _mock_yaml(
    monkeypatch: pytest.MonkeyPatch,
    config: dict[str, object] | None,
) -> None:
    monkeypatch.setattr(
        "contentcreajudge.rules.judges.length.length_resolver.load_yaml_config",
        lambda config_path: config or {},
    )


def test_resolve_length_rules_returns_selected_article_medium_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the selected article medium length rules."""
    _mock_yaml(monkeypatch, BASE_CONFIG)

    result = resolve_length_rules(
        {
            "content_type": "articles",
            "expected_length": "MEDIUM",
        },
    )

    assert result == {
        "judge_id": "length",
        "version": 1,
        "label": "Length judge",
        "description": "Evaluate content length compliance.",
        "is_blocking_rule": True,
        "measurement_unit": "words",
        "count_scope": "body_text_only",
        "exclude_html_tags": True,
        "tolerance_pct": 10,
        "min_words": 1000,
        "max_words": 1999,
        "content_type": "articles",
        "expected_length": "MEDIUM",
        "messages": {},
    }


def test_resolve_length_rules_uses_default_metadata_and_rule_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use default metadata and rule values when config keys are missing."""
    minimal_config = {
        "length_rules": {
            "ranges_by_content_type": {
                "articles": {
                    "SIMPLE": {
                        "min_words": 800,
                    },
                },
            },
        },
    }
    _mock_yaml(monkeypatch, minimal_config)

    result = resolve_length_rules(
        {
            "content_type": "articles",
            "expected_length": "SIMPLE",
        },
    )

    assert result["judge_id"] == "length"
    assert result["version"] == 1
    assert result["label"] == "Length judge"
    assert result["description"] == "Evaluate content length compliance."
    assert result["is_blocking_rule"] is True
    assert result["measurement_unit"] == "words"
    assert result["count_scope"] == "body_text_only"
    assert result["exclude_html_tags"] is True
    assert result["tolerance_pct"] == 10
    assert result["min_words"] == 800
    assert result["max_words"] is None


def test_resolve_length_rules_raises_when_content_type_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise when the content type is missing from context."""
    _mock_yaml(monkeypatch, BASE_CONFIG)

    with pytest.raises(
        MissingLengthContextError,
        match="Missing length context field: content_type",
    ):
        resolve_length_rules({"expected_length": "MEDIUM"})


def test_resolve_length_rules_raises_when_expected_length_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise when the expected length is missing from context."""
    _mock_yaml(monkeypatch, BASE_CONFIG)

    with pytest.raises(
        MissingLengthContextError,
        match="Missing length context field: expected_length",
    ):
        resolve_length_rules({"content_type": "articles"})


def test_resolve_length_rules_raises_when_content_type_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise when the content type is not configured."""
    _mock_yaml(monkeypatch, BASE_CONFIG)

    with pytest.raises(
        UnsupportedLengthValueError,
        match="Unsupported value for content_type: unknown",
    ):
        resolve_length_rules(
            {
                "content_type": "unknown",
                "expected_length": "MEDIUM",
            },
        )


def test_resolve_length_rules_raises_when_expected_length_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Raise when the expected length is not configured."""
    _mock_yaml(monkeypatch, BASE_CONFIG)

    with pytest.raises(
        UnsupportedLengthValueError,
        match="Unsupported value for expected_length: XXL",
    ):
        resolve_length_rules(
            {
                "content_type": "articles",
                "expected_length": "XXL",
            },
        )


def test_resolve_length_rules_handles_empty_yaml_as_empty_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Treat an empty YAML config as an empty dictionary."""
    _mock_yaml(monkeypatch, None)

    with pytest.raises(
        UnsupportedLengthValueError,
        match="Unsupported value for content_type: articles",
    ):
        resolve_length_rules(
            {
                "content_type": "articles",
                "expected_length": "MEDIUM",
            },
        )

from __future__ import annotations

import pytest

from contentcreajudge.rules.judges.sources.sources_resolver import (
    resolve_sources_rules,
)


def test_resolve_sources_rules_for_article_medium() -> None:
    context = {
        "content_type": "articles",
        "expected_length": "MEDIUM",
        "locale": "fr-FR",
        "require_sources": True,
    }

    rules = resolve_sources_rules(context)

    assert rules["judge_id"] == "sources"
    assert rules["content_type"] == "articles"
    assert rules["expected_length"] == "MEDIUM"
    assert rules["locale"] == "fr-FR"
    assert rules["require_sources"] is True
    assert rules["is_content_type_allowed"] is True
    assert rules["is_content_type_forbidden"] is False
    assert "html_link_format" in rules
    assert "url_cleaning" in rules
    assert "network_validation" in rules
    assert "messages" in rules


def test_resolve_sources_rules_raises_error_without_content_type() -> None:
    context = {
        "expected_length": "MEDIUM",
    }

    with pytest.raises(ValueError, match="Missing context.content_type"):
        resolve_sources_rules(context)


def test_resolve_sources_rules_raises_error_without_expected_length() -> None:
    context = {
        "content_type": "articles",
    }

    with pytest.raises(ValueError, match="Missing context.expected_length"):
        resolve_sources_rules(context)


def test_resolve_sources_rules_raises_error_for_unknown_content_type() -> None:
    context = {
        "content_type": "unknownContentType",
        "expected_length": "MEDIUM",
    }

    with pytest.raises(
        ValueError,
        match="Unknown content_type for sources evaluation: unknownContentType",
    ):
        resolve_sources_rules(context)


def test_resolve_sources_rules_raises_error_for_unknown_expected_length() -> None:
    context = {
        "content_type": "articles",
        "expected_length": "UNKNOWN",
    }

    with pytest.raises(
        ValueError,
        match="Unknown expected_length for sources evaluation: UNKNOWN",
    ):
        resolve_sources_rules(context)


def test_resolve_sources_rules_detects_forbidden_content_type() -> None:
    context = {
        "content_type": "quiz",
        "expected_length": "SIMPLE",
    }

    rules = resolve_sources_rules(context)

    assert rules["is_content_type_forbidden"] is True
    assert rules["is_content_type_allowed"] is False

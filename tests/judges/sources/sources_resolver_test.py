from __future__ import annotations

import pytest

from contentcreajudge.judges.sources.exceptions import (
    MissingSourcesContextError,
    UnsupportedSourcesValueError,
)
from contentcreajudge.rules.judges.sources.sources_resolver import (
    resolve_sources_rules,
)


def test_resolve_sources_rules_for_article_medium() -> None:
    """Verify that resolve sources rules for article medium."""
    context = {
        "content_type": "articles",
        "expected_length": "MEDIUM",
        "locale": "fr-FR",
        "require_sources": True,
        "organization_website": "https://contentcrea.com",
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
    """Verify that resolve sources rules raises error without content type."""
    context = {
        "expected_length": "MEDIUM",
    }

    with pytest.raises(
        MissingSourcesContextError,
        match=r"Missing sources context field: content_type",
    ):
        resolve_sources_rules(context)


def test_resolve_sources_rules_raises_error_without_expected_length() -> None:
    """Verify that resolve sources rules raises error without expected length."""
    context = {
        "content_type": "articles",
        "organization_website": "https://contentcrea.com",
    }

    with pytest.raises(
        MissingSourcesContextError,
        match=r"Missing sources context field: expected_length",
    ):
        resolve_sources_rules(context)


def test_resolve_sources_rules_raises_error_for_unknown_content_type() -> None:
    """Verify that resolve sources rules raises error for unknown content type."""
    context = {
        "content_type": "unknownContentType",
        "expected_length": "MEDIUM",
        "organization_website": "https://contentcrea.com",
    }

    with pytest.raises(
        UnsupportedSourcesValueError,
        match="Unsupported value for content_type: unknownContentType",
    ):
        resolve_sources_rules(context)


def test_resolve_sources_rules_raises_error_for_unknown_expected_length() -> None:
    """Verify that resolve sources rules raises error for unknown expected length."""
    context = {
        "content_type": "articles",
        "expected_length": "UNKNOWN",
        "organization_website": "https://contentcrea.com",
    }

    with pytest.raises(
        UnsupportedSourcesValueError,
        match="Unsupported value for expected_length: UNKNOWN",
    ):
        resolve_sources_rules(context)


def test_resolve_sources_rules_detects_forbidden_content_type() -> None:
    """Verify that resolve sources rules detects forbidden content type."""
    context = {
        "content_type": "quiz",
        "expected_length": "SIMPLE",
        "organization_website": "https://contentcrea.com",
    }

    rules = resolve_sources_rules(context)

    assert rules["is_content_type_forbidden"] is True
    assert rules["is_content_type_allowed"] is False

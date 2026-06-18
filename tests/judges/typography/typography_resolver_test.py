import pytest

from contentcreajudge.judges.typography.exceptions import (
    MissingTypographyContextError,
    UnsupportedTypographyLocaleError,
)
from contentcreajudge.rules.judges.typography.typography_resolver import (
    resolve_typography_rules,
)


def test_resolve_typography_rules_success() -> None:
    """The resolver should return the configured typography rule payload."""
    context = {
        "locale": "fr-FR",
    }

    resolved = resolve_typography_rules(context)

    assert resolved["judge_id"] == "typography"
    assert resolved["version"] == 1
    assert resolved["locale"] == "fr-FR"
    assert "spacing" in resolved
    assert "punctuation" in resolved
    assert "capitalization" in resolved
    assert "cleanliness" in resolved
    assert "html_cleanliness" in resolved
    assert "rules" in resolved
    assert "messages" in resolved


def test_resolve_typography_rules_missing_locale() -> None:
    """The resolver should reject missing locale context with a typed error."""
    context = {}

    with pytest.raises(MissingTypographyContextError) as exc_info:
        resolve_typography_rules(context)

    exc = exc_info.value
    assert str(exc) == "Missing typography context field: locale"
    assert exc.details == {"field_name": "locale"}


def test_resolve_typography_rules_unsupported_locale() -> None:
    """The resolver should reject unsupported locales with a typed error."""
    context = {
        "locale": "en-US",
    }

    with pytest.raises(UnsupportedTypographyLocaleError) as exc_info:
        resolve_typography_rules(context)

    exc = exc_info.value
    assert str(exc) == "Unsupported locale for typography evaluation: en-US"
    assert exc.details == {
        "locale": "en-US",
        "supported_locales": ["fr-FR"],
    }

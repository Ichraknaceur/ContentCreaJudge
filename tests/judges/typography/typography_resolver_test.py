import pytest

from contentcreajudge.rules.judges.typography.typography_resolver import (
    resolve_typography_rules,
)


def test_resolve_typography_rules_success() -> None:
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
    context = {}

    with pytest.raises(
        ValueError,
        match=r"Missing context\.locale for typography evaluation\.",
    ) as exc_info:
        resolve_typography_rules(context)

    assert str(exc_info.value) == "Missing context.locale for typography evaluation."


def test_resolve_typography_rules_unsupported_locale() -> None:
    context = {
        "locale": "en-US",
    }

    with pytest.raises(
        ValueError,
        match="Unsupported locale for typography evaluation: en-US",
    ) as exc_info:
        resolve_typography_rules(context)

    assert str(exc_info.value) == "Unsupported locale for typography evaluation: en-US"

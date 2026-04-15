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

    try:
        resolve_typography_rules(context)
        assert False, "Expected ValueError was not raised"
    except ValueError as exc:
        assert str(exc) == (
            "Missing context.locale for typography evaluation."
        )


def test_resolve_typography_rules_unsupported_locale() -> None:
    context = {
        "locale": "en-US",
    }

    try:
        resolve_typography_rules(context)
        assert False, "Expected ValueError was not raised"
    except ValueError as exc:
        assert str(exc) == (
            "Unsupported locale for typography evaluation: en-US"
        )
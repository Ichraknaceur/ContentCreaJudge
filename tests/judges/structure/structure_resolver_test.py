from contentcreajudge.rules.judges.structure.structure_resolver import (
    resolve_structure_rules,
)


def test_resolve_structure_rules_success() -> None:
    context = {
        "expected_outline_html": "<p>Intro</p><h2>Section 1</h2>",
        "locale": "fr-FR",
    }

    resolved = resolve_structure_rules(context)

    assert resolved["judge_id"] == "structure"
    assert resolved["version"] == 1
    assert resolved["locale"] == "fr-FR"
    assert "structure_rules" in resolved
    assert "rules" in resolved
    assert "messages" in resolved


def test_resolve_structure_rules_missing_expected_outline_html() -> None:
    context = {
        "locale": "fr-FR",
    }

    try:
        resolve_structure_rules(context)
        assert False, "Expected ValueError was not raised"
    except ValueError as exc:
        assert str(exc) == (
            "Missing context.expected_outline_html for structure evaluation."
        )
import pytest

from contentcreajudge.rules.judges.structure.structure_resolver import (
    resolve_structure_rules,
)


def test_resolve_structure_rules_success() -> None:
    """Resolve structure rules with expected outline context."""
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
    """Raise an error when the expected outline is missing."""
    context = {
        "locale": "fr-FR",
    }

    with pytest.raises(
        ValueError,
        match=r"Missing context\.expected_outline_html for structure evaluation\.",
    ):
        resolve_structure_rules(context)

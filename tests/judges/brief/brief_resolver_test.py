from contentcreajudge.rules.judges.brief.brief_resolver import (
    resolve_brief_rules,
)


def test_resolve_brief_rules_returns_brief_judge_id() -> None:
    rules = resolve_brief_rules()

    assert rules["judge_id"] == "brief"


def test_resolve_brief_rules_contains_required_criteria() -> None:
    rules = resolve_brief_rules()
    criteria = rules["criteria"]

    assert "angle_alignment" in criteria
    assert "axis_development" in criteria
    assert "intended_understanding" in criteria
    assert "scope_adherence" in criteria


def test_resolve_brief_rules_contains_optional_specific_element() -> None:
    rules = resolve_brief_rules()
    criteria = rules["criteria"]

    assert "specific_element_integration" in criteria
    assert criteria["specific_element_integration"]["required"] is False


def test_resolve_brief_rules_contains_thresholds() -> None:
    rules = resolve_brief_rules()
    thresholds = rules["score_thresholds"]

    assert thresholds["pass"] == 80
    assert thresholds["warn"] == 60

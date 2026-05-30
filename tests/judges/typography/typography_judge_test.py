from contentcreajudge.judges.typography.typography_judge import (
    find_attached_links,
    find_double_spaces,
    find_french_nbsp_issues,
    find_multiple_punctuation,
    find_repeated_line_breaks,
    find_space_before_comma,
    find_space_before_dot,
    find_trailing_spaces,
    run_typography_judge,
)
from contentcreajudge.preprocessing.typography_preprocessor import (
    preprocess_typography_content,
)
from contentcreajudge.rules.judges.typography.typography_resolver import (
    resolve_typography_rules,
)


def test_find_double_spaces() -> None:
    """Should detect consecutive spaces in text."""
    text = "Bonjour  le monde"
    result = find_double_spaces(text)
    assert result == ["  "]


def test_find_trailing_spaces() -> None:
    """Should detect lines ending with whitespace."""
    lines = ["Bonjour   ", "Ligne propre", "Encore\t"]
    result = find_trailing_spaces(lines)
    assert result == ["Bonjour   ", "Encore\t"]


def test_find_multiple_punctuation() -> None:
    """Should detect repeated punctuation marks."""
    text = "Incroyable !! Vraiment???"
    result = find_multiple_punctuation(text)
    assert "!!" in result
    assert "???" in result


def test_find_space_before_dot() -> None:
    """Should detect a space before a period."""
    text = "Bonjour . Fin."
    result = find_space_before_dot(text)
    assert result == [" ."]


def test_find_space_before_comma() -> None:
    """Should detect a space before a comma."""
    text = "Bonjour , comment ça va ?"
    result = find_space_before_comma(text)
    assert result == [" ,"]


def test_find_french_nbsp_issues_detects_missing_nbsp() -> None:
    """Should flag missing non-breaking spaces before French double punctuation."""
    text = "Bonjour! Prix: 50%"
    result = find_french_nbsp_issues(text)
    assert "!" in result
    assert ":" in result
    assert "%" in result


def test_find_french_nbsp_issues_passes_with_nbsp() -> None:
    """Should not flag text that uses correct non-breaking spaces."""
    text = "Bonjour\u00a0! Prix\u00a0: 50\u00a0%"
    result = find_french_nbsp_issues(text)
    assert result == []


def test_find_attached_links() -> None:
    """Should detect anchor tags immediately preceded by a word character."""
    content = 'objectifs<a href="https://example.com">Source</a>'
    result = find_attached_links(content)
    assert result == ["s<a"]


def test_find_repeated_line_breaks() -> None:
    """Should detect consecutive br tags in content."""
    content = "<p>Test</p><br><br><p>Suite</p>"
    result = find_repeated_line_breaks(content)
    assert len(result) == 1


def test_find_attached_links_ignores_links_inside_list_items() -> None:
    """Should not flag anchor tags that are the first child of a list item."""
    content = '<ul><li><a href="https://example.com">Source</a></li></ul>'
    result = find_attached_links(content)
    assert result == []


def test_run_typography_judge_pass() -> None:
    """The judge should return a passing result for clean content."""
    content = "<p>Bonjour\u00a0!</p><p>Texte propre.</p>"
    preprocessed = preprocess_typography_content(content)
    rules = resolve_typography_rules({"locale": "fr-FR"})

    result = run_typography_judge(preprocessed, rules)

    assert result["dimension"] == "typography"
    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["findings"][0]["rule_id"] == "typography.valid"


def test_run_typography_judge_warn_with_minor_issues() -> None:
    """The judge should return a warning for content with minor typography issues."""
    content = "<p>Bonjour  le monde .</p>"
    preprocessed = preprocess_typography_content(content)
    rules = resolve_typography_rules({"locale": "fr-FR"})

    result = run_typography_judge(preprocessed, rules)

    assert result["dimension"] == "typography"
    assert result["status"] == "warn"
    assert result["score"] < 100
    assert any(
        finding["rule_id"] == "typography.double_spaces"
        for finding in result["findings"]
    )
    assert any(
        finding["rule_id"] == "typography.space_before_dot"
        for finding in result["findings"]
    )


def test_run_typography_judge_fail_with_major_issue() -> None:
    """The judge should return a failing result for content with major issues."""
    content = "<p>Bonjour!</p>"
    preprocessed = preprocess_typography_content(content)
    rules = resolve_typography_rules({"locale": "fr-FR"})

    result = run_typography_judge(preprocessed, rules)

    assert result["dimension"] == "typography"
    assert result["status"] == "fail"
    assert result["score"] < 100
    assert any(
        finding["rule_id"] == "typography.french_nbsp_before_double_punctuation"
        for finding in result["findings"]
    )


def test_run_typography_judge_detects_attached_link() -> None:
    """The judge should flag an anchor tag immediately preceded by a word character."""
    content = '<p>objectifs<a href="https://example.com">Source</a></p>'
    preprocessed = preprocess_typography_content(content)
    rules = resolve_typography_rules({"locale": "fr-FR"})

    result = run_typography_judge(preprocessed, rules)

    assert any(
        finding["rule_id"] == "typography.attached_links"
        for finding in result["findings"]
    )


def test_run_typography_judge_detects_repeated_breaks() -> None:
    """The judge should flag consecutive br tags in content."""
    content = "<p>Test</p><br><br><p>Suite</p>"
    preprocessed = preprocess_typography_content(content)
    rules = resolve_typography_rules({"locale": "fr-FR"})

    result = run_typography_judge(preprocessed, rules)

    assert any(
        finding["rule_id"] == "typography.repeated_line_breaks"
        for finding in result["findings"]
    )

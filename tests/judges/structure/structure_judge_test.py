from contentcreajudge.judges.structure.structure_judge import run_structure_judge
from contentcreajudge.preprocessing.structure_preprocessor import (
    preprocess_structure_content,
)
from contentcreajudge.rules.judges.structure.structure_resolver import (
    resolve_structure_rules,
)


def _build_rules(expected_outline_html: str) -> dict[str, object]:
    return resolve_structure_rules(
        {
            "expected_outline_html": expected_outline_html,
            "locale": "fr-FR",
        },
    )


def _preprocess(
    expected_outline_html: str,
    generated_html: str,
    rules: dict[str, object],
) -> dict[str, object]:
    structure_rules = rules["structure_rules"]
    return preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=structure_rules["internal_outline_comments"][
            "patterns"
        ],
    )


def test_run_structure_judge_passes_when_structure_is_valid() -> None:
    """Pass when generated headings match the expected structure."""
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <p>Text</p>
    <h3>Sous-section A.1</h3>
    <p>Text</p>
    <h2>Conclusion</h2>
    <p>Text</p>
    """

    generated_html = """
    <p>Intro generee</p>
    <h2>Section A</h2>
    <p>Contenu</p>
    <h3>Sous-section A.1</h3>
    <p>Contenu</p>
    <h2>Conclusion</h2>
    <p>Contenu final</p>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = _preprocess(expected_outline_html, generated_html, rules)

    result = run_structure_judge(preprocessed, rules)

    assert result["dimension"] == "structure"
    assert result["status"] == "pass"
    assert result["score"] == 100


def test_run_structure_judge_detects_heading_order_issue() -> None:
    """Fail when generated headings are reordered."""
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <h3>Sous-section A.1</h3>
    <h3>Sous-section A.2</h3>
    """

    generated_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <h3>Sous-section A.2</h3>
    <h3>Sous-section A.1</h3>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = _preprocess(expected_outline_html, generated_html, rules)

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "structure.heading_order"
        for finding in result["findings"]
    )


def test_run_structure_judge_detects_heading_level_issue() -> None:
    """Fail when generated heading levels differ."""
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <h3>Sous-section A.1</h3>
    """

    generated_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <h2>Sous-section A.1</h2>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = _preprocess(expected_outline_html, generated_html, rules)

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "structure.heading_levels"
        for finding in result["findings"]
    )


def test_run_structure_judge_detects_h1_script_span_and_inline_style() -> None:
    """Fail when forbidden body markup is present."""
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    """

    generated_html = """
    <h1>Titre interdit</h1>
    <p style="color:red;">Intro</p>
    <h2>Section A</h2>
    <span>Decoration</span>
    <script>alert('x')</script>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = _preprocess(expected_outline_html, generated_html, rules)

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    rule_ids = {finding["rule_id"] for finding in result["findings"]}

    assert "structure.no_h1_in_body" in rule_ids
    assert "structure.no_scripts" in rule_ids
    assert "structure.no_decorative_spans" in rule_ids
    assert "structure.no_inline_styles_except_tables" in rule_ids


def test_run_structure_judge_detects_internal_comment_exposure() -> None:
    """Fail when internal outline comments are exposed."""
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    """

    generated_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <p>Instruction : ce texte ne doit pas apparaitre.</p>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = _preprocess(expected_outline_html, generated_html, rules)

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "structure.no_internal_outline_comments_exposed"
        for finding in result["findings"]
    )


def test_run_structure_judge_allows_optional_trailing_complementary_reading() -> None:
    """Allow one configured optional trailing section."""
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <h3>Sous-section A.1</h3>
    <h2>Conclusion</h2>
    <p><strong>CTA :</strong> Read more</p>
    """

    generated_html = """
    <p>Intro generee</p>
    <h2>Section A</h2>
    <p>Contenu</p>
    <h3>Sous-section A.1</h3>
    <p>Contenu</p>
    <h2>Conclusion</h2>
    <p>Contenu final</p>
    <h2>Lecture complémentaire</h2>
    <ul>
      <li><a href="https://example.com">Resource</a></li>
    </ul>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = _preprocess(expected_outline_html, generated_html, rules)

    result = run_structure_judge(preprocessed, rules)

    rule_ids = {finding["rule_id"] for finding in result["findings"]}

    assert "structure.heading_order" not in rule_ids
    assert "structure.heading_levels" not in rule_ids
    assert "structure.heading_text" not in rule_ids
    assert "structure.no_added_sections" not in rule_ids

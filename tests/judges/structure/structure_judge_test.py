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
        }
    )

# QStructure Validation
def test_run_structure_judge_passes_when_structure_is_valid() -> None:
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
    <p>Intro générée</p>
    <h2>Section A</h2>
    <p>Contenu</p>
    <h3>Sous-section A.1</h3>
    <p>Contenu</p>
    <h2>Conclusion</h2>
    <p>Contenu final</p>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=rules["structure_rules"]["internal_outline_comments"]["patterns"],
    )

    result = run_structure_judge(preprocessed, rules)

    assert result["dimension"] == "structure"
    assert result["status"] == "pass"
    assert result["score"] == 100

# Heading Order 
def test_run_structure_judge_detects_heading_order_issue() -> None:
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
    preprocessed = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=rules["structure_rules"]["internal_outline_comments"]["patterns"],
    )

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "structure.heading_order"
        for finding in result["findings"]
    )

# Heading Level
def test_run_structure_judge_detects_heading_level_issue() -> None:
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
    preprocessed = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=rules["structure_rules"]["internal_outline_comments"]["patterns"],
    )

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "structure.heading_levels"
        for finding in result["findings"]
    )

# H1 and style detection
def test_run_structure_judge_detects_h1_script_span_and_inline_style() -> None:
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    """

    generated_html = """
    <h1>Titre interdit</h1>
    <p style="color:red;">Intro</p>
    <h2>Section A</h2>
    <span>Décoration</span>
    <script>alert('x')</script>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=rules["structure_rules"]["internal_outline_comments"]["patterns"],
    )

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    rule_ids = {finding["rule_id"] for finding in result["findings"]}

    assert "structure.no_h1_in_body" in rule_ids
    assert "structure.no_scripts" in rule_ids
    assert "structure.no_decorative_spans" in rule_ids
    assert "structure.no_inline_styles_except_tables" in rule_ids

# Internal Comment Detection
def test_run_structure_judge_detects_internal_comment_exposure() -> None:
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    """

    generated_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <p>Instruction : ce texte ne doit pas apparaître.</p>
    """

    rules = _build_rules(expected_outline_html)
    preprocessed = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=rules["structure_rules"]["internal_outline_comments"]["patterns"],
    )

    result = run_structure_judge(preprocessed, rules)

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "structure.no_internal_outline_comments_exposed"
        for finding in result["findings"]
    )

# Tolerated added sections: Learn more 
def test_run_structure_judge_allows_optional_trailing_complementary_reading() -> None:
    expected_outline_html = """
    <p>Intro</p>
    <h2>Section A</h2>
    <h3>Sous-section A.1</h3>
    <h2>Conclusion</h2>
    <p><strong>CTA :</strong> Read more</p>
    """

    generated_html = """
    <p>Intro générée</p>
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
    preprocessed = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=rules["structure_rules"]["internal_outline_comments"]["patterns"],
    )

    result = run_structure_judge(preprocessed, rules)

    rule_ids = {finding["rule_id"] for finding in result["findings"]}

    assert "structure.heading_order" not in rule_ids
    assert "structure.heading_levels" not in rule_ids
    assert "structure.heading_text" not in rule_ids
    assert "structure.no_added_sections" not in rule_ids

from contentcreajudge.preprocessing.structure_preprocessor import (
    preprocess_structure_content,
)


def test_preprocess_structure_content_extracts_headings() -> None:
    expected_outline_html = """
    <p>Introduction attendue.</p>
    <h2>Section A</h2>
    <p>Texte A</p>
    <h3>Sous-section A.1</h3>
    <p>Texte A.1</p>
    <h2>Conclusion</h2>
    """

    generated_html = """
    <p>Introduction générée.</p>
    <h2>Section A</h2>
    <p>Contenu.</p>
    <h3>Sous-section A.1</h3>
    <p>Contenu.</p>
    <h2>Conclusion</h2>
    <p>Contenu final.</p>
    """

    result = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=["Angle de réponse", "Note", "Instruction", "Indication"],
    )

    assert result["expected"]["heading_count"] == 3
    assert result["generated"]["heading_count"] == 3
    assert result["generated"]["has_h1"] is False
    assert result["generated"]["has_script"] is False
    assert result["generated"]["has_span"] is False


def test_preprocess_structure_content_detects_forbidden_elements() -> None:
    expected_outline_html = "<p>Intro</p><h2>Section</h2>"

    generated_html = """
    <h1>Titre interdit</h1>
    <p style="color:red;">Intro</p>
    <h2>Section</h2>
    <span>Décoration</span>
    <script>alert('x')</script>
    """

    result = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=["Angle de réponse", "Note", "Instruction", "Indication"],
    )

    assert result["generated"]["has_h1"] is True
    assert result["generated"]["has_script"] is True
    assert result["generated"]["has_span"] is True
    assert result["generated"]["has_inline_style_outside_tables"] is True


def test_preprocess_structure_content_detects_internal_comments() -> None:
    expected_outline_html = "<p>Intro</p><h2>Section</h2>"

    generated_html = """
    <p>Intro</p>
    <h2>Section</h2>
    <p>Note : ce block devait rester interne.</p>
    """

    result = preprocess_structure_content(
        expected_outline_html=expected_outline_html,
        generated_html=generated_html,
        internal_comment_patterns=["Angle de réponse", "Note", "Instruction", "Indication"],
    )

    assert result["generated"]["has_internal_outline_comments_exposed"] is True
    assert "Note" in result["generated"]["detected_internal_comment_patterns"]

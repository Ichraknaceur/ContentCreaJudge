"""Tests for the funnel preprocessor."""

from __future__ import annotations

from contentcreajudge.preprocessing.funnel_preprocessor import preprocess_funnel_content


def test_preprocess_funnel_content_removes_html_tags() -> None:
    result = preprocess_funnel_content("<p>Contenu <strong>pédagogique</strong></p>")

    assert result["normalized_text"] == "Contenu pédagogique"


def test_preprocess_funnel_content_decodes_html_entities() -> None:
    result = preprocess_funnel_content(
        "<p>Diff&eacute;renciation &eacute;ditoriale</p>"
    )

    assert result["normalized_text"] == "Différenciation éditoriale"


def test_preprocess_funnel_content_normalizes_whitespace() -> None:
    result = preprocess_funnel_content("Texte\n\navec\tplusieurs    espaces")

    assert result["normalized_text"] == "Texte avec plusieurs espaces"


def test_preprocess_funnel_content_counts_words() -> None:
    result = preprocess_funnel_content("<p>Un contenu simple et clair.</p>")

    assert result["word_count"] == 5


def test_preprocess_funnel_content_detects_empty_content() -> None:
    result = preprocess_funnel_content("   <p></p>   ")

    assert result["normalized_text"] == ""
    assert result["word_count"] == 0
    assert result["is_empty"] is True


def test_preprocess_funnel_content_keeps_original_content() -> None:
    content = "<h2>Titre</h2><p>Texte.</p>"

    result = preprocess_funnel_content(content)

    assert result["original_content"] == content

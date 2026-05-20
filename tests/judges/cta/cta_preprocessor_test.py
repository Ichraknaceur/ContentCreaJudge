"""Tests for CTA preprocessing."""

from __future__ import annotations

from contentcreajudge.preprocessing.cta_preprocessor import preprocess_cta_content


def test_preprocess_cta_detects_cta_block() -> None:
    content = '<p>Intro</p><p class="cta"><strong>Read more</strong></p>'

    result = preprocess_cta_content(content)

    assert result["has_cta"] is True
    assert result["cta_count"] == 1
    assert result["cta_texts"] == ["Read more"]

    cta_block = result["cta_blocks"][0]
    assert cta_block["tag_name"] == "p"
    assert "cta" in cta_block["classes"]
    assert cta_block["has_strong"] is True
    assert cta_block["strong_text"] == "Read more"


def test_preprocess_cta_detects_missing_cta() -> None:
    content = "<p>Intro</p><p>Conclusion</p>"

    result = preprocess_cta_content(content)

    assert result["has_cta"] is False
    assert result["cta_count"] == 0
    assert result["cta_texts"] == []


def test_preprocess_cta_detects_multiple_cta_blocks() -> None:
    content = (
        "<p>Intro</p>"
        '<p class="cta"><strong>Read more</strong></p>'
        '<p class="cta"><strong>Discover</strong></p>'
    )

    result = preprocess_cta_content(content)

    assert result["has_cta"] is True
    assert result["cta_count"] == 2
    assert result["cta_texts"] == ["Read more", "Discover"]


def test_preprocess_cta_detects_complementary_reading_section() -> None:
    content = (
        "<p>Intro</p>"
        '<p class="cta"><strong>Read more</strong></p>'
        "<h2>Lecture complémentaire</h2>"
        "<ul><li>Article lié</li></ul>"
    )

    result = preprocess_cta_content(content)

    assert result["has_complementary_reading"] is True
    assert result["complementary_reading_indexes"] == [2]


def test_preprocess_cta_detects_learn_more_section() -> None:
    content = (
        "<p>Intro</p>"
        '<p class="cta"><strong>Read more</strong></p>'
        "<h2>Learn more</h2>"
        "<ul><li>Related article</li></ul>"
    )

    result = preprocess_cta_content(content)

    assert result["has_complementary_reading"] is True
    assert result["complementary_reading_indexes"] == [2]


def test_preprocess_cta_detects_quiz_correction_block() -> None:
    content = (
        "<ol><li><p><strong>Q1 - Question</strong></p></li></ol>"
        "<h2>Corrigé du quiz</h2>"
        "<ol><li><p>Réponse correcte : A</p></li></ol>"
        '<p class="cta"><strong>Read more</strong></p>'
    )

    result = preprocess_cta_content(content)

    assert result["has_quiz_correction"] is True
    assert result["quiz_correction_indexes"] == [1]
    assert result["cta_count"] == 1
    assert result["cta_blocks"][0]["index"] == 3


def test_preprocess_cta_normalizes_html_entities() -> None:
    content = '<p class="cta"><strong>Lire&nbsp;la suite</strong></p>'

    result = preprocess_cta_content(content)

    assert result["cta_texts"] == ["Lire la suite"]

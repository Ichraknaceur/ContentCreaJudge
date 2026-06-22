"""Tests for the editorial style preprocessor."""

from __future__ import annotations

from contentcreajudge.preprocessing.editorial_style_preprocessor import (
    preprocess_editorial_style_content,
)


def test_preprocess_editorial_style_content_normalizes_html() -> None:
    """It should remove HTML tags and normalize text."""
    result = preprocess_editorial_style_content(
        content="<p>Bonjour&nbsp;!</p><p>Deuxième phrase.</p>",
        editorial_style={
            "writingStyle": "<p>Style clair.</p>",
            "writeLikeThis": "<p>Bon exemple.</p>",
            "notLikeThis": "<p>Mauvais exemple.</p>",
        },
    )

    assert result["normalized_content"] == "Bonjour ! Deuxième phrase."
    assert result["editorial_style"]["writingStyle"] == "Style clair."
    assert result["editorial_style"]["writeLikeThis"] == "Bon exemple."
    assert result["editorial_style"]["notLikeThis"] == "Mauvais exemple."


def test_preprocess_editorial_style_content_counts_content_stats() -> None:
    """It should compute simple content statistics."""
    result = preprocess_editorial_style_content(
        content="Première phrase. Deuxième phrase.",
        editorial_style={
            "writingStyle": "Style clair.",
            "writeLikeThis": "Bon exemple.",
            "notLikeThis": "Mauvais exemple.",
        },
    )

    assert result["content_stats"]["word_count"] == 4
    assert result["content_stats"]["sentence_count"] == 2
    assert result["content_stats"]["is_empty"] is False


def test_preprocess_editorial_style_content_detects_missing_style_fields() -> None:
    """It should expose missing editorial style fields."""
    result = preprocess_editorial_style_content(
        content="Un article à juger.",
        editorial_style={
            "writingStyle": "Style clair.",
            "writeLikeThis": "",
            "notLikeThis": "",
        },
    )

    assert result["style_stats"]["missing_style_fields"] == [
        "writeLikeThis",
        "notLikeThis",
    ]


def test_preprocess_editorial_style_content_handles_empty_content() -> None:
    """It should mark empty content."""
    result = preprocess_editorial_style_content(
        content="   ",
        editorial_style={
            "writingStyle": "Style clair.",
            "writeLikeThis": "Bon exemple.",
            "notLikeThis": "Mauvais exemple.",
        },
    )

    assert result["normalized_content"] == ""
    assert result["content_stats"]["word_count"] == 0
    assert result["content_stats"]["sentence_count"] == 0
    assert result["content_stats"]["is_empty"] is True

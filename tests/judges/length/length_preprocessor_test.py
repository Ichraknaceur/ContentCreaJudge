from __future__ import annotations

from contentcreajudge.preprocessing.length_preprocessor import preprocess_length_content


def test_preprocess_length_content_counts_plain_text_words() -> None:
    """Count words in plain text content."""
    result = preprocess_length_content("Bonjour tout le monde")

    assert result == {
        "original_content": "Bonjour tout le monde",
        "normalized_text": "Bonjour tout le monde",
        "word_count": 4,
        "is_empty": False,
    }


def test_preprocess_length_content_removes_html_tags() -> None:
    """Remove HTML tags before counting words."""
    result = preprocess_length_content("<p>Bonjour</p><strong>le monde</strong>")

    assert result["normalized_text"] == "Bonjour le monde"
    assert result["word_count"] == 3
    assert result["is_empty"] is False


def test_preprocess_length_content_decodes_html_entities() -> None:
    """Decode HTML entities before counting words."""
    result = preprocess_length_content("<p>L&rsquo;IA &amp; le SEO</p>")

    assert result["normalized_text"] == "L\u2019IA & le SEO"
    assert result["word_count"] == 4


def test_preprocess_length_content_normalizes_whitespace() -> None:
    """Normalize repeated whitespace before counting words."""
    result = preprocess_length_content("  Bonjour\n\n\t le   monde  ")

    assert result["normalized_text"] == "Bonjour le monde"
    assert result["word_count"] == 3


def test_preprocess_length_content_returns_empty_for_empty_string() -> None:
    """Return an empty result for empty content."""
    result = preprocess_length_content("")

    assert result == {
        "original_content": "",
        "normalized_text": "",
        "word_count": 0,
        "is_empty": True,
    }


def test_preprocess_length_content_returns_empty_for_html_only() -> None:
    """Return an empty result when content only contains HTML tags."""
    result = preprocess_length_content("<p>   </p><br>")

    assert result["normalized_text"] == ""
    assert result["word_count"] == 0
    assert result["is_empty"] is True


def test_preprocess_length_content_excludes_script_and_style_content() -> None:
    """Exclude script and style block content from the word count."""
    content = (
        "<style>body { color: red; font-size: 14px; }</style>"
        "<p>Bonjour le monde</p>"
        "<script>console.log('tracking pixel loaded');</script>"
    )

    result = preprocess_length_content(content)

    assert result["normalized_text"] == "Bonjour le monde"
    assert result["word_count"] == 3

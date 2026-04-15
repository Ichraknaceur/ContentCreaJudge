from contentcreajudge.preprocessing.typography_preprocessor import (
    preprocess_typography_content,
)


def test_preprocess_typography_content_success() -> None:
    content = "<p><a></a>Bonjour&nbsp;!</p>\n<p>Test<br><br /></p>"

    result = preprocess_typography_content(content)

    assert result["original_content"] == content
    assert result["is_empty"] is False
    assert result["br_tag_count"] == 2
    assert result["anchor_tag_count"] == 1
    assert "Bonjour" in str(result["decoded_text"])
    assert "\u00A0" in str(result["decoded_text"])
    assert "Bonjour" in str(result["normalized_text"])


def test_preprocess_typography_content_empty() -> None:
    content = "   \n   "

    result = preprocess_typography_content(content)

    assert result["is_empty"] is True
    assert result["br_tag_count"] == 0
    assert result["normalized_text"] == ""


def test_preprocess_typography_content_extracts_lines() -> None:
    content = "<p>Ligne 1</p>\n<p>Ligne 2   </p>"

    result = preprocess_typography_content(content)

    assert len(result["original_lines"]) == 2
    assert len(result["decoded_lines"]) == 2
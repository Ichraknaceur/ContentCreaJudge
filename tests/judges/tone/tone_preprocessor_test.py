from __future__ import annotations

from contentcreajudge.preprocessing.tone_preprocessor import preprocess_tone_content


def test_preprocess_tone_content_keeps_original_content() -> None:
    content = "<p>Un texte didactique.</p>"

    result = preprocess_tone_content(content)

    assert result["content"] == content


def test_preprocess_tone_content_normalizes_html_text() -> None:
    content = "<p>Un&nbsp;texte <strong>didactique</strong>.</p>"

    result = preprocess_tone_content(content)

    assert result["normalized_text"] == "Un texte didactique."


def test_preprocess_tone_content_counts_words() -> None:
    content = "<p>Un texte didactique.</p>"

    result = preprocess_tone_content(content)

    assert result["word_count"] == 3
    assert result["char_count"] > 0


def test_preprocess_tone_content_detects_empty_content() -> None:
    result = preprocess_tone_content("   ")

    assert result["normalized_text"] == ""
    assert result["word_count"] == 0
    assert result["char_count"] == 0
    assert result["is_empty"] is True


def test_preprocess_tone_content_decodes_html_entities() -> None:
    content = "Ton professionnel &amp; accessible."

    result = preprocess_tone_content(content)

    assert result["normalized_text"] == "Ton professionnel & accessible."

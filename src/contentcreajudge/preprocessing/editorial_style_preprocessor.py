"""Preprocessing utilities for the editorial style judge."""

from __future__ import annotations

import html
import re
from typing import Any

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _normalize_text(value: object) -> str:
    """Normalize a text value by removing HTML tags and extra whitespace."""
    if value is None:
        return ""

    raw_text = str(value)
    text_without_html = _HTML_TAG_RE.sub(" ", raw_text)
    decoded_text = html.unescape(text_without_html)
    return _WHITESPACE_RE.sub(" ", decoded_text).strip()


def _count_paragraphs(value: str) -> int:
    """Count non-empty paragraphs from raw text."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", value) if part.strip()]
    return len(paragraphs)


def _count_sentences(value: str) -> int:
    """Count sentences using a simple punctuation-based splitter."""
    normalized_text = _normalize_text(value)

    if not normalized_text:
        return 0

    sentences = [
        sentence.strip()
        for sentence in _SENTENCE_SPLIT_RE.split(normalized_text)
        if sentence.strip()
    ]

    return len(sentences)


def _count_words(value: str) -> int:
    """Count words in normalized text."""
    normalized_text = _normalize_text(value)
    return len(normalized_text.split()) if normalized_text else 0


def preprocess_editorial_style_content(
    content: str,
    editorial_style: dict[str, Any],
) -> dict[str, object]:
    """Prepare content and editorial style inputs for editorial style evaluation."""
    writing_style = editorial_style.get("writingStyle", "")
    write_like_this = editorial_style.get("writeLikeThis", "")
    not_like_this = editorial_style.get("notLikeThis", "")

    normalized_content = _normalize_text(content)
    normalized_writing_style = _normalize_text(writing_style)
    normalized_write_like_this = _normalize_text(write_like_this)
    normalized_not_like_this = _normalize_text(not_like_this)

    missing_style_fields = [
        field_name
        for field_name, field_value in {
            "writingStyle": normalized_writing_style,
            "writeLikeThis": normalized_write_like_this,
            "notLikeThis": normalized_not_like_this,
        }.items()
        if not field_value
    ]

    return {
        "original_content": content,
        "normalized_content": normalized_content,
        "editorial_style": {
            "writingStyle": normalized_writing_style,
            "writeLikeThis": normalized_write_like_this,
            "notLikeThis": normalized_not_like_this,
        },
        "content_stats": {
            "word_count": _count_words(content),
            "sentence_count": _count_sentences(content),
            "paragraph_count": _count_paragraphs(content),
            "is_empty": not bool(normalized_content),
        },
        "style_stats": {
            "writing_style_word_count": _count_words(str(writing_style)),
            "write_like_this_word_count": _count_words(str(write_like_this)),
            "not_like_this_word_count": _count_words(str(not_like_this)),
            "missing_style_fields": missing_style_fields,
        },
    }

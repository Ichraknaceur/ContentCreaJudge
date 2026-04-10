"""Preprocessing utilities for the length judge."""

from __future__ import annotations

import html
import re


def preprocess_length_content(content: str) -> dict[str, object]:
    """Prepare the content for length evaluation"""

    text_without_html = re.sub(r"<[^>]+>", " ", content)
    decoded_text = html.unescape(text_without_html)
    normalized_text = re.sub(r"\s+", " ", decoded_text).strip()
    word_count = len(normalized_text.split()) if normalized_text else 0

    return {
        "original_content": content,
        "normalized_text": normalized_text,
        "word_count": word_count,
        "is_empty": word_count == 0,
    }
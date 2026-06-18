"""Preprocessing utilities for the tone judge."""

from __future__ import annotations

import html
import re


def preprocess_tone_content(content: str) -> dict[str, object]:
    """Prepare content for tone evaluation."""
    text_without_html = re.sub(r"<[^>]+>", " ", content)
    decoded_text = html.unescape(text_without_html)
    normalized_text = re.sub(r"\s+", " ", decoded_text).strip()
    normalized_text = re.sub(r"\s+([.,;:!?])", r"\1", normalized_text)

    return {
        "content": content,
        "normalized_text": normalized_text,
        "char_count": len(normalized_text),
        "word_count": len(normalized_text.split()) if normalized_text else 0,
        "is_empty": not bool(normalized_text),
    }

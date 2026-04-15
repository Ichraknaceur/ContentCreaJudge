"""Preprocessing utilities for the typography judge."""

from __future__ import annotations

import html
import re


def preprocess_typography_content(content: str) -> dict[str, object]:
    """Prepare the content for typography evaluation."""

    html_tag_marker = "__HTML_TAG__"
    content_with_tag_markers = re.sub(r"<[^>]+>", html_tag_marker, content)
    text_without_html = re.sub(
        rf"[ \t]*{re.escape(html_tag_marker)}(?:[ \t]*{re.escape(html_tag_marker)})*[ \t]*",
        " ",
        content_with_tag_markers,
    )

    decoded_text = html.unescape(text_without_html)
    normalized_text = re.sub(r"\s+", " ", decoded_text).strip()

    original_lines = content.splitlines()
    decoded_lines = decoded_text.splitlines()

    decoded_text_no_newlines = decoded_text.replace("\n", " ").replace("\r", " ")

    br_tag_count = len(
        re.findall(r"<br\s*/?>", content, flags=re.IGNORECASE)
    )
    anchor_tag_count = len(
        re.findall(r"<a\b", content, flags=re.IGNORECASE)
    )

    return {
        "original_content": content,
        "text_without_html": text_without_html,
        "decoded_text": decoded_text,
        "decoded_text_no_newlines": decoded_text_no_newlines,
        "normalized_text": normalized_text,
        "original_lines": original_lines,
        "decoded_lines": decoded_lines,
        "br_tag_count": br_tag_count,
        "anchor_tag_count": anchor_tag_count,
        "is_empty": len(normalized_text) == 0,
    }

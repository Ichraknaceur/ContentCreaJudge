"""Preprocessing utilities for the Brief judge."""

from __future__ import annotations

import html
import re


def preprocess_brief_content(
    article: str,
    brief: str,
) -> dict[str, object]:
    """Prepare the article and the brief for LLM-based brief evaluation."""
    normalized_article = _normalize_text(article)
    normalized_brief = _normalize_text(brief)

    article_without_html = _strip_html(article)
    normalized_article_text = _normalize_text(article_without_html)

    return {
        "original_article": article,
        "original_brief": brief,
        "normalized_article": normalized_article,
        "normalized_brief": normalized_brief,
        "article_text": normalized_article_text,
        "article_word_count": _count_words(normalized_article_text),
        "brief_word_count": _count_words(normalized_brief),
        "is_article_empty": not bool(normalized_article_text),
        "is_brief_empty": not bool(normalized_brief),
    }


def _strip_html(content: str) -> str:
    """Remove HTML tags from content."""
    text_without_html = re.sub(r"<[^>]+>", " ", content)
    return html.unescape(text_without_html)


def _normalize_text(content: str) -> str:
    """Normalize whitespace and decode HTML entities."""
    decoded_content = html.unescape(content)
    return re.sub(r"\s+", " ", decoded_content).strip()


def _count_words(content: str) -> int:
    """Count words in a normalized text."""
    if not content:
        return 0

    return len(content.split())

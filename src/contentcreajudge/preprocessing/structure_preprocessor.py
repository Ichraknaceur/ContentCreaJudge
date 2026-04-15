"""Preprocessing utilities for the structure judge."""

from __future__ import annotations

import html
import re
from typing import Any

from bs4 import BeautifulSoup, Tag


def _normalize_text(value: str) -> str:
    """Normalize extracted text for stable structural comparisons."""
    decoded = html.unescape(value)
    normalized = re.sub(r"\s+", " ", decoded).strip()
    return normalized


def _extract_headings(soup: BeautifulSoup) -> list[dict[str, str]]:
    """Extract ordered headings from HTML."""
    headings: list[dict[str, str]] = []

    for element in soup.find_all(["h2", "h3", "h4"]):
        if not isinstance(element, Tag):
            continue

        headings.append(
            {
                "level": element.name,
                "text": _normalize_text(element.get_text(" ", strip=True)),
            }
        )

    return headings


def _extract_used_tags(soup: BeautifulSoup) -> list[str]:
    """Extract all HTML tag names used in the document."""
    used_tags = {
        element.name
        for element in soup.find_all()
        if isinstance(element, Tag) and element.name is not None
    }
    return sorted(used_tags)


def _has_inline_style_outside_tables(soup: BeautifulSoup) -> bool:
    """Return True if inline styles are present outside allowed table tags."""
    allowed_style_tags = {"table", "thead", "tbody", "tr", "th", "td"}

    for element in soup.find_all():
        if not isinstance(element, Tag):
            continue

        if element.has_attr("style") and element.name not in allowed_style_tags:
            return True

    return False


def _detect_internal_comment_patterns(
    text: str,
    patterns: list[str],
) -> list[str]:
    """Return the list of internal outline comment patterns found in text."""
    normalized_text = _normalize_text(text).lower()
    detected: list[str] = []

    for pattern in patterns:
        normalized_pattern = _normalize_text(pattern).lower()
        if normalized_pattern and normalized_pattern in normalized_text:
            detected.append(pattern)

    return detected


def preprocess_structure_content(
    expected_outline_html: str,
    generated_html: str,
    internal_comment_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Prepare expected and generated HTML content for structure evaluation."""
    internal_comment_patterns = internal_comment_patterns or []

    expected_soup = BeautifulSoup(expected_outline_html, "html.parser")
    generated_soup = BeautifulSoup(generated_html, "html.parser")

    expected_headings = _extract_headings(expected_soup)
    generated_headings = _extract_headings(generated_soup)

    generated_text = _normalize_text(generated_soup.get_text(" ", strip=True))
    detected_internal_comments = _detect_internal_comment_patterns(
        text=generated_text,
        patterns=internal_comment_patterns,
    )

    return {
        "expected": {
            "raw_html": expected_outline_html,
            "headings": expected_headings,
            "heading_count": len(expected_headings),
            "has_intro_paragraph": expected_soup.find("p") is not None,
        },
        "generated": {
            "raw_html": generated_html,
            "headings": generated_headings,
            "heading_count": len(generated_headings),
            "has_intro_paragraph": generated_soup.find("p") is not None,
            "used_tags": _extract_used_tags(generated_soup),
            "has_h1": generated_soup.find("h1") is not None,
            "has_script": generated_soup.find("script") is not None,
            "has_span": generated_soup.find("span") is not None,
            "has_inline_style_outside_tables": _has_inline_style_outside_tables(
                generated_soup
            ),
            "detected_internal_comment_patterns": detected_internal_comments,
            "has_internal_outline_comments_exposed": len(detected_internal_comments) > 0,
            "normalized_text": generated_text,
        },
    }
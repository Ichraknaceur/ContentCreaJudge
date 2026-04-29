"""Preprocessing utilities for the CTA judge."""

from __future__ import annotations

import html
import re
from bs4 import BeautifulSoup
from bs4.element import Tag


def _normalize_text(text: str) -> str:
    """Normalize text for reliable CTA comparisons."""
    decoded_text = html.unescape(text)
    normalized_text = re.sub(r"\s+", " ", decoded_text).strip()
    return normalized_text


def _is_cta_tag(tag: Tag) -> bool:
    """Return True when a tag is a CTA paragraph."""
    return tag.name == "p" and "cta" in tag.get("class", [])


def _get_direct_body_children(soup: BeautifulSoup) -> list[Tag]:
    """Return top-level HTML tags in document order."""
    root = soup.body if soup.body else soup
    return [child for child in root.children if isinstance(child, Tag)]


def preprocess_cta_content(content: str) -> dict[str, object]:
    """Prepare HTML content for CTA evaluation."""

    soup = BeautifulSoup(content, "html.parser")
    direct_children = _get_direct_body_children(soup)

    cta_blocks: list[dict[str, object]] = []

    for index, tag in enumerate(direct_children):
        if not _is_cta_tag(tag):
            continue

        strong_tag = tag.find("strong")
        cta_text = _normalize_text(tag.get_text(" ", strip=True))

        cta_blocks.append(
            {
                "index": index,
                "html": str(tag),
                "text": cta_text,
                "tag_name": tag.name,
                "classes": tag.get("class", []),
                "has_strong": strong_tag is not None,
                "strong_text": (
                    _normalize_text(strong_tag.get_text(" ", strip=True))
                    if strong_tag
                    else None
                ),
            }
        )

    headings = [
        {
            "index": index,
            "tag_name": tag.name,
            "text": _normalize_text(tag.get_text(" ", strip=True)),
        }
        for index, tag in enumerate(direct_children)
        if tag.name in {"h2", "h3", "h4"}
    ]

    complementary_reading_indexes = [
        heading["index"]
        for heading in headings
        if str(heading["text"]).lower() in {"lecture complémentaire", "learn more"}
    ]

    quiz_correction_indexes = [
        heading["index"]
        for heading in headings
        if str(heading["text"]).lower() == "corrigé du quiz"
    ]

    return {
        "original_content": content,
        "normalized_text": _normalize_text(soup.get_text(" ", strip=True)),
        "top_level_tag_count": len(direct_children),
        "cta_blocks": cta_blocks,
        "cta_count": len(cta_blocks),
        "cta_texts": [block["text"] for block in cta_blocks],
        "has_cta": len(cta_blocks) > 0,
        "headings": headings,
        "has_complementary_reading": len(complementary_reading_indexes) > 0,
        "complementary_reading_indexes": complementary_reading_indexes,
        "has_quiz_correction": len(quiz_correction_indexes) > 0,
        "quiz_correction_indexes": quiz_correction_indexes,
    }
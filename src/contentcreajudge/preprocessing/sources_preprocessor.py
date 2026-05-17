"""Preprocessing utilities for the sources judge."""

from __future__ import annotations

import re
from html import unescape
from urllib.parse import urlparse

from bs4 import BeautifulSoup

RAW_URL_PATTERN = re.compile(r"(?<![\"'=])(https?://[^\s<>\"]+)")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")
ATTACHED_ANCHOR_PATTERN = re.compile(r"\w<a\s+", re.IGNORECASE)


def _is_external_url(url: str, internal_domain: str) -> bool:
    """Return True when the URL does not belong to the internal domain."""
    parsed_url = urlparse(url)
    parsed_internal = urlparse(internal_domain)

    if not parsed_url.netloc:
        return False

    return parsed_url.netloc != parsed_internal.netloc


def _normalize_html_content(content: str) -> str:
    """Normalize escaped HTML copied from JSON-like payloads."""
    return content.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")


def _is_complementary_heading(text: str) -> bool:
    """Return True when a heading represents the complementary reading section."""
    normalized = text.strip().lower()
    return normalized in {
        "lecture complémentaire",
        "lecture complementaire",
        "learn more",
    }


def preprocess_sources_content(
    content: str,
    internal_domain: str,
) -> dict[str, object]:
    """Prepare source-related signals from HTML content."""
    if not internal_domain.strip():
        internal_domain = "https://contentcrea.com"

    normalized_content = _normalize_html_content(content or "")
    soup = BeautifulSoup(normalized_content, "html.parser")
    anchors = soup.find_all("a")

    extracted_links: list[dict[str, object]] = []

    for index, anchor in enumerate(anchors, start=1):
        href = str(anchor.get("href", "")).strip()
        anchor_text = anchor.get_text(" ", strip=True)
        target = anchor.get("target")
        rel_value = anchor.get("rel")

        if isinstance(rel_value, list):
            rel = " ".join(rel_value)
        elif rel_value is None:
            rel = ""
        else:
            rel = str(rel_value)

        is_external = _is_external_url(href, internal_domain)
        section = "body"

        previous_heading = anchor.find_previous(["h2", "h3"])

        heading_text = ""
        if previous_heading is not None:
            heading_text = previous_heading.get_text(" ", strip=True)

        if heading_text and _is_complementary_heading(heading_text):
            section = "complementary_reading"

        extracted_links.append(
            {
                "index": index,
                "href": href,
                "anchor_text": unescape(anchor_text),
                "target": target or "",
                "rel": rel,
                "is_external": is_external,
                "is_internal": not is_external,
                "section": section,
                "html": str(anchor),
            },
        )

    raw_urls = RAW_URL_PATTERN.findall(normalized_content or "")
    markdown_links = MARKDOWN_LINK_PATTERN.findall(normalized_content or "")
    attached_anchor_matches = ATTACHED_ANCHOR_PATTERN.findall(
        normalized_content or "",
    )

    external_links = [link for link in extracted_links if bool(link["is_external"])]
    internal_links = [link for link in extracted_links if bool(link["is_internal"])]
    body_links = [link for link in extracted_links if link["section"] == "body"]

    complementary_reading_links = [
        link for link in extracted_links if link["section"] == "complementary_reading"
    ]

    body_external_links = [link for link in body_links if bool(link["is_external"])]

    complementary_reading_external_links = [
        link for link in complementary_reading_links if bool(link["is_external"])
    ]

    return {
        "original_content": content,
        "normalized_content": normalized_content,
        "links": extracted_links,
        "external_links": external_links,
        "internal_links": internal_links,
        "body_links": body_links,
        "complementary_reading_links": complementary_reading_links,
        "body_external_links": body_external_links,
        "complementary_reading_external_links": complementary_reading_external_links,
        "body_links_count": len(body_links),
        "complementary_reading_links_count": len(complementary_reading_links),
        "body_external_links_count": len(body_external_links),
        "complementary_reading_external_links_count": len(
            complementary_reading_external_links,
        ),
        "links_count": len(extracted_links),
        "external_links_count": len(external_links),
        "internal_links_count": len(internal_links),
        "raw_urls": raw_urls,
        "raw_urls_count": len(raw_urls),
        "markdown_links": markdown_links,
        "markdown_links_count": len(markdown_links),
        "attached_anchor_count": len(attached_anchor_matches),
        "has_links": len(extracted_links) > 0,
        "has_external_links": len(external_links) > 0,
        "has_internal_links": len(internal_links) > 0,
        "has_raw_urls": len(raw_urls) > 0,
        "has_markdown_links": len(markdown_links) > 0,
        "has_attached_anchors": len(attached_anchor_matches) > 0,
    }

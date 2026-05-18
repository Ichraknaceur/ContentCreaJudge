"""Global preprocessing utilities shared by global evaluation orchestration."""

from __future__ import annotations

# ruff: noqa: D202, I001

import html
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag


RAW_URL_PATTERN = re.compile(r"(?<![\"'=])(https?://[^\s<>\"]+)")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")
ATTACHED_ANCHOR_PATTERN = re.compile(r"\w<a\s+", re.IGNORECASE)


def preprocess_global_content(
    content: str,
    internal_domain: str = "https://contentcrea.com",
) -> dict[str, object]:
    """Extract reusable HTML and text signals for all global judges."""

    normalized_content = _normalize_html_content(content or "")
    soup = BeautifulSoup(normalized_content, "html.parser")
    root = soup.body or soup

    normalized_text = _extract_normalized_text(soup)
    headings = _extract_headings(soup)
    h2_sections = _extract_h2_sections(soup)

    return {
        "original_content": content or "",
        "normalized_content": normalized_content,
        "normalized_text": normalized_text,
        "word_count": _count_words(normalized_text),
        "is_empty": normalized_text == "",
        "body_text": normalized_text,
        "paragraphs": _extract_paragraphs(soup),
        "headings": headings,
        "headings_h2_h3": [
            heading["text"] for heading in headings if heading["level"] in {"h2", "h3"}
        ],
        "introduction": _extract_introduction(root),
        "conclusion": _extract_conclusion(soup),
        "h2_sections": h2_sections,
        "links": _extract_links(
            soup=soup,
            normalized_content=normalized_content,
            internal_domain=internal_domain,
        ),
        "cta": _extract_cta_signals(root),
        "structure": _extract_structure_signals(soup),
        "typography": _extract_typography_signals(content or ""),
    }


def _normalize_html_content(content: str) -> str:
    """Normalize escaped HTML copied from JSON-like payloads."""

    return content.replace('\\"', '"').replace("\\'", "'").replace("\\n", "\n")


def _normalize_text(text: str) -> str:
    """Decode HTML entities and normalize whitespace."""

    decoded_text = html.unescape(text)
    return re.sub(r"\s+", " ", decoded_text).strip()


def _extract_normalized_text(soup: BeautifulSoup) -> str:
    """Extract normalized visible text from HTML."""

    return _normalize_text(soup.get_text(" ", strip=True))


def _count_words(text: str) -> int:
    """Count words from normalized text."""

    return len(text.split()) if text else 0


def _extract_paragraphs(soup: BeautifulSoup) -> list[str]:
    """Extract normalized paragraph texts."""

    paragraphs: list[str] = []

    for paragraph in soup.find_all("p"):
        text = _normalize_text(paragraph.get_text(" ", strip=True))
        if text:
            paragraphs.append(text)

    return paragraphs


def _extract_headings(soup: BeautifulSoup) -> list[dict[str, object]]:
    """Extract ordered headings from H1 to H4."""

    headings: list[dict[str, object]] = []

    for index, tag in enumerate(soup.find_all(["h1", "h2", "h3", "h4"])):
        if not isinstance(tag, Tag):
            continue

        headings.append(
            {
                "index": index,
                "level": tag.name,
                "text": _normalize_text(tag.get_text(" ", strip=True)),
            }
        )

    return headings


def _get_direct_children(root: BeautifulSoup | Tag) -> list[Tag]:
    """Return top-level HTML tags in document order."""

    return [child for child in root.children if isinstance(child, Tag)]


def _extract_introduction(root: BeautifulSoup | Tag) -> str:
    """Extract introduction text before the first H2."""

    introduction_parts: list[str] = []

    for element in root.children:
        if not isinstance(element, Tag):
            continue

        if element.name == "h2":
            break

        if element.name in {"p", "ul", "ol", "blockquote"}:
            text = _normalize_text(element.get_text(" ", strip=True))
            if text:
                introduction_parts.append(text)

    return _normalize_text(" ".join(introduction_parts))


def _collect_section_text(start_h2: Tag) -> str:
    """Collect text after an H2 until the next H2."""

    parts: list[str] = []

    for sibling in start_h2.next_siblings:
        if getattr(sibling, "name", None) == "h2":
            break

        if getattr(sibling, "name", None) in {"p", "ul", "ol", "blockquote"}:
            text = _normalize_text(sibling.get_text(" ", strip=True))
            if text:
                parts.append(text)

    return _normalize_text(" ".join(parts))


def _normalize_for_matching(text: str) -> str:
    """Normalize heading text for simple matching."""

    return _normalize_text(text).lower()


def _extract_conclusion(soup: BeautifulSoup) -> str:
    """Extract conclusion text from explicit Conclusion H2 or last useful H2."""

    h2_tags = soup.find_all("h2")
    if not h2_tags:
        return ""

    for h2 in h2_tags:
        if _normalize_for_matching(h2.get_text(" ", strip=True)) == "conclusion":
            return _collect_section_text(h2)

    excluded_titles = {
        "lecture complémentaire",
        "lecture complementaire",
        "learn more",
        "sources",
        "références",
        "references",
    }

    candidate_h2_tags = [
        h2
        for h2 in h2_tags
        if _normalize_for_matching(h2.get_text(" ", strip=True)) not in excluded_titles
    ]

    if candidate_h2_tags:
        return _collect_section_text(candidate_h2_tags[-1])

    return _collect_section_text(h2_tags[-1])


def _extract_h2_sections(soup: BeautifulSoup) -> list[dict[str, object]]:
    """Extract each H2 section with its H3 headings and text."""

    sections: list[dict[str, object]] = []

    for h2 in soup.find_all("h2"):
        title = _normalize_text(h2.get_text(" ", strip=True))
        content_parts: list[str] = []
        h3_headings: list[str] = []

        for sibling in h2.next_siblings:
            if getattr(sibling, "name", None) == "h2":
                break

            sibling_name = getattr(sibling, "name", None)

            if sibling_name == "h3":
                h3_text = _normalize_text(sibling.get_text(" ", strip=True))
                if h3_text:
                    h3_headings.append(h3_text)
                    content_parts.append(h3_text)

            elif sibling_name in {"p", "ul", "ol", "blockquote"}:
                text = _normalize_text(sibling.get_text(" ", strip=True))
                if text:
                    content_parts.append(text)

        sections.append(
            {
                "h2": title,
                "h3_headings": h3_headings,
                "text": _normalize_text(" ".join(content_parts)),
            }
        )

    return sections


def _is_external_url(url: str, internal_domain: str) -> bool:
    """Return True when URL does not belong to the internal domain."""

    parsed_url = urlparse(url)
    parsed_internal = urlparse(internal_domain)

    if not parsed_url.netloc:
        return False

    return parsed_url.netloc != parsed_internal.netloc


def _is_complementary_heading(text: str) -> bool:
    """Return True when a heading is a complementary reading section."""

    normalized = text.strip().lower()
    return normalized in {
        "lecture complémentaire",
        "lecture complementaire",
        "learn more",
    }


def _extract_links(
    soup: BeautifulSoup,
    normalized_content: str,
    internal_domain: str,
) -> dict[str, object]:
    """Extract link-related signals for sources and internal links."""

    extracted_links: list[dict[str, object]] = []

    for index, anchor in enumerate(soup.find_all("a"), start=1):
        href = str(anchor.get("href", "")).strip()
        anchor_text = _normalize_text(anchor.get_text(" ", strip=True))
        target = anchor.get("target")
        rel_value = anchor.get("rel")

        if isinstance(rel_value, list):
            rel = " ".join(rel_value)
        elif rel_value is None:
            rel = ""
        else:
            rel = str(rel_value)

        previous_heading = anchor.find_previous(["h2", "h3"])
        heading_text = (
            previous_heading.get_text(" ", strip=True)
            if previous_heading is not None
            else ""
        )

        section = (
            "complementary_reading"
            if heading_text and _is_complementary_heading(heading_text)
            else "body"
        )

        is_external = _is_external_url(href, internal_domain)

        extracted_links.append(
            {
                "index": index,
                "href": href,
                "anchor_text": anchor_text,
                "target": target or "",
                "rel": rel,
                "is_external": is_external,
                "is_internal": not is_external,
                "section": section,
                "html": str(anchor),
            }
        )

    external_links = [link for link in extracted_links if link["is_external"]]
    internal_links = [link for link in extracted_links if link["is_internal"]]
    body_links = [link for link in extracted_links if link["section"] == "body"]
    complementary_links = [
        link for link in extracted_links if link["section"] == "complementary_reading"
    ]

    raw_urls = RAW_URL_PATTERN.findall(normalized_content)
    markdown_links = MARKDOWN_LINK_PATTERN.findall(normalized_content)
    attached_anchor_matches = ATTACHED_ANCHOR_PATTERN.findall(normalized_content)

    return {
        "all": extracted_links,
        "external": external_links,
        "internal": internal_links,
        "body": body_links,
        "complementary_reading": complementary_links,
        "raw_urls": raw_urls,
        "markdown_links": markdown_links,
        "links_count": len(extracted_links),
        "external_links_count": len(external_links),
        "internal_links_count": len(internal_links),
        "raw_urls_count": len(raw_urls),
        "markdown_links_count": len(markdown_links),
        "attached_anchor_count": len(attached_anchor_matches),
        "has_links": len(extracted_links) > 0,
        "has_external_links": len(external_links) > 0,
        "has_internal_links": len(internal_links) > 0,
        "has_raw_urls": len(raw_urls) > 0,
        "has_markdown_links": len(markdown_links) > 0,
        "has_attached_anchors": len(attached_anchor_matches) > 0,
    }


def _extract_cta_signals(root: BeautifulSoup | Tag) -> dict[str, object]:
    """Extract CTA blocks and CTA placement signals."""

    direct_children = _get_direct_children(root)
    cta_blocks: list[dict[str, object]] = []
    headings: list[dict[str, object]] = []

    for index, tag in enumerate(direct_children):
        text = _normalize_text(tag.get_text(" ", strip=True))

        if tag.name in {"h2", "h3", "h4"}:
            headings.append(
                {
                    "index": index,
                    "tag_name": tag.name,
                    "text": text,
                }
            )

        if tag.name == "p" and "cta" in tag.get("class", []):
            strong_tag = tag.find("strong")

            cta_blocks.append(
                {
                    "index": index,
                    "html": str(tag),
                    "text": text,
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

    complementary_reading_indexes = [
        heading["index"]
        for heading in headings
        if str(heading["text"]).lower()
        in {"lecture complémentaire", "lecture complementaire", "learn more"}
    ]

    quiz_correction_indexes = [
        heading["index"]
        for heading in headings
        if str(heading["text"]).lower() == "corrigé du quiz"
    ]

    return {
        "top_level_tag_count": len(direct_children),
        "cta_blocks": cta_blocks,
        "cta_count": len(cta_blocks),
        "cta_texts": [block["text"] for block in cta_blocks],
        "has_cta": len(cta_blocks) > 0,
        "has_complementary_reading": len(complementary_reading_indexes) > 0,
        "complementary_reading_indexes": complementary_reading_indexes,
        "has_quiz_correction": len(quiz_correction_indexes) > 0,
        "quiz_correction_indexes": quiz_correction_indexes,
    }


def _extract_used_tags(soup: BeautifulSoup) -> list[str]:
    """Extract all HTML tags used in the document."""

    used_tags = {
        element.name
        for element in soup.find_all()
        if isinstance(element, Tag) and element.name is not None
    }

    return sorted(used_tags)


def _has_inline_style_outside_tables(soup: BeautifulSoup) -> bool:
    """Return True when inline style is used outside table tags."""

    allowed_style_tags = {"table", "thead", "tbody", "tr", "th", "td"}

    for element in soup.find_all():
        if not isinstance(element, Tag):
            continue

        if element.has_attr("style") and element.name not in allowed_style_tags:
            return True

    return False


def _extract_structure_signals(soup: BeautifulSoup) -> dict[str, object]:
    """Extract common structure signals."""

    return {
        "used_tags": _extract_used_tags(soup),
        "has_h1": soup.find("h1") is not None,
        "has_script": soup.find("script") is not None,
        "has_span": soup.find("span") is not None,
        "has_intro_paragraph": soup.find("p") is not None,
        "has_inline_style_outside_tables": _has_inline_style_outside_tables(soup),
    }


def _extract_typography_signals(content: str) -> dict[str, object]:
    """Extract common typography text signals."""

    html_tag_marker = "__HTML_TAG__"
    content_with_tag_markers = re.sub(r"<[^>]+>", html_tag_marker, content)

    tag_gap_pattern = (
        rf"[ \t]*{re.escape(html_tag_marker)}"
        rf"(?:[ \t]*{re.escape(html_tag_marker)})*[ \t]*"
    )

    text_without_html = re.sub(tag_gap_pattern, " ", content_with_tag_markers)
    decoded_text = html.unescape(text_without_html)
    normalized_text = re.sub(r"\s+", " ", decoded_text).strip()

    return {
        "text_without_html": text_without_html,
        "decoded_text": decoded_text,
        "decoded_text_no_newlines": decoded_text.replace("\n", " ").replace("\r", " "),
        "normalized_text": normalized_text,
        "original_lines": content.splitlines(),
        "decoded_lines": decoded_text.splitlines(),
        "br_tag_count": len(re.findall(r"<br\s*/?>", content, flags=re.IGNORECASE)),
        "anchor_tag_count": len(re.findall(r"<a\b", content, flags=re.IGNORECASE)),
        "is_empty": normalized_text == "",
    }

"""Preprocessing utilities for the SEO judge."""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any

from bs4 import BeautifulSoup

from contentcreajudge.core.errors import ConfigurationError
from contentcreajudge.core.settings import settings


def _normalize_text(text: str) -> str:
    """Decode HTML entities and normalize whitespace."""
    decoded_text = html.unescape(text)
    return re.sub(r"\s+", " ", decoded_text).strip()


def _extract_body_text(soup: BeautifulSoup) -> str:
    """Extract the full visible text from the content."""
    return _normalize_text(soup.get_text(" ", strip=True))


def _extract_headings_h2_h3(soup: BeautifulSoup) -> list[str]:
    """Extract all H2 and H3 headings as normalized text."""
    headings: list[str] = []

    for tag in soup.find_all(["h2", "h3"]):
        heading_text = _normalize_text(tag.get_text(" ", strip=True))
        if heading_text:
            headings.append(heading_text)

    return headings


def _extract_introduction(soup: BeautifulSoup) -> str:
    """Extract the introduction as the text before the first H2."""
    introduction_parts: list[str] = []

    for element in soup.contents:
        if getattr(element, "name", None) == "h2":
            break

        if getattr(element, "name", None) in {"p", "ul", "ol", "blockquote"}:
            text = _normalize_text(element.get_text(" ", strip=True))
            if text:
                introduction_parts.append(text)

    return _normalize_text(" ".join(introduction_parts))


def _extract_conclusion(soup: BeautifulSoup) -> str:
    """Extract the conclusion text from the H2 titled 'Conclusion' when present.

    Fallback:
    - if no explicit conclusion heading exists, use the last H2 section
      excluding common trailing utility sections such as 'Lecture complémentaire'
      or 'Learn more' when possible.
    """
    h2_tags = soup.find_all("h2")
    if not h2_tags:
        return ""

    def _collect_section_text(start_h2: BeautifulSoup) -> str:
        conclusion_parts: list[str] = []

        for sibling in start_h2.next_siblings:
            if getattr(sibling, "name", None) == "h2":
                break

            if getattr(sibling, "name", None) in {"p", "ul", "ol", "blockquote"}:
                text = _normalize_text(sibling.get_text(" ", strip=True))
                if text:
                    conclusion_parts.append(text)

        return _normalize_text(" ".join(conclusion_parts))

    # Preferred case: explicit "Conclusion" heading
    for h2 in h2_tags:
        heading_text = _normalize_for_matching(h2.get_text(" ", strip=True))
        if heading_text == "conclusion":
            return _collect_section_text(h2)

    # Fallback: ignore common utility trailing sections if present
    excluded_titles = {
        "lecture complementaire",
        "lecture complémentaire",
        "learn more",
    }

    candidate_h2_tags = [
        h2
        for h2 in h2_tags
        if _normalize_for_matching(h2.get_text(" ", strip=True)) not in excluded_titles
    ]

    if candidate_h2_tags:
        return _collect_section_text(candidate_h2_tags[-1])

    # Final fallback: original last H2 behavior
    return _collect_section_text(h2_tags[-1])


def _extract_h2_sections(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Extract sections starting from each H2 until the next H2."""
    sections: list[dict[str, Any]] = []

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
            },
        )

    return sections


def _normalize_for_matching(text: str) -> str:
    """Normalize text for lexical keyword matching."""
    normalized = html.unescape(text).lower()
    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", normalized).strip()


# ***************** Lexical *****************#
def _count_exact_phrase_occurrences(text: str, phrase: str) -> int:
    """Count exact phrase occurrences with word-boundary style protection."""
    normalized_text = _normalize_for_matching(text)
    normalized_phrase = _normalize_for_matching(phrase)

    if not normalized_text or not normalized_phrase:
        return 0

    pattern = re.compile(rf"(?<!\w){re.escape(normalized_phrase)}(?!\w)")
    return len(pattern.findall(normalized_text))


def _is_keyword_present(text: str, keyword: str) -> bool:
    """Return whether a keyword appears in a text."""
    return _count_exact_phrase_occurrences(text, keyword) > 0


def _build_keyword_occurrence_map(
    body_text: str,
    secondary_keywords: list[str],
    long_tail_keywords: list[str],
) -> dict[str, dict[str, int]]:
    """Build per-keyword occurrence maps for secondary and long-tail keywords."""
    secondary_map = {
        keyword: _count_exact_phrase_occurrences(body_text, keyword)
        for keyword in secondary_keywords
    }
    long_tail_map = {
        keyword: _count_exact_phrase_occurrences(body_text, keyword)
        for keyword in long_tail_keywords
    }

    return {
        "secondary_keywords": secondary_map,
        "long_tail_keywords": long_tail_map,
    }


def _is_utility_section(title: str) -> bool:
    """Return whether an H2 title corresponds to a utility/non-SEO section."""
    normalized_title = _normalize_for_matching(title)

    utility_titles = {
        "lecture complementaire",
        "lecture complémentaire",
        "learn more",
        "sources",
        "references",
        "pour aller plus loin",
        "further reading",
    }

    return normalized_title in utility_titles


def _build_section_keyword_distribution(
    h2_sections: list[dict[str, Any]],
    secondary_keywords: list[str],
    long_tail_keywords: list[str],
) -> list[dict[str, Any]]:
    """Count secondary and long-tail keyword presence by eligible H2 section."""
    section_distribution: list[dict[str, Any]] = []

    tracked_keywords = secondary_keywords + long_tail_keywords

    for section in h2_sections:
        section_title = str(section.get("h2", ""))

        if _is_utility_section(section_title):
            continue

        section_text = str(section.get("text", ""))
        keyword_counts = {
            keyword: _count_exact_phrase_occurrences(section_text, keyword)
            for keyword in tracked_keywords
        }

        matched_keywords = [
            keyword for keyword, count in keyword_counts.items() if count > 0
        ]

        section_distribution.append(
            {
                "h2": section_title,
                "keyword_counts": keyword_counts,
                "matched_keywords": matched_keywords,
                "has_secondary_or_long_tail": len(matched_keywords) > 0,
            },
        )

    return section_distribution


def _detect_single_section_concentration(
    section_distribution: list[dict[str, Any]],
) -> bool:
    """Detect whether matched secondary/long-tail keywords sit in one H2."""
    matched_sections = [
        section
        for section in section_distribution
        if section.get("has_secondary_or_long_tail", False)
    ]
    return len(matched_sections) == 1 and len(section_distribution) > 1


def _detect_forbidden_keyword_emphasis(
    soup: BeautifulSoup,
    keywords: list[str],
    forbidden_tags: list[str],
) -> list[dict[str, str]]:
    """Detect forbidden emphasis tags containing tracked keywords."""
    matches: list[dict[str, str]] = []

    for tag_name in forbidden_tags:
        for tag in soup.find_all(tag_name):
            tag_text = _normalize_text(tag.get_text(" ", strip=True))
            matches.extend(
                {
                    "tag": tag_name,
                    "keyword": keyword,
                    "text": tag_text,
                }
                for keyword in keywords
                if _is_keyword_present(tag_text, keyword)
            )

    return matches


# ***************** Semantic *****************#

SEMANTIC_CHUNK_SIZE = settings.seo_chunk_size
SEMANTIC_CHUNK_OVERLAP = settings.seo_chunk_overlap


def _build_semantic_body_text(
    introduction: str,
    h2_sections: list[dict[str, Any]],
    body_text: str,
) -> str:
    """Build a cleaner semantic body text by excluding utility sections."""
    parts: list[str] = []

    if introduction:
        parts.append(_normalize_text(introduction))

    for section in h2_sections:
        section_title = _normalize_text(str(section.get("h2", "")))
        section_text = _normalize_text(str(section.get("text", "")))

        if not section_text:
            continue

        if _is_utility_section(section_title):
            continue

        if section_title:
            parts.append(f"{section_title}. {section_text}")
        else:
            parts.append(section_text)

    semantic_body_text = _normalize_text(" ".join(parts))

    if semantic_body_text:
        return semantic_body_text

    return _normalize_text(body_text)


def _split_text_into_words(text: str) -> list[str]:
    """Split normalized text into words."""
    normalized_text = _normalize_text(text)
    return normalized_text.split() if normalized_text else []


def _build_semantic_chunks(
    body_text: str,
    chunk_size: int = SEMANTIC_CHUNK_SIZE,
    overlap: int = SEMANTIC_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    """Split body text into overlapping chunks for semantic retrieval."""
    words = _split_text_into_words(body_text)

    if not words:
        return []

    if chunk_size <= 0:
        raise ConfigurationError("chunk_size must be greater than 0.")

    if overlap < 0:
        raise ConfigurationError("overlap must be greater than or equal to 0.")

    if overlap >= chunk_size:
        raise ConfigurationError("overlap must be smaller than chunk_size.")

    chunks: list[dict[str, Any]] = []
    step = chunk_size - overlap
    start = 0
    chunk_id = 1

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]

        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": " ".join(chunk_words),
                "start_word": start,
                "end_word": end,
                "word_count": len(chunk_words),
            },
        )

        if end == len(words):
            break

        start += step
        chunk_id += 1

    return chunks


def _build_semantic_inputs(
    main_keyword: str,
    body_text: str,
) -> dict[str, Any]:
    """Build semantic inputs for main-keyword-to-chunks retrieval."""
    return {
        "main_keyword": _normalize_text(main_keyword),
        "chunk_size": SEMANTIC_CHUNK_SIZE,
        "chunk_overlap": SEMANTIC_CHUNK_OVERLAP,
        "chunks": _build_semantic_chunks(body_text),
    }


# ***************** Overoptimization *****************#


def _split_text_into_sentences(text: str) -> list[str]:
    """Split text into simple sentence-like units."""
    normalized_text = _normalize_text(text)

    if not normalized_text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", normalized_text)

    return [sentence.strip() for sentence in sentences if sentence.strip()]


def _build_overoptimization_paragraphs(
    main_keyword: str,
    introduction: str,
    h2_sections: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build local paragraphs used for semantic over-optimization analysis."""
    paragraphs: list[dict[str, Any]] = []
    paragraph_id = 1

    if introduction:
        sentences = [
            {
                "sentence_id": index,
                "text": sentence,
                "exact_main_keyword_match": _is_keyword_present(
                    sentence,
                    main_keyword,
                ),
            }
            for index, sentence in enumerate(
                _split_text_into_sentences(introduction),
                start=1,
            )
        ]

        paragraphs.append(
            {
                "paragraph_id": paragraph_id,
                "section": "introduction",
                "text": _normalize_text(introduction),
                "sentences": sentences,
                "word_count": len(_split_text_into_words(introduction)),
            },
        )
        paragraph_id += 1

    for section in h2_sections:
        section_title = _normalize_text(str(section.get("h2", "")))
        section_text = _normalize_text(str(section.get("text", "")))

        if not section_text:
            continue

        if _is_utility_section(section_title):
            continue

        sentences = [
            {
                "sentence_id": index,
                "text": sentence,
                "exact_main_keyword_match": _is_keyword_present(
                    sentence,
                    main_keyword,
                ),
            }
            for index, sentence in enumerate(
                _split_text_into_sentences(section_text),
                start=1,
            )
        ]

        paragraphs.append(
            {
                "paragraph_id": paragraph_id,
                "section": section_title,
                "text": section_text,
                "sentences": sentences,
                "word_count": len(_split_text_into_words(section_text)),
            },
        )
        paragraph_id += 1

    return paragraphs


def _build_overoptimization_inputs(
    main_keyword: str,
    introduction: str,
    h2_sections: list[dict[str, Any]],
    body_text: str,
) -> dict[str, Any]:
    """Build inputs for local semantic over-optimization analysis."""
    paragraphs = _build_overoptimization_paragraphs(
        main_keyword=main_keyword,
        introduction=introduction,
        h2_sections=h2_sections,
    )

    total_words = sum(int(paragraph["word_count"]) for paragraph in paragraphs)

    if total_words == 0:
        total_words = len(_split_text_into_words(body_text))

    return {
        "main_keyword": _normalize_text(main_keyword),
        "total_words": total_words,
        "paragraphs": paragraphs,
    }


def preprocess_seo_content(
    content: str,
    judge_rules: dict[str, Any],
) -> dict[str, Any]:
    """Prepare content by extracting SEO structural and lexical signals."""
    soup = BeautifulSoup(content, "html.parser")

    introduction = _extract_introduction(soup)
    headings_h2_h3 = _extract_headings_h2_h3(soup)
    body_text = _extract_body_text(soup)
    h2_sections = _extract_h2_sections(soup)
    conclusion = _extract_conclusion(soup)

    main_keyword = str(judge_rules["main_keyword"])
    secondary_keywords = list(judge_rules.get("secondary_keywords", []))
    long_tail_keywords = list(judge_rules.get("long_tail_keywords", []))

    tracked_keywords = [main_keyword, *secondary_keywords, *long_tail_keywords]

    main_keyword_presence = {
        "body": _is_keyword_present(body_text, main_keyword),
        "introduction": _is_keyword_present(introduction, main_keyword),
        "headings_h2_h3": any(
            _is_keyword_present(heading, main_keyword) for heading in headings_h2_h3
        ),
        "conclusion": _is_keyword_present(conclusion, main_keyword),
    }

    main_keyword_occurrences = {
        "body": _count_exact_phrase_occurrences(body_text, main_keyword),
        "introduction": _count_exact_phrase_occurrences(introduction, main_keyword),
        "headings_h2_h3_total": sum(
            _count_exact_phrase_occurrences(heading, main_keyword)
            for heading in headings_h2_h3
        ),
        "conclusion": _count_exact_phrase_occurrences(conclusion, main_keyword),
    }

    keyword_occurrence_map = _build_keyword_occurrence_map(
        body_text=body_text,
        secondary_keywords=secondary_keywords,
        long_tail_keywords=long_tail_keywords,
    )

    section_distribution = _build_section_keyword_distribution(
        h2_sections=h2_sections,
        secondary_keywords=secondary_keywords,
        long_tail_keywords=long_tail_keywords,
    )

    formatting_constraints = judge_rules.get("formatting_constraints_rules", {})
    forbidden_tags = list(
        formatting_constraints.get("forbid_emphasis_tags_on_keywords", []),
    )

    forbidden_keyword_emphasis = _detect_forbidden_keyword_emphasis(
        soup=soup,
        keywords=tracked_keywords,
        forbidden_tags=forbidden_tags,
    )

    semantic_body_text = _build_semantic_body_text(
        introduction=introduction,
        h2_sections=h2_sections,
        body_text=body_text,
    )

    semantic_inputs = _build_semantic_inputs(
        main_keyword=main_keyword,
        body_text=semantic_body_text,
    )

    overoptimization_inputs = _build_overoptimization_inputs(
        main_keyword=main_keyword,
        introduction=introduction,
        h2_sections=h2_sections,
        body_text=body_text,
    )

    return {
        "original_content": content,
        "introduction": introduction,
        "headings_h2_h3": headings_h2_h3,
        "body_text": body_text,
        "h2_sections": h2_sections,
        "conclusion": conclusion,
        "is_empty": body_text == "",
        "lexical_signals": {
            "main_keyword": main_keyword,
            "main_keyword_presence": main_keyword_presence,
            "main_keyword_occurrences": main_keyword_occurrences,
            "secondary_keyword_occurrences": keyword_occurrence_map[
                "secondary_keywords"
            ],
            "long_tail_keyword_occurrences": keyword_occurrence_map[
                "long_tail_keywords"
            ],
            "section_distribution": section_distribution,
            "single_section_concentration_detected": (
                _detect_single_section_concentration(section_distribution)
            ),
            "forbidden_keyword_emphasis": forbidden_keyword_emphasis,
        },
        "semantic_body_text": semantic_body_text,
        "semantic_inputs": semantic_inputs,
        "overoptimization_inputs": overoptimization_inputs,
    }

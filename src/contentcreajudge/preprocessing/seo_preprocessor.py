"""Preprocessing utilities for the SEO judge."""

from __future__ import annotations

import html
import re
from typing import Any

from bs4 import BeautifulSoup
from nltk.corpus import stopwords
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from spacy.language import Language
from spacy.tokens import Doc, Span

_spacy_model: Language | None = None
_keyphrase_embedding_model: SentenceTransformer | None = None


def _get_spacy_model() -> Language:
    global _spacy_model
    if _spacy_model is None:
        try:
            _spacy_model = spacy.load("fr_core_news_sm")
        except OSError:
            _spacy_model = spacy.blank("fr")
    return _spacy_model

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
            }
        )

    return sections


def _normalize_for_matching(text: str) -> str:
    """Normalize text for lexical keyword matching."""
    normalized = html.unescape(text).lower()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

#***************** Lexical *****************#
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
            }
        )

    return section_distribution


def _detect_single_section_concentration(
    section_distribution: list[dict[str, Any]],
) -> bool:
    """Detect whether all matched secondary/long-tail keywords are concentrated in a single H2 section."""
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
            for keyword in keywords:
                if _is_keyword_present(tag_text, keyword):
                    matches.append(
                        {
                            "tag": tag_name,
                            "keyword": keyword,
                            "text": tag_text,
                        }
                    )

    return matches

#***************** Semantic *****************#
def _build_query_input(text: str) -> str:
    """Build an E5 query-formatted input."""
    normalized_text = _normalize_text(text)
    return f"query: {normalized_text}" if normalized_text else "query:"


def _build_passage_input(text: str) -> str:
    """Build an E5 passage-formatted input."""
    normalized_text = _normalize_text(text)
    return f"passage: {normalized_text}" if normalized_text else "passage:"


def _build_keyword_cluster_query(
    main_keyword: str,
    secondary_keywords: list[str],
) -> str:
    """Build a single semantic query string representing the target keyword cluster."""
    cluster_parts = [main_keyword] + secondary_keywords
    cluster_text = " ".join(part for part in cluster_parts if _normalize_text(part))
    return _build_query_input(cluster_text)


def _build_section_passages(
    h2_sections: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build E5 passage inputs for each H2 section."""
    section_passages: list[dict[str, str]] = []

    for section in h2_sections:
        h2_title = _normalize_text(str(section.get("h2", "")))
        section_text = _normalize_text(str(section.get("text", "")))

        section_passages.append(
            {
                "h2": h2_title,
                "passage": _build_passage_input(section_text),
            }
        )

    return section_passages


def _build_semantic_inputs(
    main_keyword: str,
    secondary_keywords: list[str],
    long_tail_keywords: list[str],
    introduction: str,
    conclusion: str,
    headings_h2_h3: list[str],
    body_text: str,
    h2_sections: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build all semantic inputs needed for the E5 layer."""
    return {
        "main_keyword_query": _build_query_input(main_keyword),
        "secondary_keyword_queries": [
            _build_query_input(keyword) for keyword in secondary_keywords
        ],
        "long_tail_keyword_queries": [
            _build_query_input(keyword) for keyword in long_tail_keywords
        ],
        "keyword_cluster_query": _build_keyword_cluster_query(
            main_keyword=main_keyword,
            secondary_keywords=secondary_keywords,
        ),
        "introduction_passage": _build_passage_input(introduction),
        "conclusion_passage": _build_passage_input(conclusion),
        "heading_passages": [
            _build_passage_input(heading) for heading in headings_h2_h3
        ],
        "body_passage": _build_passage_input(body_text),
        "section_passages": _build_section_passages(h2_sections),
    }

#***************** Thematic *****************#
def _get_keyphrase_embedding_model() -> SentenceTransformer:
    """Load the embedding model used to score keyphrase candidates."""
    global _keyphrase_embedding_model
    if _keyphrase_embedding_model is None:
        _keyphrase_embedding_model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2"
        )
    return _keyphrase_embedding_model

NLTK_STOPWORDS = set(stopwords.words("english")) | set(stopwords.words("french"))

CUSTOM_STOPWORDS = {
    "doit",
    "peut",
    "devient",
    "depend",
    "dépend",
    "prend",
    "prennent",
    "demeure",
    "demeurent",
    "becomes",
    "depends",
    "takes",
    "remains",
}

STOPWORDS = NLTK_STOPWORDS | CUSTOM_STOPWORDS

EDGE_NOISE_WORDS = STOPWORDS | {
    "ainsi",
    "alors",
    "comme",
    "lorsque",
    "quand",
}

INVALID_EDGE_POS = {
    "ADP",
    "AUX",
    "CCONJ",
    "DET",
    "PRON",
    "SCONJ",
    "VERB",
}

MIN_KEYPHRASE_WORDS = 2
MAX_KEYPHRASE_WORDS = 4


def _normalize_keyphrase_candidate(keyphrase: str) -> str:
    """Normalize a candidate keyphrase with light edge cleanup."""
    normalized = _normalize_text(keyphrase)
    normalized = re.sub(r"[^\w\s-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    words = normalized.split()

    while words and _normalize_for_matching(words[0]) in EDGE_NOISE_WORDS:
        words.pop(0)

    while words and _normalize_for_matching(words[-1]) in EDGE_NOISE_WORDS:
        words.pop()

    return " ".join(words)


def _is_noisy_keyphrase(keyphrase: str) -> bool:
    """Return whether a keyphrase is too noisy to be useful."""
    normalized = _normalize_for_matching(keyphrase)
    words = normalized.split()

    if len(words) < MIN_KEYPHRASE_WORDS:
        return True

    if words[0] in STOPWORDS or words[-1] in STOPWORDS:
        return True

    return False


def _is_valid_keyphrase_span(span: Span) -> bool:
    """Check whether a spaCy span is a valid candidate keyphrase."""
    tokens = [token for token in span if not token.is_space and not token.is_punct]

    if len(tokens) < MIN_KEYPHRASE_WORDS or len(tokens) > MAX_KEYPHRASE_WORDS:
        return False

    if not any(token.pos_ in {"NOUN", "PROPN"} for token in tokens):
        return False

    if tokens[0].pos_ in INVALID_EDGE_POS or tokens[-1].pos_ in INVALID_EDGE_POS:
        return False

    normalized_candidate = _normalize_keyphrase_candidate(span.text)
    return not _is_noisy_keyphrase(normalized_candidate)


def _extract_candidate_keyphrases(doc: Doc) -> list[str]:
    """Extract grammatical candidate keyphrases from a spaCy doc."""
    candidates: list[str] = []
    seen: set[str] = set()

    def _add_candidate(candidate: str) -> None:
        normalized_candidate = _normalize_keyphrase_candidate(candidate)
        normalized_for_matching = _normalize_for_matching(normalized_candidate)

        if not normalized_candidate:
            return
        if _is_noisy_keyphrase(normalized_candidate):
            return
        if normalized_for_matching in seen:
            return

        seen.add(normalized_for_matching)
        candidates.append(normalized_candidate)

    if doc.has_annotation("DEP"):
        for span in doc.noun_chunks:
            if _is_valid_keyphrase_span(span):
                _add_candidate(span.text)

    if doc.has_annotation("POS"):
        valid_pos = {"ADJ", "NOUN", "PROPN"}

        for start in range(len(doc)):
            for end in range(
                start + MIN_KEYPHRASE_WORDS,
                min(start + MAX_KEYPHRASE_WORDS, len(doc)) + 1,
            ):
                span = doc[start:end]
                tokens = [token for token in span if not token.is_space and not token.is_punct]

                if len(tokens) < MIN_KEYPHRASE_WORDS:
                    continue
                if any(token.pos_ not in valid_pos for token in tokens):
                    continue
                if not _is_valid_keyphrase_span(span):
                    continue

                _add_candidate(span.text)

    # Fallback simple si spaCy est trop pauvre
    if not candidates:
        words = _normalize_text(doc.text).split()

        for start in range(len(words)):
            for end in range(
                start + MIN_KEYPHRASE_WORDS,
                min(start + MAX_KEYPHRASE_WORDS, len(words)) + 1,
            ):
                candidate = _normalize_keyphrase_candidate(" ".join(words[start:end]))
                normalized_candidate = _normalize_for_matching(candidate)

                if not candidate:
                    continue
                if _is_noisy_keyphrase(candidate):
                    continue
                if normalized_candidate in seen:
                    continue

                seen.add(normalized_candidate)
                candidates.append(candidate)

    return candidates


def _score_candidate_keyphrases(
    text: str,
    candidates: list[str],
    top_n: int = 10,
) -> list[dict[str, float]]:
    """Score candidate keyphrases against the full document embedding."""
    if not text.strip() or not candidates:
        return []

    model = _get_keyphrase_embedding_model()
    normalized_text = _normalize_text(text)

    embeddings = model.encode(
        [normalized_text, *candidates],
        normalize_embeddings=True,
    )
    document_embedding = embeddings[0]
    candidate_embeddings = embeddings[1:]

    similarities = cosine_similarity([document_embedding], candidate_embeddings)[0]

    ranked_candidates = sorted(
        zip(candidates, similarities, strict=False),
        key=lambda item: item[1],
        reverse=True,
    )[:top_n]

    return [
        {"keyphrase": phrase, "score": float(score)}
        for phrase, score in ranked_candidates
    ]


def _filter_keyphrases(
    keyphrases: list[dict[str, float]],
    min_score: float = 0.3,
) -> list[dict[str, float]]:
    """Filter keyphrases based on a minimum score."""
    return [
        kp for kp in keyphrases
        if kp["score"] >= min_score
    ]


def _deduplicate_keyphrases(
    keyphrases: list[dict[str, float]],
) -> list[dict[str, float]]:
    """Remove exact duplicates while keeping the first occurrence."""
    seen: set[str] = set()
    deduplicated: list[dict[str, float]] = []

    for kp in keyphrases:
        normalized_phrase = _normalize_for_matching(str(kp["keyphrase"]))
        if normalized_phrase in seen:
            continue
        seen.add(normalized_phrase)
        deduplicated.append(kp)

    return deduplicated


def _clean_keyphrases(
    keyphrases: list[dict[str, float]],
) -> list[dict[str, float]]:
    """Apply final cleanup and deduplication to scored keyphrases."""
    cleaned: list[dict[str, float]] = []

    for kp in keyphrases:
        normalized_phrase = _normalize_keyphrase_candidate(str(kp["keyphrase"]))

        if not normalized_phrase:
            continue
        if _is_noisy_keyphrase(normalized_phrase):
            continue

        cleaned.append(
            {
                "keyphrase": normalized_phrase,
                "score": float(kp["score"]),
            }
        )

    return _deduplicate_keyphrases(cleaned)


def _extract_keyphrases(
    text: str,
    top_n: int = 10,
) -> list[dict[str, float]]:
    """Extract clean keyphrases using spaCy candidates + embedding scoring."""
    if not text.strip():
        return []

    doc = _get_spacy_model()(_normalize_text(text))
    candidates = _extract_candidate_keyphrases(doc)

    if not candidates:
        return []

    scored_candidates = _score_candidate_keyphrases(
        text=text,
        candidates=candidates,
        top_n=top_n,
    )

    filtered_candidates = _filter_keyphrases(scored_candidates)
    return _clean_keyphrases(filtered_candidates)


def preprocess_seo_content(
    content: str,
    judge_rules: dict[str, Any],
) -> dict[str, Any]:
    """Prepare the content for SEO evaluation by extracting structural and lexical signals."""
    soup = BeautifulSoup(content, "html.parser")

    introduction = _extract_introduction(soup)
    headings_h2_h3 = _extract_headings_h2_h3(soup)
    body_text = _extract_body_text(soup)
    h2_sections = _extract_h2_sections(soup)
    conclusion = _extract_conclusion(soup)

    main_keyword = str(judge_rules["main_keyword"])
    secondary_keywords = list(judge_rules.get("secondary_keywords", []))
    long_tail_keywords = list(judge_rules.get("long_tail_keywords", []))

    tracked_keywords = [main_keyword] + secondary_keywords + long_tail_keywords

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
        formatting_constraints.get("forbid_emphasis_tags_on_keywords", [])
    )

    forbidden_keyword_emphasis = _detect_forbidden_keyword_emphasis(
        soup=soup,
        keywords=tracked_keywords,
        forbidden_tags=forbidden_tags,
    )

    semantic_inputs = _build_semantic_inputs(
        main_keyword=main_keyword,
        secondary_keywords=secondary_keywords,
        long_tail_keywords=long_tail_keywords,
        introduction=introduction,
        conclusion=conclusion,
        headings_h2_h3=headings_h2_h3,
        body_text=body_text,
        h2_sections=h2_sections,
    )

    thematic_keyphrases = _extract_keyphrases(body_text)

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
            "secondary_keyword_occurrences": keyword_occurrence_map["secondary_keywords"],
            "long_tail_keyword_occurrences": keyword_occurrence_map["long_tail_keywords"],
            "section_distribution": section_distribution,
            "single_section_concentration_detected": _detect_single_section_concentration(
                section_distribution
            ),
            "forbidden_keyword_emphasis": forbidden_keyword_emphasis,
        },
        "semantic_inputs": semantic_inputs,
        "thematic_signals": {
            "keyphrases": thematic_keyphrases
        },
    }

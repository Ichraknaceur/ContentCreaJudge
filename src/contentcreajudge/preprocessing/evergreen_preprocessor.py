"""Preprocessing utilities for the evergreen judge."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import TypedDict

from bs4 import BeautifulSoup


class EvergreenTemporalReference(TypedDict):
    """Temporal reference detected in evergreen preprocessing."""

    value: str
    type: str
    start: int
    end: int
    context: str
    is_in_source_context: bool
    is_historical_context: bool
    is_in_input: bool


class EvergreenPreprocessingResult(TypedDict):
    """Preprocessed content and temporal signals for the evergreen judge."""

    original_content: str
    normalized_text: str
    locale_key: str
    temporal_references: list[EvergreenTemporalReference]
    temporal_references_count: int
    is_empty: bool


YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
FULL_DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-](?:19|20)\d{2}\b")

MONTHS_FR = [
    "janvier",
    "février",
    "fevrier",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "aout",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
    "decembre",
]

MONTHS_EN = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


@dataclass(frozen=True)
class _ReferenceBuildContext:
    text: str
    judge_rules: dict[str, object]
    locale_key: str
    anchor_texts: list[str]


def _normalize_text(content: str | None) -> str:
    if not content:
        return ""

    text_without_html = re.sub(r"<[^>]+>", " ", content)
    decoded_text = html.unescape(text_without_html)
    return re.sub(r"\s+", " ", decoded_text).strip()


def _extract_anchor_texts(content: str | None) -> list[str]:
    """Extract anchor texts before HTML is removed."""
    if not content:
        return []

    soup = BeautifulSoup(content, "html.parser")
    return [
        html.unescape(anchor.get_text(" ", strip=True)) for anchor in soup.find_all("a")
    ]


def _is_in_anchor_text(value: str, anchor_texts: list[str]) -> bool:
    """Check whether the detected temporal value belongs to an anchor text."""
    normalized_value = value.lower()

    return any(normalized_value in anchor_text.lower() for anchor_text in anchor_texts)


def _get_locale_key(locale: str | None) -> str:
    if not locale:
        return "fr"

    if locale.lower().startswith("en"):
        return "en"

    return "fr"


def _get_context_window(text: str, start: int, end: int, window: int = 80) -> str:
    safe_start = max(0, start - window)
    safe_end = min(len(text), end + window)
    return text[safe_start:safe_end].strip()


def _as_str_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item) for item in value if item is not None]


def _get_nested_str_list(
    data: dict[str, object],
    first_key: str,
    second_key: str,
) -> list[str]:
    first_value = data.get(first_key)

    if not isinstance(first_value, dict):
        return []

    second_value = first_value.get(second_key)
    return _as_str_list(second_value)


def _contains_marker(context: str, markers: list[str]) -> bool:
    normalized_context = context.lower()
    return any(marker.lower() in normalized_context for marker in markers if marker)


def _get_context_markers(
    judge_rules: dict[str, object],
    marker_group: str,
    locale_key: str,
) -> list[str]:
    context_detection = judge_rules.get("context_detection")

    if not isinstance(context_detection, dict):
        return []

    return _get_nested_str_list(context_detection, marker_group, locale_key)


def _is_in_source_context(
    context: str,
    judge_rules: dict[str, object],
    locale_key: str,
) -> bool:
    markers = _get_context_markers(
        judge_rules=judge_rules,
        marker_group="source_context_markers",
        locale_key=locale_key,
    )
    return _contains_marker(context, markers)


def _is_historical_context(
    context: str,
    judge_rules: dict[str, object],
    locale_key: str,
) -> bool:
    markers = _get_context_markers(
        judge_rules=judge_rules,
        marker_group="historical_context_markers",
        locale_key=locale_key,
    )
    return _contains_marker(context, markers)


def _is_in_allowed_inputs(value: str, judge_rules: dict[str, object]) -> bool:
    allowed_dates = _as_str_list(judge_rules.get("allowed_dates"))
    allowed_refs = _as_str_list(judge_rules.get("allowed_temporal_references"))

    allowed_values = [item.lower() for item in allowed_dates + allowed_refs]
    return value.lower() in allowed_values


def _build_reference(
    value: str,
    reference_type: str,
    start: int,
    end: int,
    build_context: _ReferenceBuildContext,
) -> EvergreenTemporalReference:
    text = build_context.text
    context = _get_context_window(text, start, end)
    judge_rules = build_context.judge_rules
    locale_key = build_context.locale_key

    return {
        "value": value,
        "type": reference_type,
        "start": start,
        "end": end,
        "context": context,
        "is_in_source_context": (
            _is_in_source_context(context, judge_rules, locale_key)
            or _is_in_anchor_text(value, build_context.anchor_texts)
        ),
        "is_historical_context": _is_historical_context(
            context,
            judge_rules,
            locale_key,
        ),
        "is_in_input": _is_in_allowed_inputs(value, judge_rules),
    }


def _extract_years_and_full_dates(
    text: str,
    judge_rules: dict[str, object],
    locale_key: str,
    anchor_texts: list[str],
) -> list[EvergreenTemporalReference]:
    build_context = _ReferenceBuildContext(
        text=text,
        judge_rules=judge_rules,
        locale_key=locale_key,
        anchor_texts=anchor_texts,
    )

    references = [
        _build_reference(
            match.group(),
            "full_date",
            match.start(),
            match.end(),
            build_context,
        )
        for match in FULL_DATE_PATTERN.finditer(text)
    ]

    references.extend(
        [
            _build_reference(
                match.group(),
                "year",
                match.start(),
                match.end(),
                build_context,
            )
            for match in YEAR_PATTERN.finditer(text)
        ],
    )

    return references


def _extract_month_years(
    text: str,
    judge_rules: dict[str, object],
    locale_key: str,
    anchor_texts: list[str],
) -> list[EvergreenTemporalReference]:
    months = MONTHS_EN if locale_key == "en" else MONTHS_FR
    month_pattern = "|".join(re.escape(month) for month in months)

    pattern = re.compile(
        rf"\b(?:{month_pattern})\s+(?:19|20)\d{{2}}\b",
        flags=re.IGNORECASE,
    )

    build_context = _ReferenceBuildContext(
        text=text,
        judge_rules=judge_rules,
        locale_key=locale_key,
        anchor_texts=anchor_texts,
    )

    return [
        _build_reference(
            match.group(),
            "month_year",
            match.start(),
            match.end(),
            build_context,
        )
        for match in pattern.finditer(text)
    ]


def _extract_configured_expressions(
    text: str,
    judge_rules: dict[str, object],
    locale_key: str,
    anchor_texts: list[str],
    category: tuple[str, str],
) -> list[EvergreenTemporalReference]:
    categories = judge_rules.get("temporal_expression_categories")

    if not isinstance(categories, dict):
        return []

    category_name, reference_type = category
    expressions = _get_nested_str_list(categories, category_name, locale_key)
    build_context = _ReferenceBuildContext(
        text=text,
        judge_rules=judge_rules,
        locale_key=locale_key,
        anchor_texts=anchor_texts,
    )

    references: list[EvergreenTemporalReference] = []

    for expression in expressions:
        expression_text = expression.strip()

        if not expression_text:
            continue

        pattern = re.compile(rf"\b{re.escape(expression_text)}\b", re.IGNORECASE)
        references.extend(
            [
                _build_reference(
                    match.group(),
                    reference_type,
                    match.start(),
                    match.end(),
                    build_context,
                )
                for match in pattern.finditer(text)
            ],
        )

    return references


def preprocess_evergreen_content(
    content: str | None,
    judge_rules: dict[str, object] | None,
) -> EvergreenPreprocessingResult:
    """Prepare content for evergreen evaluation."""
    safe_rules = judge_rules or {}
    locale_key = _get_locale_key(str(safe_rules.get("locale", "fr-FR")))
    anchor_texts = _extract_anchor_texts(content)
    normalized_text = _normalize_text(content)

    temporal_references: list[EvergreenTemporalReference] = []
    temporal_references.extend(
        _extract_years_and_full_dates(
            normalized_text,
            safe_rules,
            locale_key,
            anchor_texts,
        ),
    )
    temporal_references.extend(
        _extract_month_years(
            normalized_text,
            safe_rules,
            locale_key,
            anchor_texts,
        ),
    )
    temporal_references.extend(
        _extract_configured_expressions(
            normalized_text,
            safe_rules,
            locale_key,
            anchor_texts,
            ("relative_dates", "relative_date"),
        ),
    )
    temporal_references.extend(
        _extract_configured_expressions(
            normalized_text,
            safe_rules,
            locale_key,
            anchor_texts,
            ("news_references", "news_reference"),
        ),
    )
    temporal_references.extend(
        _extract_configured_expressions(
            normalized_text,
            safe_rules,
            locale_key,
            anchor_texts,
            ("version_references", "version_reference"),
        ),
    )

    return {
        "original_content": content or "",
        "normalized_text": normalized_text,
        "locale_key": locale_key,
        "temporal_references": temporal_references,
        "temporal_references_count": len(temporal_references),
        "is_empty": normalized_text == "",
    }

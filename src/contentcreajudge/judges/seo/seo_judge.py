"""Judge logic for SEO evaluation."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from sentence_transformers import SentenceTransformer
from sentence_transformers import util as st_util

_semantic_model: SentenceTransformer | None = None

SEMANTIC_THRESHOLDS = {
    "main_keyword_to_introduction": 0.82,
    "main_keyword_to_headings": 0.82,
    "main_keyword_to_conclusion": 0.82,
    "keyword_cluster_to_body": 0.84,
}

THEMATIC_THRESHOLDS = {
    "minimum_coverage_ratio": 0.40,
    "minimum_distinct_keyphrases": 3,
}

EXCLUDED_HEADING_TITLES = {
    "conclusion",
    "sources",
    "references",
    "learn more",
    "lecture complementaire",
    "lecture complémentaire",
    "pour aller plus loin",
    "further reading",
}


def _build_finding(
    rule_id: str,
    severity: str,
    message: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Build a structured finding."""
    return {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def _get_rule_severity(rules: list[dict[str, Any]], rule_id: str) -> str:
    """Return the configured severity for a rule_id."""
    for rule in rules:
        if rule.get("rule_id") == rule_id:
            return str(rule.get("severity", "minor"))
    return "minor"


def _get_semantic_model() -> SentenceTransformer:
    """Load the embedding model used for semantic SEO checks."""
    global _semantic_model
    if _semantic_model is None:
        _semantic_model = SentenceTransformer("intfloat/multilingual-e5-base")
    return _semantic_model


def _semantic_similarity(query_text: str, passage_text: str) -> float:
    """Compute cosine similarity between a query-formatted text and a passage-formatted text."""
    model = _get_semantic_model()

    embeddings = model.encode(
        [query_text, passage_text],
        convert_to_tensor=True,
        normalize_embeddings=True,
    )
    similarity = st_util.cos_sim(embeddings[0], embeddings[1]).item()
    return float(similarity)


def _normalize_heading_title(heading_passage: str) -> str:
    """Return normalized heading text from a passage-formatted input."""
    heading_text = heading_passage.replace("passage: ", "", 1)
    return heading_text.strip().lower()


def _is_conclusion_title(title: str) -> bool:
    """Return whether a section title is a conclusion heading."""
    return title.strip().lower() == "conclusion"


def _compute_semantic_signals(
    semantic_inputs: dict[str, Any],
) -> dict[str, Any]:
    """Compute semantic similarities from prepared E5 inputs."""
    main_keyword_query = str(semantic_inputs["main_keyword_query"])
    keyword_cluster_query = str(semantic_inputs["keyword_cluster_query"])
    introduction_passage = str(semantic_inputs["introduction_passage"])
    conclusion_passage = str(semantic_inputs["conclusion_passage"])
    body_passage = str(semantic_inputs["body_passage"])
    heading_passages = [
        str(heading_passage)
        for heading_passage in semantic_inputs.get("heading_passages", [])
        if _normalize_heading_title(str(heading_passage)) not in EXCLUDED_HEADING_TITLES
    ]

    introduction_similarity = _semantic_similarity(
        main_keyword_query,
        introduction_passage,
    )
    conclusion_similarity = _semantic_similarity(
        main_keyword_query,
        conclusion_passage,
    )
    body_similarity = _semantic_similarity(
        keyword_cluster_query,
        body_passage,
    )

    heading_similarities = [
        {
            "heading": heading_passage.replace("passage: ", "", 1),
            "similarity": _semantic_similarity(main_keyword_query, heading_passage),
        }
        for heading_passage in heading_passages
    ]

    best_heading_similarity = (
        max(item["similarity"] for item in heading_similarities)
        if heading_similarities
        else 0.0
    )

    return {
        "main_keyword_to_introduction": introduction_similarity,
        "main_keyword_to_conclusion": conclusion_similarity,
        "keyword_cluster_to_body": body_similarity,
        "heading_similarities": heading_similarities,
        "best_main_keyword_to_heading": best_heading_similarity,
    }


def _compute_semantic_compensation(
    semantic_signals: dict[str, Any],
) -> dict[str, bool]:
    """Determine whether strong semantic alignment compensates lexical rigidity."""
    return {
        "introduction_compensated": (
            semantic_signals["main_keyword_to_introduction"]
            >= SEMANTIC_THRESHOLDS["main_keyword_to_introduction"]
        ),
        "heading_compensated": (
            semantic_signals["best_main_keyword_to_heading"]
            >= SEMANTIC_THRESHOLDS["main_keyword_to_headings"]
        ),
        "conclusion_compensated": (
            semantic_signals["main_keyword_to_conclusion"]
            >= SEMANTIC_THRESHOLDS["main_keyword_to_conclusion"]
        ),
        "body_compensated": (
            semantic_signals["keyword_cluster_to_body"]
            >= SEMANTIC_THRESHOLDS["keyword_cluster_to_body"]
        ),
    }


#********Thematic********#
def _normalize_theme_text(text: str) -> str:
    """Normalize text for thematic matching."""
    normalized = str(text).lower()
    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(
        char for char in normalized
        if unicodedata.category(char) != "Mn"
    )
    normalized = normalized.replace("’", " ").replace("'", " ")
    normalized = re.sub(r"[^\w\s-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _build_expected_themes(lexical_signals: dict[str, Any]) -> list[str]:
    """Build expected themes from main, secondary and long-tail keywords."""
    themes: list[str] = []

    main_keyword = lexical_signals.get("main_keyword")
    if main_keyword:
        themes.append(str(main_keyword))

    themes.extend(
        str(keyword)
        for keyword in lexical_signals.get(
            "secondary_keyword_occurrences", {}
        ).keys()
    )
    themes.extend(
        str(keyword)
        for keyword in lexical_signals.get(
            "long_tail_keyword_occurrences", {}
        ).keys()
    )

    return [theme for theme in themes if _normalize_theme_text(theme)]


def _theme_matches_keyphrase(expected_theme: str, keyphrase: str) -> bool:
    """Return whether an expected theme is covered by an extracted keyphrase."""
    expected = _normalize_theme_text(expected_theme)
    extracted = _normalize_theme_text(keyphrase)

    if not expected or not extracted:
        return False

    if expected in extracted or extracted in expected:
        return True

    expected_tokens = set(expected.split())
    extracted_tokens = set(extracted.split())

    if not expected_tokens:
        return False

    overlap_ratio = len(expected_tokens & extracted_tokens) / len(expected_tokens)

    return overlap_ratio >= 0.6


def _compute_thematic_signals(
    lexical_signals: dict[str, Any],
    thematic_inputs: dict[str, Any],
    body_text: str,
) -> dict[str, Any]:
    """Compute thematic coverage from extracted keyphrases and full body text."""
    expected_themes = _build_expected_themes(lexical_signals)
    keyphrases = list(thematic_inputs.get("keyphrases", []))

    extracted_keyphrases = [
        str(item.get("keyphrase", ""))
        for item in keyphrases
        if isinstance(item, dict) and item.get("keyphrase")
    ]

    normalized_body = _normalize_theme_text(body_text)

    matched_themes: list[str] = []
    missing_themes: list[str] = []

    for theme in expected_themes:
        normalized_theme = _normalize_theme_text(theme)

        matched_in_body = normalized_theme in normalized_body
        matched_in_keyphrases = any(
            _theme_matches_keyphrase(theme, keyphrase)
            for keyphrase in extracted_keyphrases
        )

        if matched_in_body or matched_in_keyphrases:
            matched_themes.append(theme)
        else:
            missing_themes.append(theme)

    coverage_ratio = (
        len(matched_themes) / len(expected_themes)
        if expected_themes
        else 1.0
    )

    return {
        "expected_themes": expected_themes,
        "extracted_keyphrases": extracted_keyphrases,
        "matched_themes": matched_themes,
        "missing_themes": missing_themes,
        "coverage_ratio": coverage_ratio,
        "distinct_keyphrase_count": len(set(extracted_keyphrases)),
    }


def _compute_thematic_score(thematic_signals: dict[str, Any]) -> int:
    """Compute thematic score from coverage and diversity."""
    thematic_score = round(thematic_signals["coverage_ratio"] * 100)

    if (
        thematic_signals["distinct_keyphrase_count"]
        < THEMATIC_THRESHOLDS["minimum_distinct_keyphrases"]
    ):
        thematic_score = max(thematic_score - 10, 0)

    return thematic_score

#**********The judge**********#
def run_seo_judge(
    preprocessed_content: dict[str, Any],
    judge_rules: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate SEO compliance using lexical signals with semantic compensation."""
    lexical_signals = preprocessed_content["lexical_signals"]
    semantic_inputs = preprocessed_content["semantic_inputs"]
    thematic_inputs = preprocessed_content.get("thematic_signals", {})

    rules = judge_rules["rules"]
    messages = judge_rules["messages"]

    findings: list[dict[str, Any]] = []
    lexical_penalty = 0
    semantic_penalty = 0

    main_keyword = lexical_signals["main_keyword"]
    main_keyword_presence = lexical_signals["main_keyword_presence"]
    main_keyword_occurrences = lexical_signals["main_keyword_occurrences"]
    section_distribution = lexical_signals["section_distribution"]
    single_section_concentration = lexical_signals[
        "single_section_concentration_detected"
    ]
    forbidden_keyword_emphasis = lexical_signals["forbidden_keyword_emphasis"]
    long_tail_occurrences = lexical_signals["long_tail_keyword_occurrences"]

    main_keyword_rules = judge_rules["main_keyword_rules"]
    occurrence_rules = judge_rules["keyword_occurrence_rules"]
    distribution_rules = judge_rules["keyword_distribution_rules"]
    over_optimization_rules = judge_rules["over_optimization_rules"]

    total_occurrences = (
        main_keyword_occurrences["body"]
        + sum(lexical_signals["secondary_keyword_occurrences"].values())
        + sum(lexical_signals["long_tail_keyword_occurrences"].values())
    )
    has_any_keyword_occurrence = total_occurrences > 0
    main_keyword_exact_missing = main_keyword_occurrences["body"] == 0

    semantic_signals = _compute_semantic_signals(semantic_inputs)
    semantic_compensation = _compute_semantic_compensation(semantic_signals)
    thematic_signals = _compute_thematic_signals(
        lexical_signals=lexical_signals,
        thematic_inputs=thematic_inputs,
        body_text=str(preprocessed_content.get("body_text", "")),
    )
    # Guardrail:
    # If no tracked SEO keyword appears at all, semantic similarity must not compensate.
    if not has_any_keyword_occurrence:
        semantic_compensation = {
            "introduction_compensated": False,
            "heading_compensated": False,
            "conclusion_compensated": False,
            "body_compensated": False,
        }

    if (
        main_keyword_rules.get("require_presence", False)
        and not main_keyword_presence["body"]
    ):
        findings.append(
            _build_finding(
                rule_id="seo.main_keyword_presence",
                severity=_get_rule_severity(rules, "seo.main_keyword_presence"),
                message=messages["main_keyword_presence"],
                evidence={
                    "main_keyword": main_keyword,
                    "present_in_body": False,
                    "semantic_body_compensation": semantic_compensation[
                        "body_compensated"
                    ],
                },
            )
        )

        if semantic_compensation["body_compensated"]:
            lexical_penalty += 8
        else:
            lexical_penalty += 25

    required_locations = main_keyword_rules.get("required_locations", {})
    missing_locations: list[str] = []
    compensated_locations: list[str] = []

    if (
        required_locations.get("introduction", False)
        and not main_keyword_presence["introduction"]
    ):
        if semantic_compensation["introduction_compensated"]:
            compensated_locations.append("introduction")
        else:
            missing_locations.append("introduction")

    if (
        required_locations.get("heading_h2_or_h3", False)
        and not main_keyword_presence["headings_h2_h3"]
    ):
        if semantic_compensation["heading_compensated"]:
            compensated_locations.append("heading_h2_or_h3")
        else:
            missing_locations.append("heading_h2_or_h3")

    if (
        required_locations.get("conclusion", False)
        and not main_keyword_presence["conclusion"]
    ):
        if semantic_compensation["conclusion_compensated"]:
            compensated_locations.append("conclusion")
        else:
            missing_locations.append("conclusion")

    if required_locations.get("body", False) and not main_keyword_presence["body"]:
        if semantic_compensation["body_compensated"]:
            compensated_locations.append("body")
        else:
            missing_locations.append("body")

    if missing_locations or compensated_locations:
        findings.append(
            _build_finding(
                rule_id="seo.main_keyword_locations",
                severity=(
                    _get_rule_severity(rules, "seo.main_keyword_locations")
                    if missing_locations
                    else "minor"
                ),
                message=messages["main_keyword_locations"],
                evidence={
                    "main_keyword": main_keyword,
                    "missing_locations": missing_locations,
                    "compensated_locations": compensated_locations,
                },
            )
        )

        if missing_locations:
            lexical_penalty += 20
        elif compensated_locations:
            lexical_penalty += 5

    occurrence_issue = False

    min_total = occurrence_rules.get("min_total")
    max_total = occurrence_rules.get("max_total")
    min_main = occurrence_rules.get("min_main")

    below_min_total = False
    above_max_total = False
    below_min_main = False

    if occurrence_rules.get("enforce_minimum_occurrences", False):
        if min_total is not None and total_occurrences < min_total:
            below_min_total = True
            occurrence_issue = True
        if max_total is not None and total_occurrences > max_total:
            above_max_total = True
            occurrence_issue = True
        if min_main is not None and main_keyword_occurrences["body"] < min_main:
            below_min_main = True
            occurrence_issue = True

    if occurrence_issue:
        occurrence_severity = _get_rule_severity(rules, "seo.keyword_occurrences")

        if (
            semantic_compensation["body_compensated"]
            and not above_max_total
            and (below_min_total or below_min_main)
        ):
            occurrence_severity = "minor"

        findings.append(
            _build_finding(
                rule_id="seo.keyword_occurrences",
                severity=occurrence_severity,
                message=messages["keyword_occurrences"],
                evidence={
                    "main_keyword_occurrences_in_body": main_keyword_occurrences["body"],
                    "total_keyword_occurrences": total_occurrences,
                    "expected_min_total": min_total,
                    "expected_max_total": max_total,
                    "expected_min_main": min_main,
                    "semantic_body_compensation": semantic_compensation[
                        "body_compensated"
                    ],
                },
            )
        )

        if semantic_compensation["body_compensated"]:
            lexical_penalty += 8
        else:
            lexical_penalty += 15

    sections_without_keywords: list[str] = []

    if distribution_rules.get(
        "require_at_least_one_secondary_or_long_tail_per_h2_section",
        False,
    ):
        for section in section_distribution:
            if not section["has_secondary_or_long_tail"]:
                sections_without_keywords.append(str(section["h2"]))

    distribution_issue = bool(sections_without_keywords)
    conclusion_only_distribution_gap = (
        sections_without_keywords
        and all(_is_conclusion_title(section) for section in sections_without_keywords)
    )

    if (
        distribution_rules.get("forbid_single_section_concentration", False)
        and single_section_concentration
    ):
        distribution_issue = True

    if distribution_issue:
        distribution_severity = _get_rule_severity(rules, "seo.keyword_distribution")

        if (
            semantic_compensation["body_compensated"]
            and conclusion_only_distribution_gap
        ):
            distribution_severity = "minor"

        findings.append(
            _build_finding(
                rule_id="seo.keyword_distribution",
                severity=distribution_severity,
                message=messages["keyword_distribution"],
                evidence={
                    "sections_without_secondary_or_long_tail": sections_without_keywords,
                    "single_section_concentration_detected": (
                        single_section_concentration
                    ),
                    "semantic_body_compensation": semantic_compensation[
                        "body_compensated"
                    ],
                },
            )
        )

        if semantic_compensation["body_compensated"]:
            lexical_penalty += 8
        else:
            lexical_penalty += 15

    max_identical_long_tail_occurrences = over_optimization_rules.get(
        "max_identical_long_tail_occurrences"
    )

    repeated_long_tails = {
        keyword: count
        for keyword, count in long_tail_occurrences.items()
        if (
            max_identical_long_tail_occurrences is not None
            and count > max_identical_long_tail_occurrences
        )
    }

    if repeated_long_tails:
        findings.append(
            _build_finding(
                rule_id="seo.over_optimization",
                severity=_get_rule_severity(rules, "seo.over_optimization"),
                message=messages["over_optimization"],
                evidence={
                    "repeated_long_tail_keywords": repeated_long_tails,
                    "max_identical_long_tail_occurrences": (
                        max_identical_long_tail_occurrences
                    ),
                },
            )
        )
        lexical_penalty += 10

    if forbidden_keyword_emphasis:
        findings.append(
            _build_finding(
                rule_id="seo.formatting_constraints",
                severity=_get_rule_severity(rules, "seo.formatting_constraints"),
                message=messages["formatting_constraints"],
                evidence={
                    "matches_count": len(forbidden_keyword_emphasis),
                    "matches": forbidden_keyword_emphasis,
                },
            )
        )
        lexical_penalty += 10

    # Thematic layer
    if (
        thematic_signals["coverage_ratio"]
        < THEMATIC_THRESHOLDS["minimum_coverage_ratio"]
    ):
        findings.append(
            _build_finding(
                rule_id="seo.thematic_coverage",
                severity="major",
                message="The content does not sufficiently cover the expected SEO themes.",
                evidence={
                    "coverage_ratio": round(thematic_signals["coverage_ratio"], 4),
                    "minimum_coverage_ratio": THEMATIC_THRESHOLDS["minimum_coverage_ratio"],
                    "missing_themes": thematic_signals["missing_themes"],
                    "matched_themes": thematic_signals["matched_themes"],
                },
            )
        )

    if (
        thematic_signals["distinct_keyphrase_count"]
        < THEMATIC_THRESHOLDS["minimum_distinct_keyphrases"]
    ):
        findings.append(
            _build_finding(
                rule_id="seo.thematic_diversity",
                severity="minor",
                message="The extracted thematic keyphrases are not diverse enough.",
                evidence={
                    "distinct_keyphrase_count": thematic_signals["distinct_keyphrase_count"],
                    "minimum_distinct_keyphrases": THEMATIC_THRESHOLDS["minimum_distinct_keyphrases"],
                    "extracted_keyphrases": thematic_signals["extracted_keyphrases"],
                },
            )
        )

    #*********Score compute*********#
    if not semantic_compensation["introduction_compensated"]:
        semantic_penalty += 10

    if not semantic_compensation["heading_compensated"]:
        semantic_penalty += 8

    if not semantic_compensation["conclusion_compensated"]:
        semantic_penalty += 8

    if not semantic_compensation["body_compensated"]:
        semantic_penalty += 12

    lexical_score = max(100 - lexical_penalty, 0)
    semantic_score = max(100 - semantic_penalty, 0)
    thematic_score = _compute_thematic_score(thematic_signals)

    # Guardrail:
    if main_keyword_exact_missing:
        semantic_score = min(semantic_score, 60)

    if not has_any_keyword_occurrence:
        semantic_score = min(semantic_score, 40)
        thematic_score = min(thematic_score, 40)

    # Global score
    global_score = round(
        (0.5 * lexical_score) 
        + (0.3 * semantic_score) 
        + (0.2 * thematic_score)
    )

    has_findings = bool(findings)
    has_major_findings = any(finding["severity"] == "major" for finding in findings)

    if not has_any_keyword_occurrence:
        status = "fail"
    elif has_major_findings and global_score < 85:
        status = "fail"
    elif has_findings:
        status = "warn"
    elif global_score >= 85:
        status = "pass"
    elif global_score >= 60:
        status = "warn"
    else:
        status = "fail"

    return {
        "dimension": "seo",
        "status": status,
        "score": global_score,
        "subscores": {
            "lexical": lexical_score,
            "semantic": semantic_score,
            "thematic": thematic_score,
        },
        "applied_rule": judge_rules,
        "findings": findings,
        "semantic_signals": semantic_signals,
        "semantic_compensation": semantic_compensation,
        "thematic_signals": thematic_signals,
    }

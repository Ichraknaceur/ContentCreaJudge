"""Judge logic for SEO evaluation."""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Protocol

from sentence_transformers import SentenceTransformer
from sentence_transformers import util as st_util

from contentcreajudge.core.settings import settings


class _SimilarityValue(Protocol):
    """Tensor-like scalar similarity value."""

    def item(self) -> float:
        """Return the scalar similarity value."""
        ...


class _SimilarityVector(Protocol):
    """Tensor-like vector of scalar similarity values."""

    def __getitem__(self, index: int) -> _SimilarityValue:
        """Return the scalar similarity value at the requested index."""
        ...


SEMANTIC_MODEL_NAME = settings.seo_embedding_model
SEMANTIC_TOP_K = settings.seo_semantic_top_k
SEMANTIC_TOP_WEIGHTS = [0.60, 0.25, 0.15]
SEMANTIC_COMPENSATION_THRESHOLD = 70
SEMANTIC_COMPENSATION_STRONG_THRESHOLD = 75
SEMANTIC_COMPENSATION_MEDIUM_THRESHOLD = 60

OVEROPTIMIZATION_SIMILARITY_THRESHOLD = 0.75
OVEROPTIMIZATION_DENSITY_MEDIUM_THRESHOLD = 0.025
OVEROPTIMIZATION_DENSITY_HIGH_THRESHOLD = 0.045
OVEROPTIMIZATION_DENSITY_VERY_HIGH_THRESHOLD = 0.065
OVEROPTIMIZATION_LOW_RISK_SCORE = 85
OVEROPTIMIZATION_MEDIUM_LOW_RISK_SCORE = 70
OVEROPTIMIZATION_MEDIUM_HIGH_RISK_SCORE = 50

CONCENTRATION_LOW_THRESHOLD = 0.75
CONCENTRATION_MEDIUM_THRESHOLD = 0.50
CONCENTRATION_HIGH_THRESHOLD = 0.25

LOCAL_REPETITION_MEDIUM_COUNT = 2
LOCAL_REPETITION_HIGH_COUNT = 3

SEO_PASS_SCORE_THRESHOLD = 85
SEO_WARN_SCORE_THRESHOLD = 60

_DEFAULT_SCORING = {
    "pass_threshold": SEO_PASS_SCORE_THRESHOLD,
    "warn_threshold": SEO_WARN_SCORE_THRESHOLD,
    "global_weights": {
        "with_overoptimization": {
            "lexical": 0.55,
            "semantic": 0.30,
            "overoptimization": 0.15,
        },
        "without_overoptimization": {"lexical": 0.65, "semantic": 0.35},
    },
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


@lru_cache(maxsize=1)
def _load_semantic_model() -> SentenceTransformer:
    """Load and cache the embedding model used for semantic SEO checks."""
    return SentenceTransformer(SEMANTIC_MODEL_NAME)


def _get_semantic_model() -> SentenceTransformer | None:
    """Return the semantic model, or None when it cannot be loaded."""
    try:
        return _load_semantic_model()
    except Exception:  # noqa: BLE001
        return None


def warmup_semantic_model() -> None:
    """Pre-load the semantic model at startup to avoid a slow first request."""
    _get_semantic_model()


_CONCLUSION_TITLES = {
    "conclusion",
    "en conclusion",
    "pour conclure",
    "en guise de conclusion",
    "pour finir",
    "en resume",
    "en résumé",
    "pour resumer",
    "pour résumer",
    "to conclude",
    "in conclusion",
    "final thoughts",
}


def _is_conclusion_title(title: str) -> bool:
    """Return whether a section title is a conclusion heading."""
    return title.strip().lower() in _CONCLUSION_TITLES


# **********Semantic**********#
def _compute_weighted_top_chunk_score(
    top_chunks: list[dict[str, Any]],
) -> int:
    """Compute a semantic score from the ranked top chunks."""
    if not top_chunks:
        return 0

    available_weights = SEMANTIC_TOP_WEIGHTS[: len(top_chunks)]
    weight_sum = sum(available_weights)

    weighted_similarity = (
        sum(
            float(chunk["similarity"]) * weight
            for chunk, weight in zip(top_chunks, available_weights, strict=False)
        )
        / weight_sum
    )

    return round(weighted_similarity * 100)


def _compute_semantic_signals(
    semantic_inputs: dict[str, Any],
) -> dict[str, Any]:
    """Compute semantic alignment between the main keyword and semantic chunks."""
    main_keyword = str(semantic_inputs.get("main_keyword", "")).strip()
    chunks = semantic_inputs.get("chunks", [])

    if not main_keyword or not isinstance(chunks, list) or not chunks:
        return {
            "main_keyword": main_keyword,
            "top_chunks": [],
            "best_similarity": 0.0,
            "semantic_score": 0,
            "semantic_available": True,
        }

    chunk_texts = [
        str(chunk.get("text", "")).strip()
        for chunk in chunks
        if isinstance(chunk, dict) and str(chunk.get("text", "")).strip()
    ]

    if not chunk_texts:
        return {
            "main_keyword": main_keyword,
            "top_chunks": [],
            "best_similarity": 0.0,
            "semantic_score": 0,
            "semantic_available": True,
        }

    model = _get_semantic_model()
    if model is None:
        return {
            "main_keyword": main_keyword,
            "top_chunks": [],
            "best_similarity": 0.0,
            "semantic_score": 0,
            "semantic_available": False,
        }

    embeddings = model.encode(
        [main_keyword, *chunk_texts],
        convert_to_tensor=True,
        normalize_embeddings=True,
    )

    keyword_embedding = embeddings[0]
    chunk_embeddings = embeddings[1:]

    similarities = st_util.cos_sim(keyword_embedding, chunk_embeddings)[0]

    ranked_chunks: list[dict[str, Any]] = []

    valid_chunk_index = 0
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        chunk_text = str(chunk.get("text", "")).strip()
        if not chunk_text:
            continue

        similarity = float(similarities[valid_chunk_index].item())
        valid_chunk_index += 1

        ranked_chunks.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "text": chunk_text,
                "start_word": chunk.get("start_word"),
                "end_word": chunk.get("end_word"),
                "word_count": chunk.get("word_count"),
                "similarity": similarity,
            },
        )

    top_chunks = sorted(
        ranked_chunks,
        key=lambda item: float(item["similarity"]),
        reverse=True,
    )[:SEMANTIC_TOP_K]

    semantic_score = _compute_weighted_top_chunk_score(top_chunks)

    return {
        "main_keyword": main_keyword,
        "top_chunks": top_chunks,
        "best_similarity": float(top_chunks[0]["similarity"]) if top_chunks else 0.0,
        "semantic_score": semantic_score,
        "semantic_available": True,
    }


def _compute_semantic_compensation(
    semantic_signals: dict[str, Any],
) -> dict[str, Any]:
    """Return the semantic compensation level for body-level lexical weaknesses."""
    semantic_score = int(semantic_signals.get("semantic_score", 0))

    if semantic_score >= SEMANTIC_COMPENSATION_STRONG_THRESHOLD:
        level = "strong"
        penalty_reduction = 10
    elif semantic_score >= SEMANTIC_COMPENSATION_MEDIUM_THRESHOLD:
        level = "medium"
        penalty_reduction = 5
    else:
        level = "none"
        penalty_reduction = 0

    return {
        "body_compensation_level": level,
        "body_penalty_reduction": penalty_reduction,
        "body_compensated": level != "none",
    }


# **********Overoptimization**********#
def _compute_overoptimization_sentence_similarities(
    overoptimization_inputs: dict[str, Any],
) -> dict[str, Any]:
    """Compute sentence-level semantic similarity for over-optimization."""
    main_keyword = str(overoptimization_inputs.get("main_keyword", "")).strip()
    paragraphs = overoptimization_inputs.get("paragraphs", [])
    total_words = int(overoptimization_inputs.get("total_words", 0))

    if not main_keyword or not isinstance(paragraphs, list) or not paragraphs:
        return _build_overoptimization_sentence_result(main_keyword, total_words)

    sentence_records, sentence_texts = _collect_overoptimization_sentences(paragraphs)

    if not sentence_texts:
        return _build_overoptimization_sentence_result(main_keyword, total_words)

    model = _get_semantic_model()
    if model is None:
        return _build_overoptimization_sentence_result(
            main_keyword,
            total_words,
            semantic_available=False,
        )

    embeddings = model.encode(
        [main_keyword, *sentence_texts],
        convert_to_tensor=True,
        normalize_embeddings=True,
    )

    keyword_embedding = embeddings[0]
    sentence_embeddings = embeddings[1:]

    similarities = st_util.cos_sim(keyword_embedding, sentence_embeddings)[0]

    paragraph_outputs, semantic_occurrences = _build_overoptimization_paragraphs(
        sentence_records,
        similarities,
    )

    return _build_overoptimization_sentence_result(
        main_keyword,
        total_words,
        paragraphs=list(paragraph_outputs.values()),
        semantic_occurrences=semantic_occurrences,
    )


def _build_overoptimization_sentence_result(
    main_keyword: str,
    total_words: int,
    *,
    paragraphs: list[dict[str, Any]] | None = None,
    semantic_occurrences: int = 0,
    semantic_available: bool = True,
) -> dict[str, Any]:
    """Build the sentence-level over-optimization result payload."""
    return {
        "main_keyword": main_keyword,
        "total_words": total_words,
        "paragraphs": paragraphs or [],
        "semantic_occurrences": semantic_occurrences,
        "similarity_threshold": OVEROPTIMIZATION_SIMILARITY_THRESHOLD,
        "semantic_available": semantic_available,
    }


def _collect_overoptimization_sentences(
    paragraphs: list[Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Collect sentence records eligible for semantic over-optimization checks."""
    sentence_records: list[dict[str, Any]] = []
    sentence_texts: list[str] = []

    for paragraph in paragraphs:
        if not isinstance(paragraph, dict):
            continue

        for sentence in paragraph.get("sentences", []):
            if not isinstance(sentence, dict):
                continue

            sentence_text = str(sentence.get("text", "")).strip()

            if not sentence_text:
                continue

            sentence_records.append(
                {
                    "paragraph_id": paragraph.get("paragraph_id"),
                    "section": paragraph.get("section"),
                    "sentence_id": sentence.get("sentence_id"),
                    "text": sentence_text,
                    "exact_main_keyword_match": bool(
                        sentence.get("exact_main_keyword_match", False),
                    ),
                },
            )
            sentence_texts.append(sentence_text)

    return sentence_records, sentence_texts


def _build_overoptimization_paragraphs(
    sentence_records: list[dict[str, Any]],
    similarities: _SimilarityVector,
) -> tuple[dict[int, dict[str, Any]], int]:
    """Group semantic sentence similarities by paragraph."""
    paragraph_outputs: dict[int, dict[str, Any]] = {}
    semantic_occurrences = 0

    for index, record in enumerate(sentence_records):
        similarity = float(similarities[index].item())

        exact_match = bool(record["exact_main_keyword_match"])
        semantic_match = similarity >= OVEROPTIMIZATION_SIMILARITY_THRESHOLD
        is_semantic_match = exact_match or semantic_match

        if is_semantic_match:
            semantic_occurrences += 1

        paragraph_id = int(record["paragraph_id"])

        if paragraph_id not in paragraph_outputs:
            paragraph_outputs[paragraph_id] = {
                "paragraph_id": paragraph_id,
                "section": record["section"],
                "sentence_similarities": [],
            }

        paragraph_outputs[paragraph_id]["sentence_similarities"].append(
            {
                "sentence_id": record["sentence_id"],
                "text": record["text"],
                "similarity": similarity,
                "exact_main_keyword_match": exact_match,
                "semantic_match": semantic_match,
                "is_semantic_match": is_semantic_match,
            },
        )

    return paragraph_outputs, semantic_occurrences


def _compute_density_score(
    semantic_occurrences: int,
    total_words: int,
) -> dict[str, Any]:
    """Compute density score from semantic occurrences over total words."""
    if total_words <= 0:
        return {
            "density": 0.0,
            "density_level": "none",
            "density_score": 100,
        }

    density = semantic_occurrences / total_words

    if density <= OVEROPTIMIZATION_DENSITY_MEDIUM_THRESHOLD:
        density_level = "low"
        density_score = 100
    elif density <= OVEROPTIMIZATION_DENSITY_HIGH_THRESHOLD:
        density_level = "medium"
        density_score = 75
    elif density <= OVEROPTIMIZATION_DENSITY_VERY_HIGH_THRESHOLD:
        density_level = "high"
        density_score = 45
    else:
        density_level = "very_high"
        density_score = 20

    return {
        "density": round(density, 4),
        "density_level": density_level,
        "density_score": density_score,
    }


def _compute_concentration_score(
    sentence_similarity_signals: dict[str, Any],
) -> dict[str, Any]:
    """Compute concentration score from semantic matches distribution."""
    semantic_occurrences = int(
        sentence_similarity_signals.get("semantic_occurrences", 0),
    )
    paragraphs = sentence_similarity_signals.get("paragraphs", [])

    if semantic_occurrences <= 0 or not isinstance(paragraphs, list):
        return {
            "paragraphs_with_matches": 0,
            "concentration_ratio": 1.0,
            "concentration_level": "none",
            "concentration_score": 100,
        }

    paragraphs_with_matches = 0

    for paragraph in paragraphs:
        if not isinstance(paragraph, dict):
            continue

        sentence_similarities = paragraph.get("sentence_similarities", [])

        if not isinstance(sentence_similarities, list):
            continue

        has_match = any(
            isinstance(sentence, dict) and sentence.get("is_semantic_match") is True
            for sentence in sentence_similarities
        )

        if has_match:
            paragraphs_with_matches += 1

    concentration_ratio = paragraphs_with_matches / semantic_occurrences

    if concentration_ratio >= CONCENTRATION_LOW_THRESHOLD:
        concentration_level = "low"
        concentration_score = 100
    elif concentration_ratio >= CONCENTRATION_MEDIUM_THRESHOLD:
        concentration_level = "medium"
        concentration_score = 75
    elif concentration_ratio >= CONCENTRATION_HIGH_THRESHOLD:
        concentration_level = "high"
        concentration_score = 45
    else:
        concentration_level = "very_high"
        concentration_score = 20

    return {
        "paragraphs_with_matches": paragraphs_with_matches,
        "concentration_ratio": round(concentration_ratio, 4),
        "concentration_level": concentration_level,
        "concentration_score": concentration_score,
    }


def _compute_local_repetition_score(
    sentence_similarity_signals: dict[str, Any],
) -> dict[str, Any]:
    """Compute local repetition score from semantic matches inside paragraphs."""
    paragraphs = sentence_similarity_signals.get("paragraphs", [])

    if not isinstance(paragraphs, list) or not paragraphs:
        return {
            "max_local_repetition": 0,
            "local_repetition_level": "none",
            "local_repetition_score": 100,
        }

    max_local_repetition = 0

    for paragraph in paragraphs:
        if not isinstance(paragraph, dict):
            continue

        sentence_similarities = paragraph.get("sentence_similarities", [])

        if not isinstance(sentence_similarities, list):
            continue

        local_repetition = sum(
            1
            for sentence in sentence_similarities
            if isinstance(sentence, dict) and sentence.get("is_semantic_match") is True
        )

        max_local_repetition = max(max_local_repetition, local_repetition)

    if max_local_repetition <= 1:
        level = "low"
        score = 100
    elif max_local_repetition == LOCAL_REPETITION_MEDIUM_COUNT:
        level = "medium"
        score = 75
    elif max_local_repetition == LOCAL_REPETITION_HIGH_COUNT:
        level = "high"
        score = 45
    else:
        level = "very_high"
        score = 20

    return {
        "max_local_repetition": max_local_repetition,
        "local_repetition_level": level,
        "local_repetition_score": score,
    }


def _compute_overoptimization_score(
    density_signals: dict[str, Any],
    concentration_signals: dict[str, Any],
    local_repetition_signals: dict[str, Any],
    semantic_occurrences: int,
) -> dict[str, Any]:
    """Compute global overoptimization score."""
    if semantic_occurrences == 0:
        return {
            "overoptimization_applicable": False,
            "overoptimization_score": 100,
            "overoptimization_risk": "not_applicable",
            "reason": (
                "No exact or semantic occurrence of the main keyword was detected."
            ),
            "subscores": {
                "density": density_signals["density_score"],
                "concentration": concentration_signals["concentration_score"],
                "local_repetition": local_repetition_signals["local_repetition_score"],
            },
        }

    overoptimization_score = round(
        (0.40 * density_signals["density_score"])
        + (0.35 * concentration_signals["concentration_score"])
        + (0.25 * local_repetition_signals["local_repetition_score"]),
    )

    if overoptimization_score >= OVEROPTIMIZATION_LOW_RISK_SCORE:
        risk = "low"
    elif overoptimization_score >= OVEROPTIMIZATION_MEDIUM_LOW_RISK_SCORE:
        risk = "medium_low"
    elif overoptimization_score >= OVEROPTIMIZATION_MEDIUM_HIGH_RISK_SCORE:
        risk = "medium_high"
    else:
        risk = "high"

    return {
        "overoptimization_applicable": True,
        "overoptimization_score": overoptimization_score,
        "overoptimization_risk": risk,
        "subscores": {
            "density": density_signals["density_score"],
            "concentration": concentration_signals["concentration_score"],
            "local_repetition": local_repetition_signals["local_repetition_score"],
        },
    }


def _add_semantic_unavailable_finding(
    findings: list[dict[str, Any]],
    messages: dict[str, Any],
    *,
    rule_id: str,
    check: str | None = None,
) -> None:
    """Append a semantic-unavailable finding."""
    evidence: dict[str, Any] = {
        "semantic_available": False,
        "fallback": "lexical_only",
    }
    if check is not None:
        evidence["check"] = check

    findings.append(
        _build_finding(
            rule_id=rule_id,
            severity="minor",
            message=messages.get(
                "semantic_unavailable",
                (
                    "Semantic SEO checks could not be executed. "
                    "Lexical checks were applied instead."
                ),
            ),
            evidence=evidence,
        ),
    )


def _compute_seo_semantic_state(
    semantic_inputs: dict[str, Any],
    overoptimization_inputs: dict[str, Any],
    messages: dict[str, Any],
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute semantic, compensation, and over-optimization signals."""
    semantic_signals = _compute_semantic_signals(semantic_inputs)
    if semantic_signals.get("semantic_available") is False:
        _add_semantic_unavailable_finding(
            findings,
            messages,
            rule_id="seo.semantic_unavailable",
        )

    sentence_signals = _compute_overoptimization_sentence_similarities(
        overoptimization_inputs,
    )
    if sentence_signals.get("semantic_available") is False:
        _add_semantic_unavailable_finding(
            findings,
            messages,
            rule_id="seo.overoptimization_semantic_unavailable",
            check="overoptimization",
        )

    density_signals = _compute_density_score(
        semantic_occurrences=sentence_signals["semantic_occurrences"],
        total_words=sentence_signals["total_words"],
    )
    concentration_signals = _compute_concentration_score(sentence_signals)
    local_repetition_signals = _compute_local_repetition_score(sentence_signals)
    overoptimization_signals = _compute_overoptimization_score(
        density_signals=density_signals,
        concentration_signals=concentration_signals,
        local_repetition_signals=local_repetition_signals,
        semantic_occurrences=int(sentence_signals["semantic_occurrences"]),
    )

    return {
        "semantic": semantic_signals,
        "compensation": _compute_semantic_compensation(semantic_signals),
        "sentence_similarity": sentence_signals,
        "density": density_signals,
        "concentration": concentration_signals,
        "local_repetition": local_repetition_signals,
        "overoptimization": overoptimization_signals,
    }


def _disable_body_semantic_compensation() -> dict[str, Any]:
    """Return an empty semantic compensation payload."""
    return {
        "body_compensation_level": "none",
        "body_penalty_reduction": 0,
        "body_compensated": False,
    }


def _build_seo_context(
    preprocessed_content: dict[str, Any],
    judge_rules: dict[str, Any],
) -> dict[str, Any]:
    """Collect frequently used judge inputs into a context dict."""
    lexical_signals = preprocessed_content["lexical_signals"]
    main_keyword_occurrences = lexical_signals["main_keyword_occurrences"]
    total_occurrences = main_keyword_occurrences["body"]

    return {
        "lexical_signals": lexical_signals,
        "semantic_inputs": preprocessed_content["semantic_inputs"],
        "overoptimization_inputs": preprocessed_content["overoptimization_inputs"],
        "rules": judge_rules["rules"],
        "messages": judge_rules["messages"],
        "main_keyword": lexical_signals["main_keyword"],
        "presence": lexical_signals["main_keyword_presence"],
        "occurrences": main_keyword_occurrences,
        "section_distribution": lexical_signals["section_distribution"],
        "single_section_concentration": lexical_signals[
            "single_section_concentration_detected"
        ],
        "forbidden_keyword_emphasis": lexical_signals["forbidden_keyword_emphasis"],
        "content_type": str(judge_rules.get("content_type", "")),
        "main_keyword_rules": judge_rules["main_keyword_rules"],
        "occurrence_rules": judge_rules["keyword_occurrence_rules"],
        "distribution_rules": judge_rules["keyword_distribution_rules"],
        "total_occurrences": total_occurrences,
        "has_main_keyword_occurrence": total_occurrences > 0,
        "main_keyword_exact_missing": main_keyword_occurrences["body"] == 0,
    }


def _evaluate_main_keyword_presence(
    context: dict[str, Any],
    semantic_compensation: dict[str, Any],
    findings: list[dict[str, Any]],
) -> int:
    """Evaluate required main keyword presence."""
    if not (
        context["main_keyword_rules"].get("require_presence", False)
        and not context["presence"]["body"]
    ):
        return 0

    findings.append(
        _build_finding(
            rule_id="seo.main_keyword_presence",
            severity=_get_rule_severity(context["rules"], "seo.main_keyword_presence"),
            message=context["messages"]["main_keyword_presence"],
            evidence={
                "main_keyword": context["main_keyword"],
                "present_in_body": False,
                "semantic_body_compensation": semantic_compensation["body_compensated"],
                "body_compensation_level": semantic_compensation[
                    "body_compensation_level"
                ],
                "body_penalty_reduction": semantic_compensation[
                    "body_penalty_reduction"
                ],
            },
        ),
    )

    return max(25 - int(semantic_compensation["body_penalty_reduction"]), 10)


def _find_missing_keyword_locations(
    context: dict[str, Any],
    semantic_compensation: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Return missing and semantically compensated keyword locations."""
    required_locations = context["main_keyword_rules"].get("required_locations", {})
    presence = context["presence"]
    missing_locations: list[str] = []
    compensated_locations: list[str] = []

    location_checks = {
        "introduction": "introduction",
        "heading_h2_or_h3": "headings_h2_h3",
        "conclusion": "conclusion",
    }
    for location, presence_key in location_checks.items():
        if required_locations.get(location, False) and not presence[presence_key]:
            missing_locations.append(location)

    if required_locations.get("body", False) and not presence["body"]:
        if semantic_compensation["body_compensated"]:
            compensated_locations.append("body")
        else:
            missing_locations.append("body")

    return missing_locations, compensated_locations


def _evaluate_main_keyword_locations(
    context: dict[str, Any],
    semantic_compensation: dict[str, Any],
    findings: list[dict[str, Any]],
) -> int:
    """Evaluate required main keyword locations."""
    missing_locations, compensated_locations = _find_missing_keyword_locations(
        context,
        semantic_compensation,
    )
    if not missing_locations and not compensated_locations:
        return 0

    findings.append(
        _build_finding(
            rule_id="seo.main_keyword_locations",
            severity=(
                _get_rule_severity(context["rules"], "seo.main_keyword_locations")
                if missing_locations
                else "minor"
            ),
            message=context["messages"]["main_keyword_locations"],
            evidence={
                "main_keyword": context["main_keyword"],
                "missing_locations": missing_locations,
                "compensated_locations": compensated_locations,
            },
        ),
    )

    return 20 if missing_locations else 5


def _get_occurrence_flags(context: dict[str, Any]) -> dict[str, bool]:
    """Return occurrence rule violation flags."""
    occurrence_rules = context["occurrence_rules"]
    flags = {
        "below_min_total": False,
        "above_max_total": False,
        "below_min_main": False,
    }

    if not occurrence_rules.get("enforce_minimum_occurrences", False):
        return flags

    min_total = occurrence_rules.get("min_total")
    max_total = occurrence_rules.get("max_total")
    min_main = occurrence_rules.get("min_main")

    flags["below_min_total"] = (
        min_total is not None and context["total_occurrences"] < min_total
    )
    flags["above_max_total"] = (
        max_total is not None and context["total_occurrences"] > max_total
    )
    flags["below_min_main"] = (
        min_main is not None and context["occurrences"]["body"] < min_main
    )
    return flags


def _evaluate_keyword_occurrences(
    context: dict[str, Any],
    semantic_compensation: dict[str, Any],
    findings: list[dict[str, Any]],
) -> int:
    """Evaluate keyword occurrence count rules."""
    occurrence_rules = context["occurrence_rules"]
    flags = _get_occurrence_flags(context)
    if not any(flags.values()):
        return 0

    occurrence_severity = _get_rule_severity(
        context["rules"],
        "seo.keyword_occurrences",
    )
    if (
        semantic_compensation["body_compensation_level"] in {"medium", "strong"}
        and not flags["above_max_total"]
        and (flags["below_min_total"] or flags["below_min_main"])
    ):
        occurrence_severity = "minor"

    findings.append(
        _build_finding(
            rule_id="seo.keyword_occurrences",
            severity=occurrence_severity,
            message=context["messages"]["keyword_occurrences"],
            evidence={
                "main_keyword_occurrences_in_body": context["occurrences"]["body"],
                "total_keyword_occurrences": context["total_occurrences"],
                "expected_min_total": occurrence_rules.get("min_total"),
                "expected_max_total": occurrence_rules.get("max_total"),
                "expected_min_main": occurrence_rules.get("min_main"),
                "semantic_body_compensation": semantic_compensation["body_compensated"],
                "body_compensation_level": semantic_compensation[
                    "body_compensation_level"
                ],
                "body_penalty_reduction": semantic_compensation[
                    "body_penalty_reduction"
                ],
            },
        ),
    )

    return max(15 - int(semantic_compensation["body_penalty_reduction"]), 5)


def _get_sections_without_keywords(context: dict[str, Any]) -> list[str]:
    """Return H2 sections without secondary or long-tail keywords."""
    lexical_signals = context["lexical_signals"]
    secondary_keywords_provided = bool(
        lexical_signals["secondary_keyword_occurrences"]
        or lexical_signals["long_tail_keyword_occurrences"],
    )

    if not (
        secondary_keywords_provided
        and context["distribution_rules"].get(
            "require_at_least_one_secondary_or_long_tail_per_h2_section",
            False,
        )
    ):
        return []

    return [
        str(section["h2"])
        for section in context["section_distribution"]
        if not section["has_secondary_or_long_tail"]
    ]


def _evaluate_keyword_distribution(
    context: dict[str, Any],
    semantic_compensation: dict[str, Any],
    findings: list[dict[str, Any]],
) -> int:
    """Evaluate keyword distribution rules."""
    sections_without_keywords = _get_sections_without_keywords(context)
    distribution_issue = bool(sections_without_keywords)
    conclusion_only_gap = sections_without_keywords and all(
        _is_conclusion_title(section) for section in sections_without_keywords
    )

    if (
        context["distribution_rules"].get("forbid_single_section_concentration", False)
        and context["single_section_concentration"]
    ):
        distribution_issue = True

    if not distribution_issue:
        return 0

    distribution_severity = _get_rule_severity(
        context["rules"],
        "seo.keyword_distribution",
    )
    if (
        semantic_compensation["body_compensation_level"] in {"medium", "strong"}
        and conclusion_only_gap
    ):
        distribution_severity = "minor"

    findings.append(
        _build_finding(
            rule_id="seo.keyword_distribution",
            severity=distribution_severity,
            message=context["messages"]["keyword_distribution"],
            evidence={
                "sections_without_secondary_or_long_tail": sections_without_keywords,
                "single_section_concentration_detected": context[
                    "single_section_concentration"
                ],
                "semantic_body_compensation": semantic_compensation["body_compensated"],
                "body_compensation_level": semantic_compensation[
                    "body_compensation_level"
                ],
                "body_penalty_reduction": semantic_compensation[
                    "body_penalty_reduction"
                ],
            },
        ),
    )

    return max(8 - int(semantic_compensation["body_penalty_reduction"]), 0)


def _evaluate_overoptimization(
    context: dict[str, Any],
    semantic_state: dict[str, Any],
    findings: list[dict[str, Any]],
) -> int:
    """Evaluate over-optimization risk."""
    overoptimization_signals = semantic_state["overoptimization"]
    overoptimization_risk = str(overoptimization_signals["overoptimization_risk"])

    if overoptimization_risk not in {"medium_high", "high"}:
        return 0

    findings.append(
        _build_finding(
            rule_id="seo.over_optimization",
            severity=_get_rule_severity(context["rules"], "seo.over_optimization"),
            message=context["messages"]["over_optimization"],
            evidence={
                "overoptimization_score": int(
                    overoptimization_signals["overoptimization_score"],
                ),
                "overoptimization_risk": overoptimization_risk,
                "density": semantic_state["density"]["density"],
                "density_level": semantic_state["density"]["density_level"],
                "concentration_ratio": semantic_state["concentration"][
                    "concentration_ratio"
                ],
                "concentration_level": semantic_state["concentration"][
                    "concentration_level"
                ],
                "max_local_repetition": semantic_state["local_repetition"][
                    "max_local_repetition"
                ],
                "local_repetition_level": semantic_state["local_repetition"][
                    "local_repetition_level"
                ],
            },
        ),
    )

    return 10 if overoptimization_risk == "medium_high" else 20


def _evaluate_formatting_constraints(
    context: dict[str, Any],
    findings: list[dict[str, Any]],
) -> int:
    """Evaluate forbidden keyword emphasis formatting."""
    forbidden_keyword_emphasis = context["forbidden_keyword_emphasis"]
    if not forbidden_keyword_emphasis or context["content_type"] == "quiz":
        return 0

    findings.append(
        _build_finding(
            rule_id="seo.formatting_constraints",
            severity=_get_rule_severity(context["rules"], "seo.formatting_constraints"),
            message=context["messages"]["formatting_constraints"],
            evidence={
                "matches_count": len(forbidden_keyword_emphasis),
                "matches": forbidden_keyword_emphasis,
            },
        ),
    )
    return 10


def _compute_lexical_penalty(
    context: dict[str, Any],
    semantic_compensation: dict[str, Any],
    semantic_state: dict[str, Any],
    findings: list[dict[str, Any]],
) -> int:
    """Compute the total lexical penalty and append lexical findings."""
    return sum(
        (
            _evaluate_main_keyword_presence(context, semantic_compensation, findings),
            _evaluate_main_keyword_locations(context, semantic_compensation, findings),
            _evaluate_keyword_occurrences(context, semantic_compensation, findings),
            _evaluate_keyword_distribution(context, semantic_compensation, findings),
            _evaluate_overoptimization(context, semantic_state, findings),
            _evaluate_formatting_constraints(context, findings),
        ),
    )


def _compute_guarded_semantic_score(
    context: dict[str, Any],
    semantic_signals: dict[str, Any],
) -> int:
    """Compute semantic score with exact-match guardrails."""
    semantic_score = max(0, min(int(semantic_signals.get("semantic_score", 0)), 100))

    if context["main_keyword_exact_missing"]:
        semantic_score = min(semantic_score, 60)

    if not context["has_main_keyword_occurrence"]:
        semantic_score = min(semantic_score, 40)

    return semantic_score


def _compute_global_seo_score(
    lexical_score: int,
    semantic_score: int,
    semantic_state: dict[str, Any],
    scoring: dict[str, Any],
) -> int:
    """Compute the global SEO score using weights from the resolved rules."""
    overoptimization_score = int(
        semantic_state["overoptimization"]["overoptimization_score"],
    )
    weights = scoring.get("global_weights", _DEFAULT_SCORING["global_weights"])

    if semantic_state["overoptimization"]["overoptimization_applicable"]:
        w = weights.get(
            "with_overoptimization",
            _DEFAULT_SCORING["global_weights"]["with_overoptimization"],
        )
        return round(
            (w["lexical"] * lexical_score)
            + (w["semantic"] * semantic_score)
            + (w["overoptimization"] * overoptimization_score),
        )

    w = weights.get(
        "without_overoptimization",
        _DEFAULT_SCORING["global_weights"]["without_overoptimization"],
    )
    return round((w["lexical"] * lexical_score) + (w["semantic"] * semantic_score))


_SEMANTIC_AVAILABILITY_RULE_IDS = {
    "seo.semantic_unavailable",
    "seo.overoptimization_semantic_unavailable",
}


def _compute_seo_status(
    context: dict[str, Any],
    global_score: int,
    findings: list[dict[str, Any]],
    scoring: dict[str, Any],
) -> str:
    """Compute the SEO status from score and findings."""
    if not context["has_main_keyword_occurrence"]:
        return "fail"

    pass_threshold = scoring.get("pass_threshold", SEO_PASS_SCORE_THRESHOLD)
    warn_threshold = scoring.get("warn_threshold", SEO_WARN_SCORE_THRESHOLD)

    evaluable_findings = [
        f for f in findings if f.get("rule_id") not in _SEMANTIC_AVAILABILITY_RULE_IDS
    ]

    if global_score >= pass_threshold and not evaluable_findings:
        return "pass"

    if global_score >= warn_threshold:
        return "warn"

    return "fail"


# **********The judge**********#
def run_seo_judge(
    preprocessed_content: dict[str, Any],
    judge_rules: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate SEO compliance using lexical signals with semantic compensation."""
    findings: list[dict[str, Any]] = []
    context = _build_seo_context(preprocessed_content, judge_rules)
    semantic_state = _compute_seo_semantic_state(
        context["semantic_inputs"],
        context["overoptimization_inputs"],
        context["messages"],
        findings,
    )

    semantic_compensation = semantic_state["compensation"]
    if not context["has_main_keyword_occurrence"]:
        semantic_compensation = _disable_body_semantic_compensation()

    lexical_penalty = _compute_lexical_penalty(
        context,
        semantic_compensation,
        semantic_state,
        findings,
    )

    scoring = judge_rules.get("scoring") or _DEFAULT_SCORING

    lexical_score = max(100 - lexical_penalty, 0)
    semantic_score = _compute_guarded_semantic_score(
        context,
        semantic_state["semantic"],
    )
    global_score = _compute_global_seo_score(
        lexical_score,
        semantic_score,
        semantic_state,
        scoring,
    )
    status = _compute_seo_status(context, global_score, findings, scoring)

    return {
        "dimension": "seo",
        "status": status,
        "score": global_score,
        "subscores": {
            "lexical": lexical_score,
            "semantic": semantic_score,
            "overoptimization": int(
                semantic_state["overoptimization"]["overoptimization_score"],
            ),
            "overoptimization_applicable": semantic_state["overoptimization"][
                "overoptimization_applicable"
            ],
        },
        "applied_rule": judge_rules,
        "findings": findings,
        "semantic_signals": semantic_state["semantic"],
        "semantic_compensation": semantic_compensation,
        "overoptimization_signals": {
            "sentence_similarity": semantic_state["sentence_similarity"],
            "density": semantic_state["density"],
            "concentration": semantic_state["concentration"],
            "local_repetition": semantic_state["local_repetition"],
            "global": semantic_state["overoptimization"],
        },
    }

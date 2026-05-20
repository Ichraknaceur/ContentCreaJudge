"""Semantic fallback utilities for CTA evaluation."""

from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


@lru_cache(maxsize=1)
def _load_model(model_name: str) -> SentenceTransformer:
    """Load and cache the sentence-transformer model."""
    return SentenceTransformer(model_name)


def _similarity(text: str, candidates: list[str], model_name: str) -> float:
    """Return the best semantic similarity between text and candidates."""
    if not text.strip() or not candidates:
        return 0.0

    model = _load_model(model_name)
    embeddings = model.encode([text, *candidates])
    text_embedding = embeddings[0].reshape(1, -1)
    candidate_embeddings = embeddings[1:]

    scores = cosine_similarity(text_embedding, candidate_embeddings)[0]
    return float(max(scores))


def is_semantically_aligned_with_funnel(
    cta_text: str,
    allowed_labels: list[str],
    forbidden_labels: list[str],
    expected_intents: list[str],
    semantic_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate whether a custom CTA is semantically aligned with the funnel."""
    model_name = str(
        semantic_rules.get("model_name", "paraphrase-multilingual-MiniLM-L12-v2")
    )
    minimum_similarity = float(semantic_rules.get("minimum_similarity", 0.55))
    forbidden_margin = float(semantic_rules.get("forbidden_margin", 0.08))
    forbidden_similarity_threshold = float(
        semantic_rules.get("forbidden_similarity_threshold", 0.75)
    )

    positive_candidates = [*allowed_labels, *expected_intents]

    positive_score = _similarity(cta_text, positive_candidates, model_name)
    forbidden_score = _similarity(cta_text, forbidden_labels, model_name)

    is_forbidden = forbidden_score >= forbidden_similarity_threshold
    is_aligned = positive_score >= minimum_similarity and not is_forbidden

    return {
        "is_aligned": is_aligned,
        "is_forbidden": is_forbidden,
        "positive_similarity": positive_score,
        "forbidden_similarity": forbidden_score,
        "minimum_similarity": minimum_similarity,
        "forbidden_margin": forbidden_margin,
        "forbidden_similarity_threshold": forbidden_similarity_threshold,
    }

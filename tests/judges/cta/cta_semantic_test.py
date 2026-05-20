"""Tests for CTA semantic fallback logic."""

from __future__ import annotations

from contentcreajudge.judges.cta import cta_semantic


def test_semantic_fallback_accepts_positive_match_below_old_threshold(
    monkeypatch,
) -> None:
    """Accept custom CTA intent once it reaches the configured positive threshold."""

    def fake_similarity(text: str, candidates: list[str], model_name: str) -> float:
        if "Buy" in candidates:
            return 0.10
        return 0.359

    monkeypatch.setattr(cta_semantic, "_similarity", fake_similarity)

    result = cta_semantic.is_semantically_aligned_with_funnel(
        cta_text="Explore the topic",
        allowed_labels=["Read more"],
        forbidden_labels=["Buy"],
        expected_intents=["learn more about an educational topic"],
        semantic_rules={
            "minimum_similarity": 0.35,
            "forbidden_similarity_threshold": 0.75,
        },
    )

    assert result["is_aligned"] is True
    assert result["is_forbidden"] is False
    assert result["positive_similarity"] == 0.359


def test_semantic_fallback_rejects_forbidden_match_at_threshold(monkeypatch) -> None:
    """Reject CTA intent when it matches forbidden labels strongly enough."""

    def fake_similarity(text: str, candidates: list[str], model_name: str) -> float:
        if "Buy" in candidates:
            return 0.75
        return 0.80

    monkeypatch.setattr(cta_semantic, "_similarity", fake_similarity)

    result = cta_semantic.is_semantically_aligned_with_funnel(
        cta_text="Buy now",
        allowed_labels=["Read more"],
        forbidden_labels=["Buy"],
        expected_intents=["learn more about an educational topic"],
        semantic_rules={
            "minimum_similarity": 0.35,
            "forbidden_similarity_threshold": 0.75,
        },
    )

    assert result["is_aligned"] is False
    assert result["is_forbidden"] is True
    assert result["forbidden_similarity"] == 0.75

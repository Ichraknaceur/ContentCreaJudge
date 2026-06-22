"""Tests for the editorial style prompt builder."""

from __future__ import annotations

import json

from contentcreajudge.judges.editorial_style.editorial_style_prompt import (
    build_editorial_style_prompt,
    load_editorial_style_prompt,
)


def test_load_editorial_style_prompt_returns_prompt_text() -> None:
    """It should load the editorial style system prompt from markdown."""
    prompt = load_editorial_style_prompt()

    assert "JUGE" in prompt
    assert "STYLE ÉDITORIAL" in prompt
    assert "criteria_scores" in prompt


def test_build_editorial_style_prompt_returns_full_prompt() -> None:
    """It should return the prompt instructions and evaluation payload."""
    prompt = build_editorial_style_prompt(
        preprocessed_content={
            "normalized_content": "Article à juger.",
            "editorial_style": {
                "writingStyle": "Style attendu.",
                "writeLikeThis": "Bon exemple.",
                "notLikeThis": "Mauvais exemple.",
            },
        },
    )

    assert "JUGE" in prompt
    assert "STYLE ÉDITORIAL" in prompt
    assert "ENTRÉES À ÉVALUER" in prompt
    assert "Article à juger." in prompt


def test_build_editorial_style_prompt_payload_is_valid_json() -> None:
    """It should build a JSON payload with style and article only."""
    prompt = build_editorial_style_prompt(
        preprocessed_content={
            "normalized_content": "Article à juger.",
            "editorial_style": {
                "writingStyle": "Style attendu.",
                "writeLikeThis": "Bon exemple.",
                "notLikeThis": "Mauvais exemple.",
            },
            "content_stats": {
                "word_count": 3,
            },
        },
    )

    payload_text = prompt.split("ENTRÉES À ÉVALUER", maxsplit=1)[1].strip()
    payload = json.loads(payload_text)

    assert payload == {
        "editorial_style": {
            "writingStyle": "Style attendu.",
            "writeLikeThis": "Bon exemple.",
            "notLikeThis": "Mauvais exemple.",
        },
        "article": "Article à juger.",
    }

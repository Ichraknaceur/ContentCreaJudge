"""Prompt builder for the editorial style judge."""

from __future__ import annotations

import json
from pathlib import Path


def load_editorial_style_prompt() -> str:
    """Load the editorial style judge system prompt."""
    prompt_path = Path(__file__).with_name("prompt.md")
    return prompt_path.read_text(encoding="utf-8").strip()


def build_editorial_style_prompt(
    preprocessed_content: dict[str, object],
) -> str:
    """Build the full prompt string for the editorial style LLM judge."""
    editorial_style = preprocessed_content.get("editorial_style") or {}
    article = preprocessed_content.get("normalized_content", "")

    user_payload = {
        "editorial_style": editorial_style,
        "article": article,
    }

    return (
        f"{load_editorial_style_prompt()}\n\n"
        "ENTRÉES À ÉVALUER\n"
        f"{json.dumps(user_payload, ensure_ascii=False, indent=2)}"
    )

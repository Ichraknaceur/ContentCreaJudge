"""Prompt builder for the Brief Judge."""

from __future__ import annotations

from pathlib import Path

BRIEF_JUDGE_PROMPT_TEMPLATE = (
    Path(__file__).with_name("prompt.md").read_text(encoding="utf-8").strip()
)


def build_brief_prompt(
    brief: str,
    article: str,
) -> str:
    """Build the Brief Judge prompt."""
    return BRIEF_JUDGE_PROMPT_TEMPLATE.replace("{{BRIEF}}", brief).replace(
        "{{ARTICLE}}", article
    )

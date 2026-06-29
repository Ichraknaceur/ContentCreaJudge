"""LLM client adapter for judge evaluations."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


class LLMClientError(RuntimeError):
    """Raised when the LLM call fails."""


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    """Build the OpenAI client once and reuse it across calls."""
    load_dotenv()
    return OpenAI()


def call_openai_json(
    *,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Call OpenAI and return the raw text response."""
    selected_model = model or os.getenv("OPENAI_EVERGREEN_MODEL", "gpt-4.1-mini")

    try:
        client = _get_client()

        response = client.responses.create(
            model=selected_model,
            input=prompt,
            temperature=temperature,
        )

    except OpenAIError as exc:
        raise LLMClientError(f"OpenAI call failed: {exc}") from exc
    else:
        return response.output_text

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
    max_output_tokens: int | None = None,
) -> str:
    """Call OpenAI and return the raw JSON text response."""
    selected_model = model or os.getenv("OPENAI_EVERGREEN_MODEL", "gpt-4.1-mini")

    request_params: dict[str, object] = {
        "model": selected_model,
        "input": prompt,
        "temperature": temperature,
        "text": {"format": {"type": "json_object"}},
    }

    if max_output_tokens is not None:
        request_params["max_output_tokens"] = max_output_tokens

    try:
        client = _get_client()

        response = client.responses.create(**request_params)

    except OpenAIError as exc:
        raise LLMClientError(f"OpenAI call failed: {exc}") from exc
    else:
        return response.output_text

"""LLM client adapter for judge evaluations."""

from __future__ import annotations

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
    model: str,
    temperature: float = 0.0,
    max_output_tokens: int | None = None,
) -> str:
    """Call OpenAI and return the raw JSON text response.

    The model is resolved by each judge (per-judge env var and default) and
    passed in explicitly; this client only executes the request.
    """
    request_params: dict[str, object] = {
        "model": model,
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

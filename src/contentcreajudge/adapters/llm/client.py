"""LLM client adapter for judge evaluations."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


class LLMClientError(RuntimeError):
    """Raised when the LLM call fails."""


def call_openai_json(
    *,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Call OpenAI and return the raw text response."""
    load_dotenv()

    selected_model = model or os.getenv("OPENAI_DEFAULT_MODEL", "gpt-5.4-mini")

    try:
        client = OpenAI()

        response = client.responses.create(
            model=selected_model,
            input=prompt,
            temperature=temperature,
            text={
                "format": {
                    "type": "json_object",
                }
            },
        )

    except OpenAIError as exc:
        raise LLMClientError(f"OpenAI call failed: {exc}") from exc

    return response.output_text

"""Mistral client adapter for judge evaluations."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from mistralai.client import Mistral


class MistralClientError(RuntimeError):
    """Raised when the Mistral call fails."""


def call_mistral_json(
    *,
    prompt: str,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Call Mistral and return the raw text response."""
    load_dotenv()

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        raise MistralClientError("Missing MISTRAL_API_KEY environment variable.")

    selected_model = model or os.getenv(
        "MISTRAL_DEFAULT_MODEL",
        "mistral-small-latest",
    )

    try:
        client = Mistral(api_key=api_key)

        response = client.chat.complete(
            model=selected_model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

    except Exception as exc:
        raise MistralClientError(f"Mistral call failed: {exc}") from exc

    content = response.choices[0].message.content

    if isinstance(content, list):
        return "".join(
            str(chunk.get("text", "")) for chunk in content if isinstance(chunk, dict)
        )

    return str(content or "")

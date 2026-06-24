"""LLM runner for the persona judge."""

from __future__ import annotations

from contentcreajudge.adapters.llm.client import call_openai_json
from contentcreajudge.adapters.llm.mistral_client import call_mistral_json


class UnsupportedPersonaProviderError(ValueError):
    """Raised when the requested persona LLM provider is unsupported."""


def call_persona_llm(
    *,
    prompt: str,
    provider: str,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Call the selected LLM provider for the persona judge."""
    normalized_provider = provider.lower().strip()

    if normalized_provider == "openai":
        return call_openai_json(
            prompt=prompt,
            model=model,
            temperature=temperature,
        )

    if normalized_provider == "mistral":
        return call_mistral_json(
            prompt=prompt,
            model=model,
            temperature=temperature,
        )

    raise UnsupportedPersonaProviderError(
        f"Unsupported persona LLM provider: {provider}"
    )

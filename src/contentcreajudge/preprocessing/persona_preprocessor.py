"""Preprocessing utilities for the persona judge."""

from __future__ import annotations

import html
import re
from typing import Any


def _normalize_text(content: str) -> str:
    """Remove HTML tags, decode entities and normalize spaces."""
    text_without_html = re.sub(r"<[^>]+>", " ", content)
    decoded_text = html.unescape(text_without_html)
    return re.sub(r"\s+", " ", decoded_text).strip()


def _normalize_persona(persona: dict[str, Any]) -> dict[str, object]:
    """Normalize one persona from platform format to judge format."""
    data = persona.get("data") or {}
    if not isinstance(data, dict):
        data = {}

    persona_fields = data.get("personaFields") or {}
    if not isinstance(persona_fields, dict):
        persona_fields = {}

    persona_id = (
        persona.get("persona_id")
        or persona.get("uuid")
        or data.get("persona_id")
        or data.get("uuid")
    )

    return {
        "persona_id": str(persona_id) if persona_id else None,
        "first_name": data.get("firstName") or persona.get("first_name"),
        "function": data.get("function") or persona.get("function"),
        "organization_id": data.get("organizationId"),
        "active": data.get("active", True),
        "persona_fields": {
            "age": persona_fields.get("age"),
            "income_brackets": persona_fields.get("incomeBrackets"),
            "urban_or_rural": persona_fields.get("urbanOrRural"),
            "family_status": persona_fields.get("familyStatus"),
            "education_level": persona_fields.get("educationLevel"),
            "organization_type": persona_fields.get("organizationType"),
            "persona_type": persona_fields.get("personaType"),
            "professional_objectives": persona_fields.get("professionalObjectives"),
            "problems_frustrations": persona_fields.get("problemsFrustrations"),
            "decision_making_influence": persona_fields.get("decisionMakingInfluence"),
            "touch_point": persona_fields.get("touchPoint"),
            "values_ethic": persona_fields.get("valuesEthic"),
            "information_feeds": persona_fields.get("informationFeeds"),
            "psychological_profile": persona_fields.get("psychologicalProfile"),
            "motivation": persona_fields.get("motivation"),
            "personality": persona_fields.get("personality"),
        },
    }


def _normalize_personas(personas: object) -> list[dict[str, object]]:
    """Normalize all personas safely."""
    if not isinstance(personas, list):
        return []

    normalized_personas: list[dict[str, object]] = []

    for persona in personas:
        if not isinstance(persona, dict):
            continue

        normalized_persona = _normalize_persona(persona)

        if normalized_persona.get("persona_id"):
            normalized_personas.append(normalized_persona)

    return normalized_personas


def preprocess_persona_content(
    content: str,
    context: dict[str, object],
) -> dict[str, object]:
    """Prepare content and personas for persona evaluation."""
    normalized_text = _normalize_text(content)
    personas = _normalize_personas(context.get("personas"))

    return {
        "original_content": content,
        "normalized_text": normalized_text,
        "is_empty": not bool(normalized_text),
        "personas": personas,
        "expected_persona_id": context.get("expected_persona_id"),
        "business_type": context.get("business_type"),
        "content_type": context.get("content_type"),
        "funnel_stage": context.get("funnel_stage"),
        "locale": context.get("locale"),
        "providers": context.get("providers"),
    }

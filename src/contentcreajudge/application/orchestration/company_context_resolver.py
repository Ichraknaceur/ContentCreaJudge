"""Resolve reusable evaluation context from a company export ZIP."""

from __future__ import annotations

import json
import logging
import zipfile
from io import BytesIO
from typing import Any
from urllib.parse import urlparse

EXPORTED_HTML_QUOTE_WRAPPER_LENGTH = 2
logger = logging.getLogger(__name__)

SUPPORTED_FOLDERS = {
    "organization",
    "topic",
    "content",
    "contentVersion",
    "plan",
    "persona",
    "theme",
}


def _normalize_organization_website(url: str) -> str:
    """Return the canonical organization website origin."""
    cleaned_url = url.strip()

    if not cleaned_url:
        return "https://contentcrea.com"

    parsed_url = urlparse(cleaned_url)

    if not parsed_url.scheme or not parsed_url.netloc:
        return cleaned_url

    return f"{parsed_url.scheme}://{parsed_url.netloc}"


def _get_traceability_creation_date(document: dict[str, Any]) -> str:
    """Return creation date from traceability when available."""
    traceability = document.get("traceability")
    if not isinstance(traceability, dict):
        return ""

    return str(traceability.get("creationDate", ""))


def load_company_export_from_zip(zip_bytes: bytes) -> dict[str, object]:
    """Load supported JSON documents from a company export ZIP."""
    documents_by_type: dict[str, list[dict[str, Any]]] = {
        folder: [] for folder in SUPPORTED_FOLDERS
    }

    try:
        archive = zipfile.ZipFile(_bytes_to_file_like(zip_bytes))
    except zipfile.BadZipFile as error:
        raise ValueError("Invalid ZIP file.") from error

    with archive:
        for file_name in archive.namelist():
            if not file_name.endswith(".json"):
                continue

            folder = file_name.split("/", maxsplit=1)[0]

            if folder not in SUPPORTED_FOLDERS:
                continue

            try:
                document = json.loads(archive.read(file_name).decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                logger.debug(
                    "Skipping invalid exported JSON file %s: %s",
                    file_name,
                    error,
                )
                continue

            if isinstance(document, dict):
                documents_by_type[folder].append(document)

    return {
        "organization": _first(documents_by_type["organization"]),
        "topics": documents_by_type["topic"],
        "contents": documents_by_type["content"],
        "content_versions": documents_by_type["contentVersion"],
        "plans": documents_by_type["plan"],
        "personas": documents_by_type["persona"],
        "themes": documents_by_type["theme"],
    }


def build_global_payload_from_content(
    company_export: dict[str, object],
    content_id: str,
    *,
    profile: str = "default",
    request_id: str | None = None,
) -> dict[str, object]:
    """Build a global evaluation payload from one exported content."""
    contents = _as_document_list(company_export.get("contents"))
    topics = _as_document_list(company_export.get("topics"))
    content_versions = _as_document_list(company_export.get("content_versions"))

    organization = company_export.get("organization")
    if not isinstance(organization, dict):
        organization = {}

    selected_content = _find_document_by_uuid(contents, content_id)
    content_data = _get_data(selected_content)

    topic_id = str(content_data.get("topicId", ""))
    selected_topic = _find_document_by_uuid(topics, topic_id)
    topic_data = _get_data(selected_topic)

    selected_content_version = _find_latest_content_version_for_content(
        content_versions,
        content_id,
    )
    content_version_data = _get_data(selected_content_version)

    organization_data = _get_data(organization)
    organization_identity = organization_data.get("identity", {})
    if not isinstance(organization_identity, dict):
        organization_identity = {}

    organization_website = _normalize_organization_website(
        str(organization_identity.get("website") or "https://contentcrea.com"),
    )

    generated_content = _clean_exported_html(str(content_data.get("body", "")))
    expected_outline_html = _clean_exported_html(
        str(content_version_data.get("body", "")),
    )

    context = {
        "content_type": topic_data.get("contentType") or "articles",
        "expected_length": topic_data.get("length") or "MEDIUM",
        "locale": "fr-FR",
        "funnel_stage": topic_data.get("funnelStage") or "AWARENESS",
        "main_keyword": content_data.get("principalKeyword") or "",
        "secondary_keywords": [],
        "long_tail_keywords": [],
        "expected_outline_html": expected_outline_html,
        "evergreen": topic_data.get("evergreen"),
        "expected_cta": content_data.get("cta"),
        "require_sources": True,
        "organization_website": organization_website,
        "organization_domain": organization_website,
    }

    payload: dict[str, object] = {
        "content": generated_content,
        "profile": profile,
        "context": context,
        "enabled_judges": [
            "length",
            "typography",
            "seo",
            "structure",
            "sources",
        ],
    }

    if request_id:
        payload["request_id"] = request_id

    return payload


def list_exported_contents(company_export: dict[str, object]) -> list[dict[str, str]]:
    """Return lightweight content options for UI selection."""
    contents = _as_document_list(company_export.get("contents"))

    options: list[dict[str, str]] = []

    for content in contents:
        content_data = _get_data(content)
        content_id = str(content.get("uuid", ""))
        title = str(content_data.get("title") or content_id)

        if not content_id:
            continue

        options.append(
            {
                "id": content_id,
                "label": title,
            },
        )

    return options


def _as_document_list(value: object) -> list[dict[str, Any]]:
    """Return value as a list of dict documents."""
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, dict)]


def _get_data(document: object) -> dict[str, Any]:
    """Return the data field from an exported document."""
    if not isinstance(document, dict):
        return {}

    data = document.get("data")
    return data if isinstance(data, dict) else {}


def _find_document_by_uuid(
    documents: list[dict[str, Any]],
    document_id: str,
) -> dict[str, Any]:
    """Find a document by UUID."""
    for document in documents:
        if str(document.get("uuid", "")) == document_id:
            return document

    return {}


def _find_latest_content_version_for_content(
    content_versions: list[dict[str, Any]],
    content_id: str,
) -> dict[str, Any]:
    """Find the latest content version linked to a content."""
    matching_versions = [
        version
        for version in content_versions
        if str(_get_data(version).get("contentId", "")) == content_id
    ]

    if not matching_versions:
        return {}

    return sorted(
        matching_versions,
        key=_get_traceability_creation_date,
        reverse=True,
    )[0]


def _clean_exported_html(value: str) -> str:
    """Clean HTML strings exported with extra JSON quotes."""
    cleaned_value = value.strip()

    if (
        len(cleaned_value) >= EXPORTED_HTML_QUOTE_WRAPPER_LENGTH
        and cleaned_value[0] == '"'
        and cleaned_value[-1] == '"'
    ):
        cleaned_value = cleaned_value[1:-1]

    return cleaned_value.replace('\\"', '"').replace("\\n", "\n").replace("\\/", "/")


def _bytes_to_file_like(zip_bytes: bytes) -> BytesIO:
    """Return a file-like object from bytes."""
    return BytesIO(zip_bytes)


def _first(items: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the first item from a list."""
    return items[0] if items else None

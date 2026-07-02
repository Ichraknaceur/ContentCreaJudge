from __future__ import annotations

import json
import zipfile
from io import BytesIO

from contentcreajudge.application.orchestration.company_context_resolver import (
    build_global_payload_from_content,
    list_exported_contents,
    load_company_export_from_zip,
)


def _build_test_zip(
    *, organization_website: str = "https://liris.cnrs.fr/liris"
) -> bytes:
    """Build a minimal company export ZIP for resolver tests."""
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, mode="w") as archive:
        archive.writestr(
            "organization/organization_1.json",
            json.dumps(
                {
                    "documentType": "organization",
                    "uuid": "org-1",
                    "data": {
                        "identity": {
                            "name": "LIRIS",
                            "website": organization_website,
                        },
                    },
                },
            ),
        )
        archive.writestr(
            "topic/topic_1.json",
            json.dumps(
                {
                    "documentType": "topic",
                    "uuid": "topic-1",
                    "data": {
                        "name": "Topic test",
                        "contentType": "articles",
                        "length": "MEDIUM",
                        "funnelStage": "AWARENESS",
                        "evergreen": True,
                    },
                },
            ),
        )
        archive.writestr(
            "content/content_1.json",
            json.dumps(
                {
                    "documentType": "content",
                    "uuid": "content-1",
                    "data": {
                        "title": "Article test",
                        "topicId": "topic-1",
                        "body": "<p>Contenu généré.</p>",
                        "principalKeyword": "mot-clé principal",
                        "cta": "Lire la suite",
                    },
                },
            ),
        )
        archive.writestr(
            "contentVersion/content_version_1.json",
            json.dumps(
                {
                    "documentType": "contentVersion",
                    "uuid": "version-1",
                    "traceability": {"creationDate": "2026-05-18T10:00:00Z"},
                    "data": {
                        "contentId": "content-1",
                        "body": "<h2>Plan attendu</h2>",
                    },
                },
            ),
        )
        archive.writestr(
            "ignored/file.txt",
            "not json",
        )

    return zip_buffer.getvalue()


def test_load_company_export_from_zip_reads_supported_documents() -> None:
    result = load_company_export_from_zip(_build_test_zip())

    assert isinstance(result["organization"], dict)
    assert result["organization"]["uuid"] == "org-1"

    topics = result["topics"]
    assert isinstance(topics, list)
    assert len(topics) == 1
    assert topics[0]["uuid"] == "topic-1"

    contents = result["contents"]
    assert isinstance(contents, list)
    assert len(contents) == 1
    assert contents[0]["uuid"] == "content-1"

    content_versions = result["content_versions"]
    assert isinstance(content_versions, list)
    assert len(content_versions) == 1
    assert content_versions[0]["uuid"] == "version-1"


def test_list_exported_contents_returns_ui_options() -> None:
    company_export = load_company_export_from_zip(_build_test_zip())

    options = list_exported_contents(company_export)

    assert options == [
        {
            "id": "content-1",
            "label": "Article test",
        },
    ]


def test_build_global_payload_from_content_uses_zip_data() -> None:
    company_export = load_company_export_from_zip(_build_test_zip())

    payload = build_global_payload_from_content(
        company_export,
        "content-1",
        request_id="test-001",
    )

    context = payload["context"]

    assert payload["request_id"] == "test-001"
    assert payload["content"] == "<p>Contenu généré.</p>"
    assert payload["profile"] == "default"

    assert context["content_type"] == "articles"
    assert context["expected_length"] == "MEDIUM"
    assert context["locale"] == "fr-FR"
    assert context["funnel_stage"] == "AWARENESS"
    assert context["main_keyword"] == "mot-clé principal"
    assert context["secondary_keywords"] == []
    assert context["long_tail_keywords"] == []
    assert context["expected_outline_html"] == "<h2>Plan attendu</h2>"
    assert context["evergreen"] is True
    assert context["expected_cta"] == "Lire la suite"
    assert context["require_sources"] is True
    assert context["organization_website"] == "https://liris.cnrs.fr"
    assert context["organization_domain"] == "https://liris.cnrs.fr"


def test_build_global_payload_from_content_enables_global_judges() -> None:
    company_export = load_company_export_from_zip(_build_test_zip())

    payload = build_global_payload_from_content(company_export, "content-1")

    assert payload["enabled_judges"] == [
        "length",
        "typography",
        "seo",
        "structure",
        "sources",
    ]


def test_build_global_payload_from_content_falls_back_when_organization_website_is_empty() -> (
    None
):
    company_export = load_company_export_from_zip(
        _build_test_zip(organization_website=""),
    )

    payload = build_global_payload_from_content(company_export, "content-1")

    context = payload["context"]

    assert context["organization_website"] == "https://contentcrea.com"
    assert context["organization_domain"] == "https://contentcrea.com"

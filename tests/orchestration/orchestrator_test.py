from __future__ import annotations

import json
import zipfile
from io import BytesIO

import pytest

from contentcreajudge.application.orchestration import judge_registry
from contentcreajudge.application.orchestration.company_context_resolver import (
    build_global_payload_from_content,
    load_company_export_from_zip,
)
from contentcreajudge.application.orchestration.orchestrator import (
    _build_judge_results,
    execute_global_evaluation,
)


def _build_orchestration_test_zip() -> bytes:
    """Build a minimal company ZIP compatible with global orchestration tests."""
    zip_buffer = BytesIO()

    article_body = "<p>" + "mot " * 1200 + "</p><h2>Conclusion</h2><p>Fin.</p>"

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
                            "website": "https://liris.cnrs.fr/liris",
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
                        "body": article_body,
                        "principalKeyword": "mot clé principal",
                        "cta": "Read more",
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
                        "body": "<p>Introduction attendue.</p><h2>Conclusion</h2>",
                    },
                },
            ),
        )

    return zip_buffer.getvalue()


@pytest.mark.asyncio
async def test_execute_global_evaluation_with_length_pass() -> None:
    payload = {
        "content": "<p>" + "mot " * 1200 + "</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "enabled_judges": ["length"],
    }

    result = await execute_global_evaluation(payload)

    assert result["status"] == "completed"
    assert result["score"] is None
    assert result["judge_results"][0]["judge"] == "length"
    assert result["judge_results"][0]["status"] == "pass"
    assert result["judge_results"][0]["score"] == 100


@pytest.mark.asyncio
async def test_execute_global_evaluation_with_length_fail() -> None:
    payload = {
        "content": "<p>Texte trop court.</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "enabled_judges": ["length"],
    }

    result = await execute_global_evaluation(payload)

    assert result["status"] == "completed"
    assert result["score"] is None
    assert result["judge_results"][0]["judge"] == "length"
    assert result["judge_results"][0]["status"] == "fail"
    assert result["judge_results"][0]["score"] == 0


@pytest.mark.asyncio
async def test_execute_global_evaluation_ignores_unknown_judge() -> None:
    payload = {
        "content": "<p>" + "mot " * 1200 + "</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "enabled_judges": ["unknown"],
    }

    result = await execute_global_evaluation(payload)

    assert result["status"] == "completed"
    assert result["score"] is None
    assert result["judge_results"] == []
    assert result["dimension_results"] == []
    assert result["technical_errors"] == []
    assert result["metadata"]["skipped_judges"] == ["unknown"]


@pytest.mark.asyncio
async def test_execute_global_evaluation_reports_failed_judge_in_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _failing_flow(_payload: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("boom")

    monkeypatch.setitem(judge_registry.JUDGE_REGISTRY, "length", _failing_flow)

    payload = {
        "content": "<p>Texte.</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
        },
        "enabled_judges": ["length"],
    }

    result = await execute_global_evaluation(payload)

    length_entry = next(
        judge_result
        for judge_result in result["judge_results"]
        if judge_result["judge"] == "length"
    )
    assert length_entry["status"] == "error"
    assert length_entry["error"] == "boom"
    assert length_entry["score"] is None
    assert result["technical_errors"]


@pytest.mark.asyncio
async def test_execute_global_evaluation_returns_global_preprocessing() -> None:
    payload = {
        "content": """
        <p>Introduction avec un lien brut https://example.org.</p>
        <h2>Conclusion</h2>
        <p>Conclusion de test.</p>
        <p class="cta"><strong>Read more</strong></p>
        """,
        "profile": "default",
        "context": {
            "content_type": "articles",
            "expected_length": "MEDIUM",
            "locale": "fr-FR",
            "organization_domain": "https://contentcrea.com",
        },
        "enabled_judges": ["length"],
    }

    result = await execute_global_evaluation(payload)

    assert "global_preprocessing" in result

    preprocessing = result["global_preprocessing"]

    assert preprocessing["word_count"] > 0
    assert preprocessing["is_empty"] is False
    assert preprocessing["conclusion"] == "Conclusion de test. Read more"

    cta = preprocessing["cta"]
    assert cta["has_cta"] is True
    assert cta["cta_count"] == 1

    links = preprocessing["links"]
    assert links["raw_urls_count"] == 1


@pytest.mark.asyncio
async def test_execute_global_evaluation_from_company_zip_payload() -> None:
    company_export = load_company_export_from_zip(_build_orchestration_test_zip())

    payload = build_global_payload_from_content(
        company_export,
        "content-1",
        request_id="zip-test-001",
    )

    # Keep this integration test light and deterministic.
    # SEO and sources may require heavier dependencies/network checks.
    payload["enabled_judges"] = ["length", "typography", "structure"]

    result = await execute_global_evaluation(payload)

    judge_results = result["judge_results"]
    judge_names = {judge_result["judge"] for judge_result in judge_results}

    assert result["evaluation_id"] == "zip-test-001"
    assert result["status"] == "completed"
    assert result["technical_errors"] == []

    assert judge_names == {"length", "typography", "structure"}

    assert result["global_preprocessing"]["word_count"] >= 1200

    length_result = next(
        judge_result
        for judge_result in judge_results
        if judge_result["judge"] == "length"
    )
    assert length_result["status"] == "pass"
    assert length_result["score"] == 100


def test_build_judge_results_keeps_subscores() -> None:
    dimension_results = [
        {
            "dimension": "seo",
            "status": "warn",
            "score": 74,
            "subscores": {
                "lexical": 70,
                "semantic": 70,
                "overoptimization": 100,
            },
            "findings": [],
        }
    ]

    result = _build_judge_results(dimension_results)

    assert result[0]["judge"] == "seo"
    assert result[0]["status"] == "warn"
    assert result[0]["score"] == 74
    assert result[0]["subscores"]["lexical"] == 70
    assert result[0]["subscores"]["semantic"] == 70
    assert result[0]["subscores"]["overoptimization"] == 100


def test_build_judge_results_fallbacks_invalid_findings() -> None:
    dimension_results = [
        {
            "dimension": "seo",
            "status": "warn",
            "score": 74,
            "findings": "invalid",
        }
    ]

    result = _build_judge_results(dimension_results)

    assert result[0]["findings"] == []

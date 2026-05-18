from __future__ import annotations

import pytest

from contentcreajudge.application.orchestration.orchestrator import (
    _build_judge_results,
    execute_global_evaluation,
)


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

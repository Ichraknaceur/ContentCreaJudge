"""Tests for CTA evaluation flow."""

from __future__ import annotations

import pytest

from contentcreajudge.application.judge_flow.cta_flow import execute_cta_flow


def test_execute_cta_flow_with_valid_cta() -> None:
    payload = {
        "content": '<p>Intro</p><p class="cta"><strong>Read more</strong></p>',
        "profile": "default",
        "context": {
            "content_type": "articles",
            "funnel_stage": "AWARENESS",
            "expected_cta": "Read more",
            "content_purpose": "Sensibilisation",
            "language": "en",
        },
    }

    result = execute_cta_flow(payload)

    assert result["rule_resolution"]["enabled_judges"] == ["cta"]
    assert result["preprocessing"]["cta_count"] == 1
    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"


def test_execute_cta_flow_with_missing_cta() -> None:
    payload = {
        "content": "<p>Intro</p><p>Conclusion</p>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "funnel_stage": "AWARENESS",
            "expected_cta": "Read more",
            "content_purpose": "Sensibilisation",
            "language": "en",
        },
    }

    result = execute_cta_flow(payload)

    assert result["preprocessing"]["cta_count"] == 0
    assert result["judge_result"]["status"] == "fail"
    assert result["aggregation"]["status"] == "fail"


def test_execute_cta_flow_with_complementary_reading_without_read_more_cta() -> None:
    payload = {
        "content": "<p>Intro</p><h2>Lecture complémentaire</h2><ul><li>Article</li></ul>",
        "profile": "default",
        "context": {
            "content_type": "articles",
            "funnel_stage": "AWARENESS",
            "expected_cta": "Read more",
            "content_purpose": "Sensibilisation",
            "language": "en",
        },
    }

    result = execute_cta_flow(payload)

    assert result["preprocessing"]["has_complementary_reading"] is True
    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"


def test_execute_cta_flow_keeps_request_echo() -> None:
    payload = {
        "content": '<p>Intro</p><p class="cta"><strong>Read more</strong></p>',
        "profile": "default",
        "request_id": "cta-test-001",
        "context": {
            "content_type": "articles",
            "funnel_stage": "AWARENESS",
            "expected_cta": "Read more",
            "language": "en",
        },
    }

    result = execute_cta_flow(payload)

    assert result["request_echo"]["profile"] == "default"
    assert result["request_echo"]["request_id"] == "cta-test-001"
    assert result["request_echo"]["context"]["expected_cta"] == "Read more"


def test_execute_cta_flow_raises_error_when_context_is_not_a_dictionary() -> None:
    payload = {
        "content": '<p>Intro</p><p class="cta"><strong>Read more</strong></p>',
        "profile": "default",
        "context": "invalid-context",
    }

    with pytest.raises(TypeError, match=r"context must be a dictionary\."):
        execute_cta_flow(payload)

"""Tests for the funnel evaluation flow."""

from __future__ import annotations

from contentcreajudge.application.judge_flow.funnel_flow import execute_funnel_flow


def test_execute_funnel_flow_runs_openai_and_mistral(monkeypatch) -> None:
    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.resolve_funnel_rules",
        lambda context: {"expected_funnel": "awareness"},
    )
    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.preprocess_funnel_content",
        lambda content: {
            "original_content": content,
            "normalized_text": "Contenu pédagogique.",
            "word_count": 2,
            "is_empty": False,
        },
    )

    def fake_run_funnel_judge(
        content, judge_rules, *, provider="openai", model=None, temperature=0.0
    ):
        return {
            "dimension": "funnel",
            "status": "pass" if provider == "openai" else "warn",
            "score": 90 if provider == "openai" else 72,
            "provider": provider,
            "findings": [],
        }

    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.run_funnel_judge",
        fake_run_funnel_judge,
    )
    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.aggregate_funnel_result",
        lambda judge_result: {
            "status": judge_result["status"],
            "score": judge_result["score"],
            "summary": "ok",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        },
    )

    result = execute_funnel_flow(
        {
            "content": "<p>Contenu pédagogique.</p>",
            "profile": "default",
            "context": {"expected_funnel": "awareness"},
        }
    )

    assert result["judge_results"]["openai"]["provider"] == "openai"
    assert result["judge_results"]["mistral"]["provider"] == "mistral"
    assert result["aggregations"]["openai"]["status"] == "pass"
    assert result["aggregations"]["mistral"]["status"] == "warn"
    assert result["preprocessing"]["normalized_text"] == "Contenu pédagogique."


def test_execute_funnel_flow_uses_env_models_by_not_passing_model(monkeypatch) -> None:
    called_models = {}

    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.resolve_funnel_rules",
        lambda context: {"expected_funnel": "awareness"},
    )
    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.preprocess_funnel_content",
        lambda content: {
            "original_content": content,
            "normalized_text": content,
            "word_count": 1,
            "is_empty": False,
        },
    )

    def fake_run_funnel_judge(
        content, judge_rules, *, provider="openai", model=None, temperature=0.0
    ):
        called_models[provider] = model
        return {
            "dimension": "funnel",
            "status": "pass",
            "score": 90,
            "provider": provider,
            "findings": [],
        }

    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.run_funnel_judge",
        fake_run_funnel_judge,
    )
    monkeypatch.setattr(
        "contentcreajudge.application.judge_flow.funnel_flow.aggregate_funnel_result",
        lambda judge_result: {
            "status": judge_result["status"],
            "score": judge_result["score"],
            "summary": "ok",
            "dimension_results": [judge_result],
            "blocking_issues": [],
        },
    )

    result = execute_funnel_flow(
        {
            "content": "Texte",
            "context": {"expected_funnel": "awareness"},
        }
    )

    assert called_models["openai"] is None
    assert called_models["mistral"] is None
    assert result["judge_results"]["openai"]["status"] == "pass"
    assert result["judge_results"]["mistral"]["status"] == "pass"

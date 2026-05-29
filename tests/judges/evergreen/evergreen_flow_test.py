import json

import pytest

from contentcreajudge.application.judge_flow.evergreen_flow import (
    execute_evergreen_flow,
)


def _mock_llm_response(
    monkeypatch: pytest.MonkeyPatch,
    *,
    score: int,
    passages: list[dict[str, object]] | None = None,
) -> None:
    payload = {
        "scores": {
            "dependance_temporelle": 3,
            "stabilite_informations": 3,
            "utilite_durable": 3,
            "besoin_mise_a_jour": 3,
            "reutilisabilite_editoriale": 3,
        },
        "score_global_evergreen": score,
        "niveau": "moyen",
        "passages_problematiques": passages or [],
        "informations_a_surveiller": [],
        "justification_courte": "Evaluation de test.",
        "recommandations": [],
    }

    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(payload),
    )


def test_execute_evergreen_flow_with_evergreen_true_and_unprovided_year(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(
        monkeypatch,
        score=30,
        passages=[
            {
                "extrait": "En 2024",
                "probleme": "Reference temporelle forte.",
                "gravite": "forte",
            },
        ],
    )
    payload = {
        "content": "En 2024, les pratiques editoriales evoluent.",
        "profile": "default",
        "request_id": "req-1",
        "context": {
            "evergreen": True,
            "locale": "fr-FR",
            "allowed_dates": [],
            "allowed_temporal_references": [],
        },
    }

    result = execute_evergreen_flow(payload)

    assert result["request_echo"]["content"] == payload["content"]
    assert result["request_echo"]["profile"] == "default"
    assert result["request_echo"]["request_id"] == "req-1"
    assert result["rule_resolution"]["enabled_judges"] == ["evergreen"]
    assert result["preprocessing"]["temporal_references_count"] >= 1
    assert result["judge_result"]["dimension"] == "evergreen"
    assert result["judge_result"]["status"] == "fail"
    assert result["aggregation"]["status"] == "fail"
    assert result["message"].startswith("Evergreen flow complete")


def test_execute_evergreen_flow_with_evergreen_false_returns_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=60)
    payload = {
        "content": "En 2024, les pratiques editoriales evoluent.",
        "profile": "default",
        "context": {
            "evergreen": False,
            "locale": "fr-FR",
        },
    }

    result = execute_evergreen_flow(payload)

    assert result["judge_result"]["status"] == "warn"
    assert result["judge_result"]["score"] == 60
    assert result["aggregation"]["status"] == "warn"


def test_execute_evergreen_flow_allows_input_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=85)
    payload = {
        "content": "Le cadre editorial a ete defini en 2024.",
        "profile": "default",
        "context": {
            "evergreen": True,
            "locale": "fr-FR",
            "allowed_dates": ["2024"],
        },
    }

    result = execute_evergreen_flow(payload)

    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"


def test_execute_evergreen_flow_allows_source_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=85)
    payload = {
        "content": "Selon une etude de 2024, les usages editoriaux evoluent.",
        "profile": "default",
        "context": {
            "evergreen": True,
            "locale": "fr-FR",
        },
    }

    result = execute_evergreen_flow(payload)

    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"


def test_execute_evergreen_flow_with_missing_context_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=30)
    payload = {
        "content": "En 2024, le sujet evolue.",
        "profile": "default",
    }

    result = execute_evergreen_flow(payload)

    assert result["request_echo"]["context"] == {}
    assert result["judge_result"]["dimension"] == "evergreen"
    assert "aggregation" in result


def test_execute_evergreen_flow_with_invalid_context_type_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=30)
    payload = {
        "content": "En 2024, le sujet evolue.",
        "profile": "default",
        "context": "invalid-context",
    }

    result = execute_evergreen_flow(payload)

    assert result["request_echo"]["context"] == {}
    assert result["judge_result"]["dimension"] == "evergreen"
    assert "aggregation" in result


def test_execute_evergreen_flow_with_empty_payload_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=85)

    result = execute_evergreen_flow({})

    assert result["request_echo"]["content"] == ""
    assert result["request_echo"]["profile"] == "default"
    assert result["request_echo"]["request_id"] is None
    assert result["preprocessing"]["is_empty"] is True
    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"

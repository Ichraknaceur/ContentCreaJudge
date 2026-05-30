import json
from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from contentcreajudge.api.app import create_app

if TYPE_CHECKING:
    import pytest


def _mock_llm_response(monkeypatch: pytest.MonkeyPatch, *, score: int) -> None:
    payload = {
        "scores": {},
        "score_global_evergreen": score,
        "niveau": "moyen",
        "passages_problematiques": [],
        "informations_a_surveiller": [],
        "justification_courte": "Evaluation de test.",
        "recommandations": [],
    }

    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(payload),
    )


def test_evergreen_api_returns_200_with_valid_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=30)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/evergreen/evaluate",
        json={
            "content": "En 2024, les pratiques éditoriales évoluent.",
            "profile": "default",
            "context": {
                "evergreen": True,
                "locale": "fr-FR",
            },
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["judge_result"]["dimension"] == "evergreen"
    assert body["aggregation"]["status"] == "fail"


def test_evergreen_api_uses_fallbacks_with_minimal_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_llm_response(monkeypatch, score=85)
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/evergreen/evaluate",
        json={},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["request_echo"]["content"] == ""
    assert body["request_echo"]["profile"] == "default"
    assert body["preprocessing"]["is_empty"] is True
    assert body["judge_result"]["status"] == "pass"


def test_evergreen_api_rejects_unknown_top_level_field() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/judges/evergreen/evaluate",
        json={
            "content": "Texte.",
            "profile": "default",
            "context": {
                "evergreen": True,
            },
            "unknown_field": "not allowed",
        },
    )

    assert response.status_code == 422

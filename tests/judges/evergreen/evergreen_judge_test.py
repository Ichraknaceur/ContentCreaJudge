from __future__ import annotations

import json
from typing import TYPE_CHECKING

from contentcreajudge.adapters.llm.client import LLMClientError
from contentcreajudge.judges.evergreen.evergreen_judge import run_evergreen_judge

if TYPE_CHECKING:
    import pytest

    from contentcreajudge.preprocessing.evergreen_preprocessor import (
        EvergreenPreprocessingResult,
    )


def _rules() -> dict[str, object]:
    return {
        "prompt_template": "Content:\n{{CONTENT}}\nSignals:\n{{TEMPORAL_SIGNALS}}",
        "llm": {
            "model_env_var": "OPENAI_EVERGREEN_MODEL",
            "default_model": "gpt-4.1-mini",
            "temperature": 0.0,
        },
        "scoring": {
            "pass_min_score": 70,
            "warn_min_score": 50,
        },
        "llm_messages": {
            "llm_error": "The evergreen evaluation could not be completed reliably.",
        },
    }


def _preprocessed() -> EvergreenPreprocessingResult:
    return {
        "original_content": "Original content",
        "normalized_text": "Normalized content",
        "locale_key": "fr",
        "temporal_references": [
            {
                "value": "2024",
                "type": "year",
                "start": 0,
                "end": 4,
                "context": "En 2024",
                "is_in_source_context": False,
                "is_historical_context": False,
                "is_in_input": False,
            },
        ],
        "temporal_references_count": 1,
        "is_empty": False,
    }


def _llm_payload(
    *,
    score: int = 85,
    passages: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "scores": {
            "dependance_temporelle": 4,
            "stabilite_informations": 4,
            "utilite_durable": 5,
            "besoin_mise_a_jour": 4,
            "reutilisabilite_editoriale": 5,
        },
        "score_global_evergreen": score,
        "niveau": "excellent",
        "passages_problematiques": passages or [],
        "informations_a_surveiller": [],
        "justification_courte": "Contenu durable.",
        "recommandations": [],
    }


def test_run_evergreen_judge_returns_pass_from_llm_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_call_openai_json(**kwargs: object) -> str:
        assert kwargs["model"] == "gpt-4.1-mini"
        assert kwargs["temperature"] == 0.0
        prompt = str(kwargs["prompt"])
        assert "Normalized content" in prompt
        assert '"temporal_references_count": 1' in prompt
        return json.dumps(_llm_payload(score=85))

    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        fake_call_openai_json,
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["dimension"] == "evergreen"
    assert result["status"] == "pass"
    assert result["score"] == 85
    assert result["findings"] == []
    assert result["llm_evaluation"]["score_global_evergreen"] == 85
    assert result["llm_raw_response"]


def test_run_evergreen_judge_returns_warn_from_scoring_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(_llm_payload(score=60)),
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["status"] == "warn"
    assert result["score"] == 60


def test_run_evergreen_judge_returns_fail_from_low_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(_llm_payload(score=30)),
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["status"] == "fail"
    assert result["score"] == 30


def test_run_evergreen_judge_downgrades_fail_to_warn_when_not_evergreen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rules = _rules()
    rules["evergreen_required"] = False
    rules["activation"] = {"downgrade_to_warning_when_evergreen_false": True}

    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(_llm_payload(score=30)),
    )

    result = run_evergreen_judge(_preprocessed(), rules)

    assert result["status"] == "warn"
    assert result["score"] == 30


def test_run_evergreen_judge_keeps_fail_when_evergreen_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rules = _rules()
    rules["evergreen_required"] = True
    rules["activation"] = {"downgrade_to_warning_when_evergreen_false": True}

    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(_llm_payload(score=30)),
    )

    result = run_evergreen_judge(_preprocessed(), rules)

    assert result["status"] == "fail"


def test_run_evergreen_judge_builds_findings_from_problematic_passages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passages = [
        {
            "extrait": "prix 2024",
            "probleme": "Information tarifaire datée.",
            "gravite": "forte",
        },
    ]
    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(_llm_payload(score=45, passages=passages)),
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["findings"] == [
        {
            "rule_id": "evergreen.llm.problematic_passage",
            "severity": "forte",
            "message": "Information tarifaire datée.",
            "evidence": {"extrait": "prix 2024"},
        },
    ]


def test_run_evergreen_judge_parses_json_inside_markdown_fence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_response = f"```json\n{json.dumps(_llm_payload(score=72))}\n```"
    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: raw_response,
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["status"] == "pass"
    assert result["score"] == 72


def test_run_evergreen_judge_uses_alternate_score_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _llm_payload(score=0)
    payload.pop("score_global_evergreen")
    payload["score_global"] = 55
    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: json.dumps(payload),
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["status"] == "warn"
    assert result["score"] == 55


def test_run_evergreen_judge_returns_error_when_prompt_template_is_missing() -> None:
    rules = _rules()
    rules["prompt_template"] = ""

    result = run_evergreen_judge(_preprocessed(), rules)

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["findings"][0]["rule_id"] == "evergreen.llm_error"
    assert result["findings"][0]["message"] == (
        "The evergreen evaluation could not be completed reliably."
    )
    assert result["findings"][0]["evidence"] == {
        "error": "Missing prompt_template in evergreen rules.",
    }
    assert result["llm_evaluation"] == {}
    assert result["llm_raw_response"] == ""


def test_run_evergreen_judge_returns_error_when_llm_call_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_llm_error(**_kwargs: object) -> str:
        raise LLMClientError("OpenAI call failed")

    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        raise_llm_error,
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["status"] == "fail"
    assert result["findings"][0]["rule_id"] == "evergreen.llm_error"
    assert result["findings"][0]["evidence"] == {"error": "OpenAI call failed"}


def test_run_evergreen_judge_returns_error_when_llm_json_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        lambda **_kwargs: "not json",
    )

    result = run_evergreen_judge(_preprocessed(), _rules())

    assert result["status"] == "fail"
    assert result["findings"][0]["rule_id"] == "evergreen.llm_error"
    assert result["findings"][0]["evidence"] == {
        "error": "LLM response is not valid JSON.",
    }


def test_run_evergreen_judge_uses_original_content_when_normalized_text_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    preprocessed = _preprocessed()
    preprocessed["normalized_text"] = ""

    def fake_call_openai_json(**kwargs: object) -> str:
        assert "Original content" in str(kwargs["prompt"])
        return json.dumps(_llm_payload(score=80))

    monkeypatch.setattr(
        "contentcreajudge.judges.evergreen.evergreen_judge.call_openai_json",
        fake_call_openai_json,
    )

    result = run_evergreen_judge(preprocessed, _rules())

    assert result["status"] == "pass"

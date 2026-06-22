"""Tests for the editorial style judge."""

from __future__ import annotations

from typing import Any

from contentcreajudge.judges.editorial_style.editorial_style_judge import (
    run_editorial_style_judge,
)


def _rules() -> dict[str, object]:
    return {
        "judge_id": "editorial_style",
        "criteria": {
            "style_alignment": {"weight": 0.20},
            "reasoning_alignment": {"weight": 0.20},
            "concept_handling": {"weight": 0.15},
            "expression_control": {"weight": 0.15},
            "writing_conventions": {"weight": 0.15},
            "example_alignment": {"weight": 0.15},
        },
        "thresholds": {"pass_score": 80, "warn_score": 60},
        "severity_policy": {
            "critical_forces_status": "fail",
            "major_max_status": "warn",
        },
    }


def _preprocessed_content() -> dict[str, object]:
    return {
        "normalized_content": "Article à juger.",
        "editorial_style": {
            "writingStyle": "Style attendu.",
            "writeLikeThis": "Bon exemple.",
            "notLikeThis": "Mauvais exemple.",
        },
    }


def test_run_editorial_style_judge_returns_final_pass(
    monkeypatch: Any,
) -> None:
    """It should return a final pass result when both providers pass."""
    response = """
    {
      "criteria_scores": {
        "style_alignment": 90,
        "reasoning_alignment": 85,
        "concept_handling": 88,
        "expression_control": 86,
        "writing_conventions": 84,
        "example_alignment": 90
      },
      "findings": [],
      "summary": "Article bien aligné."
    }
    """

    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_openai_json",
        lambda **kwargs: response,
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_mistral_json",
        lambda **kwargs: response,
    )

    result = run_editorial_style_judge(_preprocessed_content(), _rules())

    assert result["dimension"] == "editorial_style"
    assert result["status"] == "pass"
    assert result["score"] == 87
    assert result["agreement"] is True
    assert result["score_gap"] == 0
    assert result["criteria_scores"]["style_alignment"] == 90
    assert result["findings"] == []
    assert "providers" in result


def test_run_editorial_style_judge_returns_warn_when_one_provider_warns(
    monkeypatch: Any,
) -> None:
    """It should return warn when one provider warns."""
    openai_response = """
    {
      "criteria_scores": {
        "style_alignment": 90,
        "reasoning_alignment": 90,
        "concept_handling": 90,
        "expression_control": 90,
        "writing_conventions": 90,
        "example_alignment": 90
      },
      "findings": [],
      "summary": "Article aligné."
    }
    """

    mistral_response = """
    {
      "criteria_scores": {
        "style_alignment": 70,
        "reasoning_alignment": 70,
        "concept_handling": 70,
        "expression_control": 70,
        "writing_conventions": 70,
        "example_alignment": 70
      },
      "findings": [],
      "summary": "Alignement partiel."
    }
    """

    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_openai_json",
        lambda **kwargs: openai_response,
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_mistral_json",
        lambda **kwargs: mistral_response,
    )

    result = run_editorial_style_judge(_preprocessed_content(), _rules())

    assert result["status"] == "warn"
    assert result["score"] == 80
    assert result["agreement"] is False
    assert result["score_gap"] == 20


def test_run_editorial_style_judge_returns_fail_when_one_provider_fails(
    monkeypatch: Any,
) -> None:
    """It should return fail when one provider fails."""
    openai_response = """
    {
      "criteria_scores": {
        "style_alignment": 90,
        "reasoning_alignment": 90,
        "concept_handling": 90,
        "expression_control": 90,
        "writing_conventions": 90,
        "example_alignment": 90
      },
      "findings": [],
      "summary": "Article aligné."
    }
    """

    mistral_response = """
    {
      "criteria_scores": {
        "style_alignment": 40,
        "reasoning_alignment": 40,
        "concept_handling": 40,
        "expression_control": 40,
        "writing_conventions": 40,
        "example_alignment": 40
      },
      "findings": [],
      "summary": "Alignement faible."
    }
    """

    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_openai_json",
        lambda **kwargs: openai_response,
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_mistral_json",
        lambda **kwargs: mistral_response,
    )

    result = run_editorial_style_judge(_preprocessed_content(), _rules())

    assert result["status"] == "fail"
    assert result["score"] == 65
    assert result["agreement"] is False
    assert result["score_gap"] == 50


def test_run_editorial_style_judge_merges_findings(
    monkeypatch: Any,
) -> None:
    """It should merge provider findings with provider names."""
    response = """
    {
      "criteria_scores": {
        "style_alignment": 90,
        "reasoning_alignment": 90,
        "concept_handling": 90,
        "expression_control": 90,
        "writing_conventions": 90,
        "example_alignment": 90
      },
      "findings": [
        {
          "rule_id": "editorial_style.expression_control",
          "severity": "major",
          "message": "Expression trop emphatique.",
          "evidence": "Une révolution incroyable."
        }
      ],
      "summary": "Alignement global correct."
    }
    """

    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_openai_json",
        lambda **kwargs: response,
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_mistral_json",
        lambda **kwargs: response,
    )

    result = run_editorial_style_judge(_preprocessed_content(), _rules())

    assert result["status"] == "warn"
    assert len(result["findings"]) == 2
    assert result["findings"][0]["provider"] == "openai"
    assert result["findings"][1]["provider"] == "mistral"


def test_run_editorial_style_judge_handles_invalid_json(
    monkeypatch: Any,
) -> None:
    """It should return fail when providers return invalid JSON."""
    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_openai_json",
        lambda **kwargs: "not valid json",
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_mistral_json",
        lambda **kwargs: "not valid json",
    )

    result = run_editorial_style_judge(_preprocessed_content(), _rules())

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["agreement"] is True
    assert result["findings"][0]["rule_id"] == "editorial_style.invalid_json"


def test_run_editorial_style_judge_handles_provider_failure(
    monkeypatch: Any,
) -> None:
    """It should return fail when providers raise exceptions."""

    def raise_error(**kwargs: object) -> str:
        raise RuntimeError("Provider unavailable")

    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_openai_json",
        raise_error,
    )
    monkeypatch.setattr(
        "contentcreajudge.judges.editorial_style.editorial_style_judge.call_mistral_json",
        raise_error,
    )

    result = run_editorial_style_judge(_preprocessed_content(), _rules())

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["agreement"] is True
    assert result["findings"][0]["rule_id"] == "editorial_style.openai.provider_error"
    assert result["findings"][1]["rule_id"] == "editorial_style.mistral.provider_error"

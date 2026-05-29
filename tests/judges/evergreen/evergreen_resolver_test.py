from typing import NoReturn

import pytest

from contentcreajudge.rules.judges.evergreen.evergreen_resolver import (
    resolve_evergreen_rules,
)


def test_resolve_evergreen_rules_falls_back_when_config_loading_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ensure default config is used when YAML loading fails."""

    def raise_config_error(_file: object) -> NoReturn:
        raise RuntimeError("invalid config")

    monkeypatch.setattr(
        "contentcreajudge.rules.judges.evergreen.evergreen_resolver.yaml.safe_load",
        raise_config_error,
    )

    resolved = resolve_evergreen_rules({"evergreen": True})

    assert resolved["judge_id"] == "evergreen"
    assert resolved["version"] == 2
    assert resolved["label"] == "Evergreen judge"
    assert resolved["mode"] == "llm"
    assert resolved["is_blocking_rule"] is False
    assert resolved["evergreen_required"] is True
    assert resolved["llm"] == {
        "provider": "openai",
        "model_env_var": "OPENAI_EVERGREEN_MODEL",
        "default_model": "gpt-4.1-mini",
        "temperature": 0.0,
        "max_tokens": 2000,
    }
    assert resolved["scoring"]["pass_min_score"] == 70
    assert resolved["scoring"]["warn_min_score"] == 50
    assert resolved["weights"]["dependance_temporelle"] == 0.25
    assert resolved["prompt_template"] == ""
    assert resolved["llm_messages"]["llm_error"] == (
        "The evergreen evaluation could not be completed reliably."
    )
    assert resolved["activation"] == {}
    assert resolved["rules"] == []


def test_resolve_evergreen_rules_with_evergreen_true() -> None:
    """Resolve evergreen config when evergreen mode is required."""
    context = {
        "evergreen": True,
        "locale": "fr-FR",
        "allowed_dates": ["2024"],
        "allowed_temporal_references": ["depuis 2024"],
        "brief": "Le brief autorise un contexte historique.",
    }

    resolved = resolve_evergreen_rules(context)

    assert resolved["judge_id"] == "evergreen"
    assert resolved["evergreen_required"] is True
    assert resolved["locale"] == "fr-FR"
    assert resolved["allowed_dates"] == ["2024"]
    assert resolved["allowed_temporal_references"] == ["depuis 2024"]
    assert resolved["mode"] == "llm"
    assert resolved["is_blocking_rule"] is False
    assert resolved["llm"]["provider"] == "openai"
    assert resolved["llm"]["model_env_var"] == "OPENAI_EVERGREEN_MODEL"
    assert resolved["scoring"]["pass_min_score"] == 70
    assert resolved["weights"]["stabilite_informations"] == 0.30
    assert "prompt_template" in resolved
    assert "llm_messages" in resolved
    assert "temporal_expression_categories" in resolved
    assert "context_detection" in resolved


def test_resolve_evergreen_rules_with_evergreen_false() -> None:
    """Resolve evergreen config when evergreen mode is disabled."""
    context = {
        "evergreen": False,
        "locale": "en-US",
    }

    resolved = resolve_evergreen_rules(context)

    assert resolved["judge_id"] == "evergreen"
    assert resolved["evergreen_required"] is False
    assert resolved["locale"] == "en-US"
    assert resolved["allowed_dates"] == []
    assert resolved["allowed_temporal_references"] == []
    assert resolved["llm"]["default_model"] == "gpt-4.1-mini"
    assert resolved["scoring"]["warn_min_score"] == 50


def test_resolver_with_empty_context() -> None:
    """Resolve evergreen config with default context values."""
    resolved = resolve_evergreen_rules({})

    assert resolved["evergreen_required"] is False
    assert resolved["locale"] == "fr-FR"
    assert resolved["mode"] == "llm"

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
    assert resolved["version"] == 1
    assert resolved["label"] == "Evergreen judge"
    assert resolved["evergreen_required"] is True
    assert resolved["activation"] == {}
    assert resolved["rules"] == []
    assert resolved["messages"] == {}


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
    assert "temporal_expression_categories" in resolved
    assert "context_detection" in resolved
    assert "messages" in resolved


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


def test_resolver_with_empty_context() -> None:
    """Resolve evergreen config with default context values."""
    resolved = resolve_evergreen_rules({})

    assert resolved["evergreen_required"] is False
    assert resolved["locale"] == "fr-FR"

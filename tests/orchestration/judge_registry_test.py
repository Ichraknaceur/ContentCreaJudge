from __future__ import annotations

from contentcreajudge.application.orchestration.judge_registry import (
    DEFAULT_ENABLED_JUDGES,
    get_runnable_judges,
)


def test_get_runnable_judges_returns_length() -> None:
    runnable_judges = get_runnable_judges(["length"])

    assert list(runnable_judges.keys()) == ["length"]


def test_get_runnable_judges_ignores_unknown_judge() -> None:
    runnable_judges = get_runnable_judges(["unknown"])

    assert runnable_judges == {}


def test_get_runnable_judges_uses_default_when_input_is_invalid() -> None:
    runnable_judges = get_runnable_judges("length")

    assert list(runnable_judges.keys()) == DEFAULT_ENABLED_JUDGES

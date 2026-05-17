from contentcreajudge.application.judge_flow.typography_flow import (
    execute_typography_flow,
)


def test_execute_typography_flow_pass() -> None:
    """The flow should return a passing result for clean content."""
    payload = {
        "content": "<p>Bonjour\u00a0! Texte propre.</p>",
        "profile": "default",
        "context": {
            "locale": "fr-FR",
        },
        "request_id": "req-001",
    }

    result = execute_typography_flow(payload)

    assert "request_echo" in result
    assert "rule_resolution" in result
    assert "preprocessing" in result
    assert "judge_result" in result
    assert "aggregation" in result

    assert result["request_echo"]["request_id"] == "req-001"
    assert result["judge_result"]["dimension"] == "typography"
    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"


def test_execute_typography_flow_warn() -> None:
    """The flow should return a warning result for content with minor issues."""
    payload = {
        "content": "<p>Bonjour  le monde .</p>",
        "profile": "default",
        "context": {
            "locale": "fr-FR",
        },
    }

    result = execute_typography_flow(payload)

    assert result["judge_result"]["dimension"] == "typography"
    assert result["judge_result"]["status"] == "warn"
    assert result["aggregation"]["status"] == "warn"


def test_execute_typography_flow_fail() -> None:
    """The flow should return a failing result for content with major issues."""
    payload = {
        "content": "<p>Bonjour!</p>",
        "profile": "default",
        "context": {
            "locale": "fr-FR",
        },
    }

    result = execute_typography_flow(payload)

    assert result["judge_result"]["dimension"] == "typography"
    assert result["judge_result"]["status"] == "fail"
    assert result["aggregation"]["status"] == "fail"


def test_execute_typography_flow_keeps_profile_and_context() -> None:
    """The flow should echo the profile and context in the response."""
    payload = {
        "content": "<p>Bonjour\u00a0! Texte propre.</p>",
        "profile": "editorial",
        "context": {
            "locale": "fr-FR",
        },
    }

    result = execute_typography_flow(payload)

    assert result["request_echo"]["profile"] == "editorial"
    assert result["request_echo"]["context"]["locale"] == "fr-FR"
    assert result["rule_resolution"]["profile"] == "editorial"

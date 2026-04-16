from contentcreajudge.application.judge_flow.typography_flow import (
    execute_typography_flow,
)


def test_execute_typography_flow_pass() -> None:
    payload = {
        "content": "<p>Bonjour\u00A0! Texte propre.</p>",
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
    payload = {
        "content": "<p>Bonjour\u00A0! Texte propre.</p>",
        "profile": "editorial",
        "context": {
            "locale": "fr-FR",
        },
    }

    result = execute_typography_flow(payload)

    assert result["request_echo"]["profile"] == "editorial"
    assert result["request_echo"]["context"]["locale"] == "fr-FR"
    assert result["rule_resolution"]["profile"] == "editorial"
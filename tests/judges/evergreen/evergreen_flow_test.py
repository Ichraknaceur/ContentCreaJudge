from contentcreajudge.application.judge_flow.evergreen_flow import (
    execute_evergreen_flow,
)


def test_execute_evergreen_flow_with_evergreen_true_and_unprovided_year() -> None:
    payload = {
        "content": "En 2024, les pratiques éditoriales évoluent.",
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


def test_execute_evergreen_flow_with_evergreen_false_returns_warning() -> None:
    payload = {
        "content": "En 2024, les pratiques éditoriales évoluent.",
        "profile": "default",
        "context": {
            "evergreen": False,
            "locale": "fr-FR",
        },
    }

    result = execute_evergreen_flow(payload)

    assert result["judge_result"]["status"] == "warn"
    assert result["judge_result"]["score"] == 90
    assert result["aggregation"]["status"] == "warn"


def test_execute_evergreen_flow_allows_input_date() -> None:
    payload = {
        "content": "Le cadre éditorial a été défini en 2024.",
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


def test_execute_evergreen_flow_allows_source_context() -> None:
    payload = {
        "content": "Selon une étude de 2024, les usages éditoriaux évoluent.",
        "profile": "default",
        "context": {
            "evergreen": True,
            "locale": "fr-FR",
        },
    }

    result = execute_evergreen_flow(payload)

    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"


def test_execute_evergreen_flow_with_missing_context_does_not_crash() -> None:
    payload = {
        "content": "En 2024, le sujet évolue.",
        "profile": "default",
    }

    result = execute_evergreen_flow(payload)

    assert result["request_echo"]["context"] == {}
    assert result["judge_result"]["dimension"] == "evergreen"
    assert "aggregation" in result


def test_execute_evergreen_flow_with_invalid_context_type_does_not_crash() -> None:
    payload = {
        "content": "En 2024, le sujet évolue.",
        "profile": "default",
        "context": "invalid-context",
    }

    result = execute_evergreen_flow(payload)

    assert result["request_echo"]["context"] == {}
    assert result["judge_result"]["dimension"] == "evergreen"
    assert "aggregation" in result


def test_execute_evergreen_flow_with_empty_payload_does_not_crash() -> None:
    result = execute_evergreen_flow({})

    assert result["request_echo"]["content"] == ""
    assert result["request_echo"]["profile"] == "default"
    assert result["request_echo"]["request_id"] is None
    assert result["preprocessing"]["is_empty"] is True
    assert result["judge_result"]["status"] == "pass"
    assert result["aggregation"]["status"] == "pass"

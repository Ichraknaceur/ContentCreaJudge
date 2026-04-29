from contentcreajudge.judges.evergreen.evergreen_judge import run_evergreen_judge
from contentcreajudge.preprocessing.evergreen_preprocessor import (
    EvergreenPreprocessingResult,
)


def _rules(evergreen_required: bool = True) -> dict[str, object]:
    return {
        "evergreen_required": evergreen_required,
        "messages": {
            "unprovided_dates": (
                "The content contains dates that were not provided in the inputs."
            ),
            "relative_temporal_references": (
                "The content contains relative temporal expressions."
            ),
            "news_references": "The content contains news-related references.",
            "version_references": "The content contains version references.",
            "current_trend_references": "The content contains current-trend wording.",
        },
    }


def _preprocessed(
    *,
    value: str = "2024",
    reference_type: str = "year",
    is_in_source_context: bool = False,
    is_historical_context: bool = False,
    is_in_input: bool = False,
) -> EvergreenPreprocessingResult:
    return {
        "original_content": "",
        "normalized_text": "",
        "locale_key": "fr",
        "temporal_references": [
            {
                "value": value,
                "type": reference_type,
                "start": 0,
                "end": len(value),
                "context": value,
                "is_in_source_context": is_in_source_context,
                "is_historical_context": is_historical_context,
                "is_in_input": is_in_input,
            },
        ],
        "temporal_references_count": 1,
        "is_empty": False,
    }


def test_evergreen_true_fails_on_unprovided_year() -> None:
    result = run_evergreen_judge(_preprocessed(), _rules(True))

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["findings"][0]["rule_id"] == "evergreen.unprovided_dates"
    assert result["findings"][0]["severity"] == "major"


def test_evergreen_false_warns_on_temporal_reference() -> None:
    result = run_evergreen_judge(_preprocessed(), _rules(False))

    assert result["status"] == "warn"
    assert result["score"] == 90
    assert result["findings"][0]["severity"] == "minor"


def test_source_context_is_allowed() -> None:
    result = run_evergreen_judge(
        _preprocessed(is_in_source_context=True),
        _rules(True),
    )

    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["findings"] == []


def test_historical_context_is_allowed() -> None:
    result = run_evergreen_judge(
        _preprocessed(is_historical_context=True),
        _rules(True),
    )

    assert result["status"] == "pass"
    assert result["findings"] == []


def test_input_date_is_allowed() -> None:
    result = run_evergreen_judge(
        _preprocessed(is_in_input=True),
        _rules(True),
    )

    assert result["status"] == "pass"
    assert result["findings"] == []


def test_relative_reference_gets_relative_rule_id() -> None:
    result = run_evergreen_judge(
        _preprocessed(value="actuellement", reference_type="relative_date"),
        _rules(True),
    )

    assert result["status"] == "fail"
    assert result["findings"][0]["rule_id"] == (
        "evergreen.relative_temporal_references"
    )


def test_news_reference_gets_news_rule_and_message() -> None:
    result = run_evergreen_judge(
        _preprocessed(value="news", reference_type="news_reference"),
        _rules(True),
    )

    assert result["findings"][0]["rule_id"] == "evergreen.news_references"
    assert result["findings"][0]["message"] == (
        "The content contains news-related references."
    )
    assert result["findings"][0]["severity"] == "major"


def test_version_reference_gets_version_rule_and_message() -> None:
    result = run_evergreen_judge(
        _preprocessed(value="latest version", reference_type="version_reference"),
        _rules(True),
    )

    assert result["findings"][0]["rule_id"] == "evergreen.version_references"
    assert result["findings"][0]["message"] == (
        "The content contains version references."
    )
    assert result["findings"][0]["severity"] == "major"


def test_current_trend_reference_gets_fallback_rule_and_minor_severity() -> None:
    result = run_evergreen_judge(
        _preprocessed(value="current trend", reference_type="current_trend_reference"),
        _rules(True),
    )

    assert result["findings"][0]["rule_id"] == "evergreen.current_trend_references"
    assert result["findings"][0]["message"] == (
        "The content contains current-trend wording."
    )
    assert result["findings"][0]["severity"] == "minor"


def test_message_falls_back_when_messages_config_is_not_dict() -> None:
    rules = _rules(True)
    rules["messages"] = []

    result = run_evergreen_judge(_preprocessed(), rules)

    assert result["findings"][0]["message"] == (
        "The content contains a temporal reference."
    )


def test_message_falls_back_when_configured_message_is_not_string() -> None:
    rules = _rules(True)
    messages = rules["messages"]
    assert isinstance(messages, dict)
    messages["unprovided_dates"] = None

    result = run_evergreen_judge(_preprocessed(), rules)

    assert result["findings"][0]["message"] == (
        "The content contains a temporal reference."
    )

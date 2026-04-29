from contentcreajudge.preprocessing.evergreen_preprocessor import (
    _get_locale_key,
    _get_nested_str_list,
    preprocess_evergreen_content,
)


def _rules() -> dict[str, object]:
    return {
        "locale": "fr-FR",
        "allowed_dates": ["2023"],
        "allowed_temporal_references": [],
        "temporal_expression_categories": {
            "relative_dates": {
                "fr": ["aujourd'hui", "récemment", "actuellement"],
                "en": ["today", "recently", "currently"],
            },
            "news_references": {
                "fr": ["actualité", "tendance actuelle"],
                "en": ["news", "current trend"],
            },
            "version_references": {
                "fr": ["dernière version", "version actuelle"],
                "en": ["latest version", "current version"],
            },
        },
        "context_detection": {
            "source_context_markers": {
                "fr": ["selon", "étude", "rapport", "baromètre"],
                "en": ["according to", "study", "report"],
            },
            "historical_context_markers": {
                "fr": ["depuis", "historiquement", "dans les années"],
                "en": ["since", "historically"],
            },
        },
    }


def test_preprocess_detects_year() -> None:
    result = preprocess_evergreen_content(
        "En 2024, les pratiques éditoriales évoluent.",
        _rules(),
    )

    assert result["temporal_references_count"] >= 1
    assert any(ref["value"] == "2024" for ref in result["temporal_references"])


def test_preprocess_marks_source_context() -> None:
    result = preprocess_evergreen_content(
        "Selon une étude de 2024, les usages évoluent.",
        _rules(),
    )

    assert any(
        ref["value"] == "2024" and ref["is_in_source_context"] is True
        for ref in result["temporal_references"]
    )


def test_preprocess_marks_historical_context() -> None:
    result = preprocess_evergreen_content(
        "Depuis 2010, le marketing de contenu s’est structuré.",
        _rules(),
    )

    assert any(
        ref["value"] == "2010" and ref["is_historical_context"] is True
        for ref in result["temporal_references"]
    )


def test_preprocess_marks_input_allowed_date() -> None:
    result = preprocess_evergreen_content(
        "Le cadre éditorial a été défini en 2023.",
        _rules(),
    )

    assert any(
        ref["value"] == "2023" and ref["is_in_input"] is True
        for ref in result["temporal_references"]
    )


def test_preprocess_detects_relative_expression() -> None:
    result = preprocess_evergreen_content(
        "Actuellement, les contenus doivent rester différenciants.",
        _rules(),
    )

    assert any(ref["type"] == "relative_date" for ref in result["temporal_references"])


def test_preprocess_handles_none_content_without_crashing() -> None:
    result = preprocess_evergreen_content(None, _rules())

    assert result["normalized_text"] == ""
    assert result["temporal_references_count"] == 0
    assert result["is_empty"] is True


def test_preprocess_handles_missing_rules_without_crashing() -> None:
    result = preprocess_evergreen_content(
        "En 2024, le sujet évolue.",
        None,
    )

    assert result["temporal_references_count"] >= 1


def test_get_locale_key_defaults_to_french_without_locale() -> None:
    assert _get_locale_key(None) == "fr"


def test_get_locale_key_detects_english_locale() -> None:
    assert _get_locale_key("en-US") == "en"


def test_get_nested_str_list_returns_empty_when_parent_is_not_dict() -> None:
    assert _get_nested_str_list({"relative_dates": []}, "relative_dates", "fr") == []


def test_preprocess_detects_full_date() -> None:
    result = preprocess_evergreen_content(
        "Le rapport a ete publie le 12/03/2024.",
        _rules(),
    )

    assert any(
        ref["value"] == "12/03/2024" and ref["type"] == "full_date"
        for ref in result["temporal_references"]
    )


def test_preprocess_detects_month_year() -> None:
    result = preprocess_evergreen_content(
        "La mise a jour date de mars 2024.",
        _rules(),
    )

    assert any(
        ref["value"] == "mars 2024" and ref["type"] == "month_year"
        for ref in result["temporal_references"]
    )


def test_preprocess_uses_english_month_year_patterns() -> None:
    rules = _rules()
    rules["locale"] = "en-US"

    result = preprocess_evergreen_content(
        "The report was updated in March 2024.",
        rules,
    )

    assert result["locale_key"] == "en"
    assert any(
        ref["value"] == "March 2024" and ref["type"] == "month_year"
        for ref in result["temporal_references"]
    )


def test_preprocess_ignores_empty_configured_expression() -> None:
    rules = _rules()
    temporal_categories = rules["temporal_expression_categories"]
    assert isinstance(temporal_categories, dict)
    relative_dates = temporal_categories["relative_dates"]
    assert isinstance(relative_dates, dict)
    relative_dates["fr"] = ["   ", "actuellement"]

    result = preprocess_evergreen_content(
        "Actuellement, les contenus restent utiles.",
        rules,
    )

    assert [
        ref["value"]
        for ref in result["temporal_references"]
        if ref["type"] == "relative_date"
    ] == ["Actuellement"]


def test_preprocess_marks_year_inside_anchor_text_as_source_context() -> None:
    result = preprocess_evergreen_content(
        content=(
            "<p>Lecture complémentaire</p>"
            "<ul>"
            '<li><a href="https://liris.cnrs.fr/evenement/journee-theses-2026">'
            "Journée des thèses 2026 - pour les D2"
            "</a></li>"
            "</ul>"
        ),
        judge_rules=_rules(),
    )

    assert any(
        ref["value"] == "2026" and ref["is_in_source_context"] is True
        for ref in result["temporal_references"]
    )

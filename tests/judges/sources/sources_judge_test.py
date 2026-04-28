from __future__ import annotations

from contentcreajudge.judges.sources.sources_judge import run_sources_judge


JUDGE_RULES = {
    "require_sources": True,
    "expected_length": "MEDIUM",
    "content_type": "articles",
    "is_content_type_allowed": True,
    "is_content_type_allowed_with_caution": False,
    "is_content_type_forbidden": False,
    "reference_limits": {
        "min_external_references_per_h2": 1,
        "max_external_references_per_h2": 2,
    },
    "html_link_format": {
        "required_attributes": {
            "target": "_blank",
            "rel": "noopener noreferrer",
        },
        "forbidden_anchor_texts": [
            "cliquez ici",
            "lire plus",
            "click here",
            "read more",
        ],
    },
    "messages": {
        "real_and_accessible_sources": (
            "External sources must be real, accessible, and directly related to the claim."
        ),
        "external_reference_count_by_length": (
            "The number of external references must be consistent with the expected content length."
        ),
        "content_type_policy": (
            "External links are not allowed for this content type unless officially required."
        ),
        "network_accessibility": (
            "Source URLs must be checked through a network accessibility validation."
        ),
        "html_anchor_format": (
            "External sources must use the required HTML anchor format."
        ),
        "no_raw_or_markdown_url": "Raw URLs and Markdown links are forbidden.",
        "no_tracking_parameters": "URLs must not contain tracking parameters.",
        "descriptive_anchor_text": "Link anchor text must be descriptive.",
        "no_duplicate_links": "Each external source must appear only once.",
    },
}


def _base_preprocessed_content() -> dict[str, object]:
    return {
        "external_links": [
            {
                "href": "https://example.com/report",
                "anchor_text": "Example Report",
                "target": "_blank",
                "rel": "noopener noreferrer",
                "is_external": True,
            }
        ],
        "external_links_count": 1,
        "raw_urls": [],
        "raw_urls_count": 0,
        "markdown_links": [],
        "markdown_links_count": 0,
        "attached_anchor_count": 0,
        "has_raw_urls": False,
        "has_markdown_links": False,
        "has_attached_anchors": False,
    }


def _base_validation_results() -> list[dict[str, object]]:
    return [
        {
            "url": "https://example.com/report",
            "is_valid_format": True,
            "has_tracking_parameters": False,
            "tracking_parameters": [],
            "network_status": "reachable",
            "http_status_code": 200,
            "error": None,
        }
    ]


def test_sources_judge_passes_with_valid_source() -> None:
    result = run_sources_judge(
        preprocessed_content=_base_preprocessed_content(),
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["dimension"] == "sources"
    assert result["status"] == "pass"
    assert result["score"] == 100
    assert result["findings"][0]["rule_id"] == "sources.valid"


def test_sources_judge_fails_when_required_source_is_missing() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["external_links"] = []
    preprocessed["external_links_count"] = 0

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=[],
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "fail"
    assert result["score"] == 0
    assert result["findings"][0]["rule_id"] == "sources.real_and_accessible_sources"


def test_sources_judge_fails_on_raw_url() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["has_raw_urls"] = True
    preprocessed["raw_urls"] = ["https://example.com/report"]
    preprocessed["raw_urls_count"] = 1

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "sources.no_raw_or_markdown_url"
        for finding in result["findings"]
    )


def test_sources_judge_fails_on_markdown_link() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["has_markdown_links"] = True
    preprocessed["markdown_links"] = ["[Source](https://example.com/report)"]
    preprocessed["markdown_links_count"] = 1

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "sources.no_raw_or_markdown_url"
        for finding in result["findings"]
    )


def test_sources_judge_warn_on_invalid_external_link_attributes() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["external_links"][0]["target"] = ""
    preprocessed["external_links"][0]["rel"] = ""

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "warn"
    assert any(
        finding["rule_id"] == "sources.html_anchor_format"
        for finding in result["findings"]
    )


def test_sources_judge_warns_on_attached_anchor() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["has_attached_anchors"] = True
    preprocessed["attached_anchor_count"] = 1

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "warn"
    assert result["score"] == 80
    assert any(
        finding["rule_id"] == "sources.html_anchor_format"
        and finding["severity"] == "minor"
        and finding["evidence"]["attached_anchor_count"] == 1
        for finding in result["findings"]
    )


def test_sources_judge_warns_on_empty_anchor_text() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["external_links"][0]["anchor_text"] = "   "

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "warn"
    assert result["score"] == 80
    assert any(
        finding["rule_id"] == "sources.descriptive_anchor_text"
        and finding["severity"] == "minor"
        and finding["evidence"]["reason"] == "empty_anchor_text"
        for finding in result["findings"]
    )


def test_sources_judge_warns_on_generic_anchor_text() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["external_links"][0]["anchor_text"] = "cliquez ici"

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "warn"
    assert result["score"] == 80
    assert any(
        finding["rule_id"] == "sources.descriptive_anchor_text"
        for finding in result["findings"]
    )


def test_sources_judge_warns_on_duplicate_external_links() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["external_links"].append(
        {
            "href": "https://example.com/report",
            "anchor_text": "Example Report duplicate",
            "target": "_blank",
            "rel": "noopener noreferrer",
            "is_external": True,
        }
    )
    preprocessed["external_links_count"] = 2

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=_base_validation_results(),
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "warn"
    assert any(
        finding["rule_id"] == "sources.no_duplicate_links"
        for finding in result["findings"]
    )


def test_sources_judge_fails_on_tracking_parameters() -> None:
    validation_results = _base_validation_results()
    validation_results[0]["has_tracking_parameters"] = True
    validation_results[0]["tracking_parameters"] = ["utm_source"]

    result = run_sources_judge(
        preprocessed_content=_base_preprocessed_content(),
        validation_results=validation_results,
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "sources.no_tracking_parameters"
        for finding in result["findings"]
    )


def test_sources_judge_fails_on_invalid_url_format() -> None:
    validation_results = _base_validation_results()
    validation_results[0]["is_valid_format"] = False
    validation_results[0]["error"] = "invalid_url_format"

    result = run_sources_judge(
        preprocessed_content=_base_preprocessed_content(),
        validation_results=validation_results,
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "sources.real_and_accessible_sources"
        and finding["severity"] == "major"
        and finding["evidence"]["error"] == "invalid_url_format"
        for finding in result["findings"]
    )


def test_sources_judge_fails_on_unreachable_url() -> None:
    validation_results = _base_validation_results()
    validation_results[0]["network_status"] = "unreachable"
    validation_results[0]["http_status_code"] = 404
    validation_results[0]["error"] = "http_status_404"

    result = run_sources_judge(
        preprocessed_content=_base_preprocessed_content(),
        validation_results=validation_results,
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "sources.network_accessibility"
        for finding in result["findings"]
    )


def test_sources_judge_warns_on_unknown_network_status() -> None:
    validation_results = _base_validation_results()
    validation_results[0]["network_status"] = "unknown"
    validation_results[0]["error"] = "timeout"

    result = run_sources_judge(
        preprocessed_content=_base_preprocessed_content(),
        validation_results=validation_results,
        judge_rules=JUDGE_RULES,
    )

    assert result["status"] == "warn"
    assert result["score"] == 80
    assert any(
        finding["rule_id"] == "sources.network_accessibility"
        for finding in result["findings"]
    )


def test_sources_judge_fails_when_simple_content_has_too_many_external_sources() -> None:
    preprocessed = _base_preprocessed_content()
    preprocessed["external_links"].append(
        {
            "href": "https://example.com/second-report",
            "anchor_text": "Second Report",
            "target": "_blank",
            "rel": "noopener noreferrer",
            "is_external": True,
        }
    )
    preprocessed["external_links_count"] = 2

    judge_rules = {
        **JUDGE_RULES,
        "expected_length": "SIMPLE",
        "reference_limits": {
            "max_external_references_total": 1,
        },
    }

    validation_results = _base_validation_results()
    validation_results.append(
        {
            "url": "https://example.com/second-report",
            "is_valid_format": True,
            "has_tracking_parameters": False,
            "tracking_parameters": [],
            "network_status": "reachable",
            "http_status_code": 200,
            "error": None,
        }
    )

    result = run_sources_judge(
        preprocessed_content=preprocessed,
        validation_results=validation_results,
        judge_rules=judge_rules,
    )

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "sources.external_reference_count_by_length"
        for finding in result["findings"]
    )


def test_sources_judge_fails_when_external_links_are_forbidden_for_content_type() -> None:
    judge_rules = {
        **JUDGE_RULES,
        "content_type": "quiz",
        "is_content_type_allowed": False,
        "is_content_type_allowed_with_caution": False,
        "is_content_type_forbidden": True,
    }

    result = run_sources_judge(
        preprocessed_content=_base_preprocessed_content(),
        validation_results=_base_validation_results(),
        judge_rules=judge_rules,
    )

    assert result["status"] == "fail"
    assert any(
        finding["rule_id"] == "sources.content_type_policy"
        for finding in result["findings"]
    )


def test_sources_judge_warns_when_external_links_are_allowed_with_caution() -> None:
    judge_rules = {
        **JUDGE_RULES,
        "content_type": "audioScript",
        "is_content_type_allowed": False,
        "is_content_type_allowed_with_caution": True,
        "is_content_type_forbidden": False,
    }

    result = run_sources_judge(
        preprocessed_content=_base_preprocessed_content(),
        validation_results=_base_validation_results(),
        judge_rules=judge_rules,
    )

    assert result["status"] == "warn"
    assert result["score"] == 80
    assert any(
        finding["rule_id"] == "sources.content_type_policy"
        for finding in result["findings"]
    )
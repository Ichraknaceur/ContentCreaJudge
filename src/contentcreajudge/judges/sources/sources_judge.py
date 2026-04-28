"""Judge logic for source compliance evaluation."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _make_finding(
    rule_id: str,
    severity: str,
    message: str,
    evidence: dict[str, object],
) -> dict[str, object]:
    """Create a normalized finding."""
    return {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }


def _normalize_text(value: str) -> str:
    """Normalize text for simple comparisons."""
    return value.strip().lower()


def _has_required_rel(actual_rel: str, expected_rel: str) -> bool:
    """Check that all expected rel tokens are present."""
    actual_tokens = set(actual_rel.split())
    expected_tokens = set(expected_rel.split())
    return expected_tokens.issubset(actual_tokens)


def run_sources_judge(
    preprocessed_content: dict[str, object],
    validation_results: list[dict[str, object]],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate source compliance using preprocessing and URL validation results."""

    findings: list[dict[str, object]] = []

    messages = judge_rules["messages"]
    html_rules = judge_rules["html_link_format"]
    required_attributes = html_rules["required_attributes"]
    forbidden_anchor_texts = {
        _normalize_text(text)
        for text in html_rules["forbidden_anchor_texts"]
    }

    require_sources = bool(judge_rules["require_sources"])
    external_links = preprocessed_content["external_links"]
    external_links_count = int(preprocessed_content["external_links_count"])

    # Source policy based on content type
    content_type = str(judge_rules.get("content_type", ""))
    is_content_type_allowed_with_caution = bool(
        judge_rules.get("is_content_type_allowed_with_caution", False)
    )
    is_content_type_forbidden = bool(
        judge_rules.get("is_content_type_forbidden", False)
    )

    if is_content_type_forbidden and external_links_count > 0:
        findings.append(
            _make_finding(
                rule_id="sources.content_type_policy",
                severity="major",
                message=str(messages["content_type_policy"]),
                evidence={
                    "content_type": content_type,
                    "external_links_count": external_links_count,
                    "reason": "external_links_forbidden_for_content_type",
                },
            )
        )

    elif is_content_type_allowed_with_caution and external_links_count > 0:
        findings.append(
            _make_finding(
                rule_id="sources.content_type_policy",
                severity="minor",
                message=str(messages["content_type_policy"]),
                evidence={
                    "content_type": content_type,
                    "external_links_count": external_links_count,
                    "reason": "external_links_allowed_with_caution",
                },
            )
        )

    # Required sources are missing
    if require_sources and external_links_count == 0:
        findings.append(
            _make_finding(
                rule_id="sources.real_and_accessible_sources",
                severity="major",
                message=str(messages["real_and_accessible_sources"]),
                evidence={
                    "external_links_count": external_links_count,
                    "require_sources": require_sources,
                },
            )
        )
    
    # External reference limits based on expected content length
    expected_length = str(judge_rules["expected_length"])
    reference_limits = judge_rules.get("reference_limits", {})

    if isinstance(reference_limits, dict):
        max_total = reference_limits.get("max_external_references_total")

        if max_total is not None and external_links_count > int(max_total):
            findings.append(
                _make_finding(
                    rule_id="sources.external_reference_count_by_length",
                    severity="major",
                    message=str(
                        messages["external_reference_count_by_length"]
                    ),
                    evidence={
                        "expected_length": expected_length,
                        "external_links_count": external_links_count,
                        "max_external_references_total": max_total,
                    },
                )
            )

        min_per_h2 = reference_limits.get("min_external_references_per_h2")

        if (
            require_sources
            and min_per_h2 is not None
            and external_links_count == 0
        ):
            findings.append(
                _make_finding(
                    rule_id="sources.external_reference_count_by_length",
                    severity="minor",
                    message=str(
                        messages["external_reference_count_by_length"]
                    ),
                    evidence={
                        "expected_length": expected_length,
                        "external_links_count": external_links_count,
                        "min_external_references_per_h2": min_per_h2,
                        "note": (
                            "V1 checks global absence only. "
                            "Per-H2 reference distribution will be added later."
                        ),
                    },
                )
            )

    # Raw URLs are forbidden
    if bool(preprocessed_content["has_raw_urls"]):
        findings.append(
            _make_finding(
                rule_id="sources.no_raw_or_markdown_url",
                severity="major",
                message=str(messages["no_raw_or_markdown_url"]),
                evidence={
                    "raw_urls": preprocessed_content["raw_urls"],
                    "raw_urls_count": preprocessed_content["raw_urls_count"],
                },
            )
        )

    # Markdown links are forbidden
    if bool(preprocessed_content["has_markdown_links"]):
        findings.append(
            _make_finding(
                rule_id="sources.no_raw_or_markdown_url",
                severity="major",
                message=str(messages["no_raw_or_markdown_url"]),
                evidence={
                    "markdown_links": preprocessed_content["markdown_links"],
                    "markdown_links_count": preprocessed_content[
                        "markdown_links_count"
                    ],
                },
            )
        )

    # <a> tags attached to the previous word
    if bool(preprocessed_content["has_attached_anchors"]):
        findings.append(
            _make_finding(
                rule_id="sources.html_anchor_format",
                severity="minor",
                message=str(messages["html_anchor_format"]),
                evidence={
                    "attached_anchor_count": preprocessed_content[
                        "attached_anchor_count"
                    ],
                },
            )
        )

    # Required HTML attributes for external links
    for link in external_links:
        href = str(link["href"])
        target = str(link["target"])
        rel = str(link["rel"])
        anchor_text = str(link["anchor_text"])

        expected_target = str(required_attributes["target"])
        expected_rel = str(required_attributes["rel"])

        invalid_target = target != expected_target
        invalid_rel = not _has_required_rel(rel, expected_rel)

        if invalid_target or invalid_rel:
            findings.append(
                _make_finding(
                    rule_id="sources.html_anchor_format",
                    severity="minor",
                    message=str(messages["html_anchor_format"]),
                    evidence={
                        "href": href,
                        "target": target,
                        "expected_target": expected_target,
                        "rel": rel,
                        "expected_rel": expected_rel,
                    },
                )
            )

        # Empty or generic anchor text
        normalized_anchor_text = _normalize_text(anchor_text)

        if not normalized_anchor_text:
            findings.append(
                _make_finding(
                    rule_id="sources.descriptive_anchor_text",
                    severity="minor",
                    message=str(messages["descriptive_anchor_text"]),
                    evidence={
                        "href": href,
                        "anchor_text": anchor_text,
                        "reason": "empty_anchor_text",
                    },
                )
            )

        elif normalized_anchor_text in forbidden_anchor_texts:
            findings.append(
                _make_finding(
                    rule_id="sources.descriptive_anchor_text",
                    severity="minor",
                    message=str(messages["descriptive_anchor_text"]),
                    evidence={
                        "href": href,
                        "anchor_text": anchor_text,
                        "reason": "generic_anchor_text",
                    },
                )
            )

    # Duplicate external links
    external_hrefs = [str(link["href"]) for link in external_links]
    duplicated_hrefs = [
        href for href, count in Counter(external_hrefs).items() if count > 1
    ]

    if duplicated_hrefs:
        findings.append(
            _make_finding(
                rule_id="sources.no_duplicate_links",
                severity="minor",
                message=str(messages["no_duplicate_links"]),
                evidence={
                    "duplicated_hrefs": duplicated_hrefs,
                },
            )
        )

    # URL validation results from network checks
    for validation in validation_results:
        url = str(validation["url"])

        if not bool(validation["is_valid_format"]):
            findings.append(
                _make_finding(
                    rule_id="sources.real_and_accessible_sources",
                    severity="major",
                    message=str(messages["real_and_accessible_sources"]),
                    evidence={
                        "url": url,
                        "error": validation["error"],
                    },
                )
            )

        # Presence of tracking parameters
        if bool(validation["has_tracking_parameters"]):
            findings.append(
                _make_finding(
                    rule_id="sources.no_tracking_parameters",
                    severity="major",
                    message=str(messages["no_tracking_parameters"]),
                    evidence={
                        "url": url,
                        "tracking_parameters": validation[
                            "tracking_parameters"
                        ],
                    },
                )
            )

        network_status = str(validation["network_status"])

        if network_status == "unreachable":
            findings.append(
                _make_finding(
                    rule_id="sources.network_accessibility",
                    severity="major",
                    message=str(messages["network_accessibility"]),
                    evidence={
                        "url": url,
                        "http_status_code": validation["http_status_code"],
                        "error": validation["error"],
                    },
                )
            )

        elif network_status == "unknown":
            findings.append(
                _make_finding(
                    rule_id="sources.network_accessibility",
                    severity="minor",
                    message=str(messages["network_accessibility"]),
                    evidence={
                        "url": url,
                        "network_status": network_status,
                        "error": validation["error"],
                    },
                )
            )

    major_findings = [
        finding for finding in findings if finding["severity"] == "major"
    ]
    minor_findings = [
        finding for finding in findings if finding["severity"] == "minor"
    ]

    if major_findings:
        status = "fail"
        score = 0
    elif minor_findings:
        status = "warn"
        score = 80
    else:
        status = "pass"
        score = 100
        findings.append(
            _make_finding(
                rule_id="sources.valid",
                severity="info",
                message="Sources comply with the configured rules.",
                evidence={
                    "external_links_count": external_links_count,
                    "validated_urls_count": len(validation_results),
                },
            )
        )

    return {
        "dimension": "sources",
        "status": status,
        "score": score,
        "applied_rule": judge_rules,
        "findings": findings,
    }

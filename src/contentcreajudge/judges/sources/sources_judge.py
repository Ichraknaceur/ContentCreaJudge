"""Judge logic for source compliance evaluation."""

from __future__ import annotations

from collections import Counter


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
    return set(expected_rel.split()).issubset(set(actual_rel.split()))


def _get_message(
    messages: dict[str, object],
    key: str,
    fallback: str,
) -> str:
    """Return a configured message or a safe fallback."""
    return str(messages.get(key, fallback))


def _as_dict(value: object) -> dict[str, object]:
    """Return a dictionary or an empty fallback."""
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    """Return a list or an empty fallback."""
    return value if isinstance(value, list) else []


def _append_content_type_policy_finding(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    judge_rules: dict[str, object],
    external_links_count: int,
) -> None:
    """Evaluate source permissions for the configured content type."""
    content_type = str(judge_rules.get("content_type", ""))
    is_allowed_with_caution = bool(
        judge_rules.get("is_content_type_allowed_with_caution", False),
    )
    is_forbidden = bool(judge_rules.get("is_content_type_forbidden", False))

    if is_forbidden and external_links_count > 0:
        findings.append(
            _make_finding(
                rule_id="sources.content_type_policy",
                severity="major",
                message=_get_message(
                    messages,
                    "content_type_policy",
                    "External links are not allowed for this content type.",
                ),
                evidence={
                    "content_type": content_type,
                    "external_links_count": external_links_count,
                    "reason": "external_links_forbidden_for_content_type",
                },
            ),
        )
    elif is_allowed_with_caution and external_links_count > 0:
        findings.append(
            _make_finding(
                rule_id="sources.content_type_policy",
                severity="minor",
                message=_get_message(
                    messages,
                    "content_type_policy",
                    "External links are allowed with caution for this content type.",
                ),
                evidence={
                    "content_type": content_type,
                    "external_links_count": external_links_count,
                    "reason": "external_links_allowed_with_caution",
                },
            ),
        )


def _append_complementary_reading_finding(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    preprocessed_content: dict[str, object],
    complementary_reading_rules: dict[str, object],
) -> str:
    """Evaluate complementary reading links and return the required domain."""
    required_domain = str(
        complementary_reading_rules.get("required_domain", ""),
    ).strip()
    external_links = _as_list(
        preprocessed_content.get("complementary_reading_external_links", []),
    )

    if required_domain and external_links:
        findings.append(
            _make_finding(
                rule_id="sources.complementary_reading_policy",
                severity="major",
                message=_get_message(
                    messages,
                    "complementary_reading_policy",
                    (
                        "Complementary reading links must come from the "
                        "organization website."
                    ),
                ),
                evidence={
                    "required_domain": required_domain,
                    "invalid_links": external_links,
                    "reason": (
                        "complementary_reading_contains_links_outside_organization"
                    ),
                },
            ),
        )

    return required_domain


def _append_required_sources_finding(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    judge_rules: dict[str, object],
    body_external_links_count: int,
    complementary_reading_links_count: int,
) -> bool:
    """Evaluate whether at least one source link is present when required."""
    require_sources = bool(judge_rules.get("require_sources", False))
    has_any_source_link = (
        body_external_links_count > 0 or complementary_reading_links_count > 0
    )
    if require_sources and not has_any_source_link:
        findings.append(
            _make_finding(
                rule_id="sources.real_and_accessible_sources",
                severity="major",
                message=_get_message(
                    messages,
                    "real_and_accessible_sources",
                    "External sources must be real and accessible.",
                ),
                evidence={
                    "body_external_links_count": body_external_links_count,
                    "complementary_reading_links_count": (
                        complementary_reading_links_count
                    ),
                    "require_sources": require_sources,
                },
            ),
        )
    return has_any_source_link


def _append_reference_limit_findings(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    judge_rules: dict[str, object],
    external_links_count: int,
    *,
    has_any_source_link: bool,
) -> None:
    """Evaluate total and minimum reference limits."""
    require_sources = bool(judge_rules.get("require_sources", False))
    expected_length = str(judge_rules.get("expected_length", "unknown"))
    reference_limits = judge_rules.get("reference_limits", {})
    if not isinstance(reference_limits, dict):
        return

    message = _get_message(
        messages,
        "external_reference_count_by_length",
        (
            "The number of external references must be consistent with the "
            "expected content length."
        ),
    )
    max_total = reference_limits.get("max_external_references_total")
    if max_total is not None and external_links_count > int(max_total):
        findings.append(
            _make_finding(
                rule_id="sources.external_reference_count_by_length",
                severity="major",
                message=message,
                evidence={
                    "expected_length": expected_length,
                    "external_links_count": external_links_count,
                    "max_external_references_total": max_total,
                },
            ),
        )

    min_per_h2 = reference_limits.get("min_external_references_per_h2")
    if require_sources and min_per_h2 is not None and not has_any_source_link:
        findings.append(
            _make_finding(
                rule_id="sources.external_reference_count_by_length",
                severity="minor",
                message=message,
                evidence={
                    "expected_length": expected_length,
                    "external_links_count": external_links_count,
                    "min_external_references_per_h2": min_per_h2,
                    "note": (
                        "V1 checks global absence only. "
                        "Per-H2 reference distribution will be added later."
                    ),
                },
            ),
        )


def _append_content_format_findings(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    preprocessed_content: dict[str, object],
) -> None:
    """Evaluate raw URLs, Markdown links, and attached anchors."""
    if bool(preprocessed_content.get("has_raw_urls", False)):
        findings.append(
            _make_finding(
                rule_id="sources.no_raw_or_markdown_url",
                severity="major",
                message=_get_message(
                    messages,
                    "no_raw_or_markdown_url",
                    "Raw URLs and Markdown links are forbidden.",
                ),
                evidence={
                    "raw_urls": preprocessed_content.get("raw_urls", []),
                    "raw_urls_count": preprocessed_content.get("raw_urls_count", 0),
                },
            ),
        )

    if bool(preprocessed_content.get("has_markdown_links", False)):
        findings.append(
            _make_finding(
                rule_id="sources.no_raw_or_markdown_url",
                severity="major",
                message=_get_message(
                    messages,
                    "no_raw_or_markdown_url",
                    "Raw URLs and Markdown links are forbidden.",
                ),
                evidence={
                    "markdown_links": preprocessed_content.get("markdown_links", []),
                    "markdown_links_count": preprocessed_content.get(
                        "markdown_links_count",
                        0,
                    ),
                },
            ),
        )

    if bool(preprocessed_content.get("has_attached_anchors", False)):
        findings.append(
            _make_finding(
                rule_id="sources.html_anchor_format",
                severity="minor",
                message=_get_message(
                    messages,
                    "html_anchor_format",
                    "External sources must use the required HTML anchor format.",
                ),
                evidence={
                    "attached_anchor_count": preprocessed_content.get(
                        "attached_anchor_count",
                        0,
                    ),
                },
            ),
        )


def _append_external_link_findings(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    external_links: list[object],
    required_attributes: dict[str, object],
    forbidden_anchor_texts: set[str],
) -> None:
    """Evaluate external link attributes and descriptive anchor text."""
    expected_target = str(required_attributes.get("target", ""))
    expected_rel = str(required_attributes.get("rel", ""))

    for link in external_links:
        if not isinstance(link, dict):
            continue

        href = str(link.get("href", ""))
        target = str(link.get("target", ""))
        rel = str(link.get("rel", ""))
        anchor_text = str(link.get("anchor_text", ""))
        invalid_target = bool(expected_target) and target != expected_target
        invalid_rel = bool(expected_rel) and not _has_required_rel(rel, expected_rel)

        if invalid_target or invalid_rel:
            findings.append(
                _make_finding(
                    rule_id="sources.html_anchor_format",
                    severity="minor",
                    message=_get_message(
                        messages,
                        "html_anchor_format",
                        "External sources must use the required HTML anchor format.",
                    ),
                    evidence={
                        "href": href,
                        "target": target,
                        "expected_target": expected_target,
                        "rel": rel,
                        "expected_rel": expected_rel,
                    },
                ),
            )

        normalized_anchor_text = _normalize_text(anchor_text)
        if not normalized_anchor_text:
            reason = "empty_anchor_text"
        elif normalized_anchor_text in forbidden_anchor_texts:
            reason = "generic_anchor_text"
        else:
            continue

        findings.append(
            _make_finding(
                rule_id="sources.descriptive_anchor_text",
                severity="minor",
                message=_get_message(
                    messages,
                    "descriptive_anchor_text",
                    "Link anchor text must be descriptive.",
                ),
                evidence={
                    "href": href,
                    "anchor_text": anchor_text,
                    "reason": reason,
                },
            ),
        )


def _append_duplicate_link_finding(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    external_links: list[object],
) -> None:
    """Evaluate duplicated external hrefs."""
    external_hrefs = [
        str(link.get("href", ""))
        for link in external_links
        if isinstance(link, dict) and str(link.get("href", "")).strip()
    ]
    duplicated_hrefs = [
        href for href, count in Counter(external_hrefs).items() if count > 1
    ]
    if duplicated_hrefs:
        findings.append(
            _make_finding(
                rule_id="sources.no_duplicate_links",
                severity="minor",
                message=_get_message(
                    messages,
                    "no_duplicate_links",
                    "Each external source must appear only once.",
                ),
                evidence={"duplicated_hrefs": duplicated_hrefs},
            ),
        )


def _append_validation_findings(
    findings: list[dict[str, object]],
    messages: dict[str, object],
    validation_results: list[dict[str, object]],
) -> None:
    """Evaluate URL validation and network accessibility results."""
    for validation in validation_results:
        if not isinstance(validation, dict):
            continue

        url = str(validation.get("url", ""))
        if not bool(validation.get("is_valid_format", False)):
            findings.append(
                _make_finding(
                    rule_id="sources.real_and_accessible_sources",
                    severity="major",
                    message=_get_message(
                        messages,
                        "real_and_accessible_sources",
                        "External sources must be real and accessible.",
                    ),
                    evidence={"url": url, "error": validation.get("error")},
                ),
            )

        if bool(validation.get("has_tracking_parameters", False)):
            findings.append(
                _make_finding(
                    rule_id="sources.no_tracking_parameters",
                    severity="major",
                    message=_get_message(
                        messages,
                        "no_tracking_parameters",
                        "URLs must not contain tracking parameters.",
                    ),
                    evidence={
                        "url": url,
                        "tracking_parameters": validation.get(
                            "tracking_parameters",
                            [],
                        ),
                    },
                ),
            )

        network_status = str(validation.get("network_status", "unknown"))
        if network_status == "unreachable":
            severity = "major"
            fallback = "Source URLs must be accessible."
            evidence = {
                "url": url,
                "http_status_code": validation.get("http_status_code"),
                "error": validation.get("error"),
            }
        elif network_status == "unknown":
            severity = "minor"
            fallback = "Source URL accessibility could not be confirmed."
            evidence = {
                "url": url,
                "network_status": network_status,
                "error": validation.get("error"),
            }
        else:
            continue

        findings.append(
            _make_finding(
                rule_id="sources.network_accessibility",
                severity=severity,
                message=_get_message(messages, "network_accessibility", fallback),
                evidence=evidence,
            ),
        )


def _build_judge_summary(
    findings: list[dict[str, object]],
    judge_rules: dict[str, object],
    external_links_count: int,
    validation_results: list[dict[str, object]],
    required_domain: str,
) -> dict[str, object]:
    """Build the final sources judge payload."""
    major_findings = [
        finding for finding in findings if finding.get("severity") == "major"
    ]
    minor_findings = [
        finding for finding in findings if finding.get("severity") == "minor"
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
                    "organization_website": required_domain,
                },
            ),
        )

    return {
        "dimension": "sources",
        "status": status,
        "score": score,
        "applied_rule": judge_rules,
        "findings": findings,
    }


def run_sources_judge(
    preprocessed_content: dict[str, object],
    validation_results: list[dict[str, object]],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate source compliance using preprocessing and URL validation results."""
    findings: list[dict[str, object]] = []
    messages = _as_dict(judge_rules.get("messages", {}))
    html_rules = _as_dict(judge_rules.get("html_link_format", {}))
    required_attributes = _as_dict(html_rules.get("required_attributes", {}))
    forbidden_anchor_texts = {
        _normalize_text(str(text))
        for text in html_rules.get("forbidden_anchor_texts", [])
    }
    external_links = _as_list(preprocessed_content.get("external_links", []))
    external_links_count = int(preprocessed_content.get("external_links_count", 0))
    _append_content_type_policy_finding(
        findings,
        messages,
        judge_rules,
        external_links_count,
    )
    required_domain = _append_complementary_reading_finding(
        findings,
        messages,
        preprocessed_content,
        _as_dict(judge_rules.get("complementary_reading", {})),
    )
    body_external_links_count = int(
        preprocessed_content.get("body_external_links_count", 0),
    )
    complementary_reading_links_count = int(
        preprocessed_content.get("complementary_reading_links_count", 0),
    )
    has_any_source_link = _append_required_sources_finding(
        findings,
        messages,
        judge_rules,
        body_external_links_count,
        complementary_reading_links_count,
    )

    _append_reference_limit_findings(
        findings,
        messages,
        judge_rules,
        external_links_count,
        has_any_source_link=has_any_source_link,
    )
    _append_content_format_findings(findings, messages, preprocessed_content)
    _append_external_link_findings(
        findings,
        messages,
        external_links,
        required_attributes,
        forbidden_anchor_texts,
    )
    _append_duplicate_link_finding(findings, messages, external_links)
    _append_validation_findings(findings, messages, validation_results)

    return _build_judge_summary(
        findings,
        judge_rules,
        external_links_count,
        validation_results,
        required_domain,
    )

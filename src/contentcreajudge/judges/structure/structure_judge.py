"""Judge logic for HTML structure evaluation."""

from __future__ import annotations

from typing import Any


def _get_rule_config(
    rules: list[dict[str, Any]],
    rule_id: str,
) -> dict[str, Any] | None:
    """Return the matching rule configuration for a given rule_id."""
    for rule in rules:
        if rule.get("rule_id") == rule_id:
            return rule
    return None


def _build_finding(
    *,
    rule_id: str,
    severity: str,
    message: str,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """Build a normalized finding payload."""
    return {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
        "evidence": evidence,
    }

def _strip_optional_trailing_heading(
    headings: list[dict[str, Any]],
    structure_rules: dict[str, Any],
) -> list[dict[str, Any]]:
    """Remove one allowed optional trailing heading if configured."""
    optional_config = structure_rules.get("optional_trailing_sections", {})

    if not optional_config.get("allow_enabled", False):
        return headings

    if not headings:
        return headings

    allowed_titles = {
        str(title).strip().lower()
        for title in optional_config.get("allowed_titles", [])
    }

    last_heading = headings[-1]
    last_text = str(last_heading.get("text", "")).strip().lower()

    if last_text in allowed_titles:
        return headings[:-1]

    return headings

def run_structure_judge(
    preprocessed_content: dict[str, Any],
    judge_rules: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate generated HTML structure against the expected outline and constraints."""
    expected = preprocessed_content["expected"]
    generated = preprocessed_content["generated"]

    expected_headings = expected["headings"]
    generated_headings = generated["headings"]

    rules = judge_rules["rules"]
    messages = judge_rules["messages"]
    structure_rules = judge_rules["structure_rules"]

    comparison_expected_headings = expected_headings
    comparison_generated_headings = _strip_optional_trailing_heading(
        generated_headings,
        structure_rules,
    )

    findings: list[dict[str, Any]] = []

    expected_heading_texts = [item["text"] for item in comparison_expected_headings]
    generated_heading_texts = [item["text"] for item in comparison_generated_headings]

    expected_heading_levels = [item["level"] for item in comparison_expected_headings]
    generated_heading_levels = [item["level"] for item in comparison_generated_headings]

    allowed_heading_tags = set(
        structure_rules["allowed_html_tags"]["headings"]
    )
    allowed_body_tags = set(
        structure_rules["allowed_html_tags"]["body"]
    )
    allowed_tags = allowed_heading_tags | allowed_body_tags

    used_tags = set(generated["used_tags"])
    unauthorized_tags = sorted(tag for tag in used_tags if tag not in allowed_tags)

    # Heading order
    if structure_rules["post_generation_checks"]["verify_heading_order"]:
        if expected_heading_texts != generated_heading_texts:
            rule = _get_rule_config(rules, "structure.heading_order")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.heading_order",
                        severity=rule["severity"],
                        message=messages["heading_order_mismatch"],
                        evidence={
                            "expected_heading_texts": expected_heading_texts,
                            "generated_heading_texts": generated_heading_texts,
                        },
                    )
                )

    # Heading levels
    if structure_rules["post_generation_checks"]["verify_heading_levels"]:
        if expected_heading_levels != generated_heading_levels:
            rule = _get_rule_config(rules, "structure.heading_levels")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.heading_levels",
                        severity=rule["severity"],
                        message=messages["heading_level_mismatch"],
                        evidence={
                            "expected_heading_levels": expected_heading_levels,
                            "generated_heading_levels": generated_heading_levels,
                        },
                    )
                )

    # Heading text
    if structure_rules["keep_same_heading_text"]:
        if sorted(expected_heading_texts) != sorted(generated_heading_texts):
            rule = _get_rule_config(rules, "structure.heading_text")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.heading_text",
                        severity=rule["severity"],
                        message=messages["heading_text_mismatch"],
                        evidence={
                            "expected_heading_texts": expected_heading_texts,
                            "generated_heading_texts": generated_heading_texts,
                        },
                    )
                )

    # Added sections
    if structure_rules["forbid"]["add_sections"]:
        if len(comparison_generated_headings) > len(comparison_expected_headings):
            rule = _get_rule_config(rules, "structure.no_added_sections")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.no_added_sections",
                        severity=rule["severity"],
                        message=messages["added_sections_detected"],
                        evidence={
                            "expected_heading_count": len(expected_headings),
                            "generated_heading_count": len(generated_headings),
                            "expected_heading_count_for_comparison": len(
                                comparison_expected_headings
                            ),
                            "generated_heading_count_for_comparison": len(
                                comparison_generated_headings
                            ),
                        },
                    )
                )

    # Removed sections
    if structure_rules["forbid"]["remove_sections"]:
        if len(comparison_generated_headings) < len(comparison_expected_headings):
            rule = _get_rule_config(rules, "structure.no_removed_sections")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.no_removed_sections",
                        severity=rule["severity"],
                        message=messages["removed_sections_detected"],
                        evidence={
                            "expected_heading_count": len(expected_headings),
                            "generated_heading_count": len(generated_headings),
                            "expected_heading_count_for_comparison": len(
                                comparison_expected_headings
                            ),
                            "generated_heading_count_for_comparison": len(
                                comparison_generated_headings
                            ),
                        },
                    )
                )

    # H1 forbidden
    if structure_rules["forbid"]["use_h1_in_body"]:
        if generated["has_h1"]:
            rule = _get_rule_config(rules, "structure.no_h1_in_body")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.no_h1_in_body",
                        severity=rule["severity"],
                        message=messages["h1_in_body_detected"],
                        evidence={"has_h1": True},
                    )
                )

    # Internal outline comments exposed
    if structure_rules["forbid"]["expose_internal_comments_from_outline"]:
        if generated["has_internal_outline_comments_exposed"]:
            rule = _get_rule_config(
                rules,
                "structure.no_internal_outline_comments_exposed",
            )
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.no_internal_outline_comments_exposed",
                        severity=rule["severity"],
                        message=messages["internal_outline_comment_exposed"],
                        evidence={
                            "detected_patterns": generated[
                                "detected_internal_comment_patterns"
                            ]
                        },
                    )
                )

    # Unauthorized HTML tags
    if structure_rules["forbid"]["use_unauthorized_html_tags"]:
        if unauthorized_tags:
            rule = _get_rule_config(rules, "structure.allowed_tags_only")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.allowed_tags_only",
                        severity=rule["severity"],
                        message=messages["unauthorized_tags_detected"],
                        evidence={
                            "unauthorized_tags": unauthorized_tags,
                            "used_tags": sorted(used_tags),
                            "allowed_tags": sorted(allowed_tags),
                        },
                    )
                )

    # Script tags forbidden
    if structure_rules["html_constraints"]["forbid_scripts"]:
        if generated["has_script"]:
            rule = _get_rule_config(rules, "structure.no_scripts")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.no_scripts",
                        severity=rule["severity"],
                        message=messages["script_tag_detected"],
                        evidence={"has_script": True},
                    )
                )

    # Decorative span forbidden
    if structure_rules["html_constraints"]["forbid_decorative_spans"]:
        if generated["has_span"]:
            rule = _get_rule_config(rules, "structure.no_decorative_spans")
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.no_decorative_spans",
                        severity=rule["severity"],
                        message=messages["decorative_span_detected"],
                        evidence={"has_span": True},
                    )
                )

    # Inline styles forbidden outside tables
    if structure_rules["html_constraints"]["forbid_inline_styles_except_tables"]:
        if generated["has_inline_style_outside_tables"]:
            rule = _get_rule_config(
                rules,
                "structure.no_inline_styles_except_tables",
            )
            if rule and rule.get("enabled", False):
                findings.append(
                    _build_finding(
                        rule_id="structure.no_inline_styles_except_tables",
                        severity=rule["severity"],
                        message=messages["inline_style_detected"],
                        evidence={"has_inline_style_outside_tables": True},
                    )
                )

    if findings:
        return {
            "dimension": "structure",
            "status": "fail",
            "score": 0,
            "applied_rule": judge_rules,
            "findings": findings,
        }

    return {
        "dimension": "structure",
        "status": "pass",
        "score": 100,
        "applied_rule": judge_rules,
        "findings": [
            _build_finding(
                rule_id="structure.valid",
                severity="info",
                message=messages["pass"],
                evidence={
                    "expected_heading_count": len(expected_headings),
                    "generated_heading_count": len(generated_headings),
                    "used_tags": sorted(used_tags),
                },
            )
        ],
    }
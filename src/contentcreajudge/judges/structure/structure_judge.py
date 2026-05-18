"""Judge logic for HTML structure evaluation."""

from __future__ import annotations

from typing import Any, NamedTuple


class _StructureCheck(NamedTuple):
    """Configuration for one structure rule check."""

    condition: bool
    rule_id: str
    message_key: str
    evidence: dict[str, Any]


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


def _enabled_finding(
    check: _StructureCheck,
    rules: list[dict[str, Any]],
    messages: dict[str, str],
) -> dict[str, Any] | None:
    """Build a finding when a check is triggered and its rule is enabled."""
    if not check.condition:
        return None

    rule = _get_rule_config(rules, check.rule_id)
    if not rule or not rule.get("enabled", False):
        return None

    return _build_finding(
        rule_id=check.rule_id,
        severity=rule["severity"],
        message=messages.get(check.message_key, check.message_key),
        evidence=check.evidence,
    )


def _collect_findings(
    checks: list[_StructureCheck],
    rules: list[dict[str, Any]],
    messages: dict[str, str],
) -> list[dict[str, Any]]:
    """Return findings for all triggered and enabled checks."""
    return [
        finding
        for check in checks
        if (finding := _enabled_finding(check, rules, messages)) is not None
    ]


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


def _heading_count_evidence(
    expected_headings: list[dict[str, Any]],
    generated_headings: list[dict[str, Any]],
    comparison_expected_headings: list[dict[str, Any]],
    comparison_generated_headings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return counts used by added and removed section findings."""
    return {
        "expected_heading_count": len(expected_headings),
        "generated_heading_count": len(generated_headings),
        "expected_heading_count_for_comparison": len(comparison_expected_headings),
        "generated_heading_count_for_comparison": len(comparison_generated_headings),
    }


def run_structure_judge(
    preprocessed_content: dict[str, Any],
    judge_rules: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate generated HTML structure against expected outline constraints."""
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

    expected_heading_texts = [item["text"] for item in comparison_expected_headings]
    generated_heading_texts = [item["text"] for item in comparison_generated_headings]

    expected_heading_levels = [item["level"] for item in comparison_expected_headings]
    generated_heading_levels = [item["level"] for item in comparison_generated_headings]

    allowed_heading_tags = set(
        structure_rules["allowed_html_tags"]["headings"],
    )
    allowed_body_tags = set(
        structure_rules["allowed_html_tags"]["body"],
    )
    allowed_tags = allowed_heading_tags | allowed_body_tags

    used_tags = set(generated["used_tags"])
    unauthorized_tags = sorted(tag for tag in used_tags if tag not in allowed_tags)
    heading_count_evidence = _heading_count_evidence(
        expected_headings,
        generated_headings,
        comparison_expected_headings,
        comparison_generated_headings,
    )
    post_generation_checks = structure_rules["post_generation_checks"]
    forbidden_rules = structure_rules["forbid"]
    html_constraints = structure_rules["html_constraints"]

    findings = _collect_findings(
        [
            _StructureCheck(
                post_generation_checks["verify_heading_order"]
                and expected_heading_texts != generated_heading_texts,
                "structure.heading_order",
                "heading_order_mismatch",
                {
                    "expected_heading_texts": expected_heading_texts,
                    "generated_heading_texts": generated_heading_texts,
                },
            ),
            _StructureCheck(
                post_generation_checks["verify_heading_levels"]
                and expected_heading_levels != generated_heading_levels,
                "structure.heading_levels",
                "heading_level_mismatch",
                {
                    "expected_heading_levels": expected_heading_levels,
                    "generated_heading_levels": generated_heading_levels,
                },
            ),
            _StructureCheck(
                structure_rules["keep_same_heading_text"]
                and sorted(expected_heading_texts) != sorted(generated_heading_texts),
                "structure.heading_text",
                "heading_text_mismatch",
                {
                    "expected_heading_texts": expected_heading_texts,
                    "generated_heading_texts": generated_heading_texts,
                },
            ),
            _StructureCheck(
                forbidden_rules["add_sections"]
                and len(comparison_generated_headings)
                > len(comparison_expected_headings),
                "structure.no_added_sections",
                "added_sections_detected",
                heading_count_evidence,
            ),
            _StructureCheck(
                forbidden_rules["remove_sections"]
                and len(comparison_generated_headings)
                < len(comparison_expected_headings),
                "structure.no_removed_sections",
                "removed_sections_detected",
                heading_count_evidence,
            ),
            _StructureCheck(
                forbidden_rules["use_h1_in_body"] and generated["has_h1"],
                "structure.no_h1_in_body",
                "h1_in_body_detected",
                {"has_h1": True},
            ),
            _StructureCheck(
                forbidden_rules["expose_internal_comments_from_outline"]
                and generated["has_internal_outline_comments_exposed"],
                "structure.no_internal_outline_comments_exposed",
                "internal_outline_comment_exposed",
                {
                    "detected_patterns": generated[
                        "detected_internal_comment_patterns"
                    ],
                },
            ),
            _StructureCheck(
                forbidden_rules["use_unauthorized_html_tags"]
                and bool(unauthorized_tags),
                "structure.allowed_tags_only",
                "unauthorized_tags_detected",
                {
                    "unauthorized_tags": unauthorized_tags,
                    "used_tags": sorted(used_tags),
                    "allowed_tags": sorted(allowed_tags),
                },
            ),
            _StructureCheck(
                html_constraints["forbid_scripts"] and generated["has_script"],
                "structure.no_scripts",
                "script_tag_detected",
                {"has_script": True},
            ),
            _StructureCheck(
                html_constraints["forbid_decorative_spans"] and generated["has_span"],
                "structure.no_decorative_spans",
                "decorative_span_detected",
                {"has_span": True},
            ),
            _StructureCheck(
                html_constraints["forbid_inline_styles_except_tables"]
                and generated["has_inline_style_outside_tables"],
                "structure.no_inline_styles_except_tables",
                "inline_style_detected",
                {"has_inline_style_outside_tables": True},
            ),
        ],
        rules,
        messages,
    )

    applied_rule = {
        "judge_id": judge_rules.get("judge_id"),
        "expected_outline_html": judge_rules.get("expected_outline_html"),
        "locale": judge_rules.get("locale"),
    }

    if findings:
        return {
            "dimension": "structure",
            "status": "fail",
            "score": 0,
            "applied_rule": applied_rule,
            "findings": findings,
        }

    return {
        "dimension": "structure",
        "status": "pass",
        "score": 100,
        "applied_rule": applied_rule,
        "findings": [
            _build_finding(
                rule_id="structure.valid",
                severity="info",
                message=messages.get(
                    "pass", "The HTML structure matches the expected outline."
                ),
                evidence={
                    "expected_heading_count": len(expected_headings),
                    "generated_heading_count": len(generated_headings),
                    "used_tags": sorted(used_tags),
                },
            ),
        ],
    }

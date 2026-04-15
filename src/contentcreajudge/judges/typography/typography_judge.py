"""Judge logic for typography evaluation."""

from __future__ import annotations

import re


def find_double_spaces(decoded_text: str) -> list[str]:
    """Find multiple consecutive spaces in decoded text."""
    return re.findall(r" {2,}", decoded_text)


def find_trailing_spaces(lines: list[str]) -> list[str]:
    """Find lines ending with trailing spaces or tabs."""
    return [line for line in lines if re.search(r"[ \t]+$", line)]


def find_multiple_punctuation(decoded_text: str) -> list[str]:
    """Find excessive punctuation such as !!, ??? or mixed repeated punctuation."""
    return re.findall(r"[!?.,;:]{2,}", decoded_text)


def find_space_before_dot(decoded_text: str) -> list[str]:
    """Find spaces before periods."""
    return re.findall(r"\s+\.", decoded_text)


def find_space_before_comma(decoded_text: str) -> list[str]:
    """Find spaces before commas."""
    return re.findall(r"\s+,", decoded_text)


def find_french_nbsp_issues(decoded_text: str) -> list[str]:
    """Find missing non-breaking spaces before French double punctuation marks."""
    return re.findall(r"(?<!\u00A0)[:;!?%]", decoded_text)


def find_attached_links(original_content: str) -> list[str]:
    """Find anchor tags directly attached to the previous word."""
    return re.findall(r"[^\s(]<a\b", original_content, flags=re.IGNORECASE)


def find_repeated_line_breaks(original_content: str) -> list[str]:
    """Find repeated HTML line breaks such as <br><br>."""
    return re.findall(
        r"(<br\s*/?>\s*){2,}",
        original_content,
        flags=re.IGNORECASE,
    )

def run_typography_judge(
    preprocessed_content: dict[str, object],
    judge_rules: dict[str, object],
) -> dict[str, object]:
    """Evaluate the content against typography rules."""

    decoded_text = str(preprocessed_content["decoded_text"])
    original_content = str(preprocessed_content["original_content"])
    original_lines = list(preprocessed_content["original_lines"])

    messages = judge_rules["messages"]
    configured_rules = judge_rules["rules"]

    severity_by_rule_id = {
        rule["rule_id"]: rule["severity"]
        for rule in configured_rules
        if rule.get("enabled", False)
    }

    findings: list[dict[str, object]] = []

    def add_finding(
        rule_id: str,
        message_key: str,
        evidence: dict[str, object],
    ) -> None:
        findings.append(
            {
                "rule_id": rule_id,
                "severity": severity_by_rule_id[rule_id],
                "message": messages[message_key],
                "evidence": evidence,
            }
        )

    double_spaces_matches = find_double_spaces(decoded_text)
    if double_spaces_matches:
        add_finding(
            rule_id="typography.double_spaces",
            message_key="double_spaces",
            evidence={"matches_count": len(double_spaces_matches)},
        )

    trailing_spaces_matches = find_trailing_spaces(original_lines)
    if trailing_spaces_matches:
        add_finding(
            rule_id="typography.trailing_spaces",
            message_key="trailing_spaces",
            evidence={"lines_count": len(trailing_spaces_matches)},
        )

    space_before_dot_matches = find_space_before_dot(decoded_text)
    if space_before_dot_matches:
        add_finding(
            rule_id="typography.space_before_dot",
            message_key="space_before_dot",
            evidence={"matches_count": len(space_before_dot_matches)},
        )

    space_before_comma_matches = find_space_before_comma(decoded_text)
    if space_before_comma_matches:
        add_finding(
            rule_id="typography.space_before_comma",
            message_key="space_before_comma",
            evidence={"matches_count": len(space_before_comma_matches)},
        )

    french_nbsp_matches = find_french_nbsp_issues(decoded_text)
    if french_nbsp_matches:
        add_finding(
            rule_id="typography.french_nbsp_before_double_punctuation",
            message_key="french_nbsp_before_double_punctuation",
            evidence={"matches_count": len(french_nbsp_matches)},
        )

    multiple_punctuation_matches = find_multiple_punctuation(decoded_text)
    if multiple_punctuation_matches:
        add_finding(
            rule_id="typography.multiple_punctuation",
            message_key="multiple_punctuation",
            evidence={"matches_count": len(multiple_punctuation_matches)},
        )

    attached_links_matches = find_attached_links(original_content)
    if attached_links_matches:
        add_finding(
            rule_id="typography.attached_links",
            message_key="attached_links",
            evidence={"matches_count": len(attached_links_matches)},
        )

    repeated_breaks_matches = find_repeated_line_breaks(original_content)
    if repeated_breaks_matches:
        add_finding(
            rule_id="typography.repeated_line_breaks",
            message_key="repeated_line_breaks",
            evidence={"matches_count": len(repeated_breaks_matches)},
        )

    if not findings:
        return {
            "dimension": "typography",
            "status": "pass",
            "score": 100,
            "applied_rule": judge_rules,
            "findings": [
                {
                    "rule_id": "typography.valid",
                    "severity": "info",
                    "message": "Typography rules passed successfully.",
                    "evidence": {"matches_count": 0},
                }
            ],
        }

    major_count = sum(1 for finding in findings if finding["severity"] == "major")
    minor_count = sum(1 for finding in findings if finding["severity"] == "minor")

    score = max(0, 100 - (major_count * 25) - (minor_count * 10))

    if major_count > 0:
        status = "fail"
    else:
        status = "warn"

    return {
        "dimension": "typography",
        "status": status,
        "score": score,
        "applied_rule": judge_rules,
        "findings": findings,
    }
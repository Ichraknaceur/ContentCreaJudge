from __future__ import annotations

from typing import TYPE_CHECKING, Any

import streamlit as st

if TYPE_CHECKING:
    from collections.abc import Callable


_HTTP_SUCCESS_MIN = 200
_HTTP_SUCCESS_MAX = 300


def read_uploaded_text_file(uploaded_file: Any) -> str:  # noqa: ANN401
    """Read an uploaded text-based file and return its UTF-8 content."""
    if uploaded_file is None:
        return ""

    file_bytes = uploaded_file.getvalue()
    if not file_bytes:
        return ""

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("utf-8", errors="replace")


def extract_api_error_message(response_body: object) -> str | None:
    """Return a user-facing API error message when the backend provides one."""
    if not isinstance(response_body, dict):
        return None

    error_payload = response_body.get("error")
    if not isinstance(error_payload, dict):
        return None

    message = error_payload.get("message")
    if not isinstance(message, str) or not message.strip():
        return None

    return message


def render_status_banner(
    response_status: object,
    error: object,
    api_error_message: str | None,
    success_message: str,
) -> None:
    """Render the top-level status banner for a judge exchange."""
    if error:
        st.error(api_error_message or str(error))
    elif (
        response_status
        and _HTTP_SUCCESS_MIN <= int(response_status) < _HTTP_SUCCESS_MAX
    ):
        st.success(success_message)
    else:
        st.error(api_error_message or f"Request failed with status {response_status}.")


def render_rule_resolution_section(rule_resolution: dict[str, object]) -> None:
    """Render the rule resolution pipeline step."""
    st.markdown(
        f"**Rule resolution** - profile: `{rule_resolution.get('profile', 'unknown')}`",
    )

    judge_rules = rule_resolution.get("judge_rules")
    if judge_rules:
        with st.expander("Show resolved rules"):
            st.json(judge_rules)


def render_findings_section(findings: object) -> None:
    """Render judge findings when present."""
    if not isinstance(findings, list) or not findings:
        return

    st.markdown("**Findings**")

    for finding in findings:
        if not isinstance(finding, dict):
            continue

        severity = str(finding.get("severity", "unknown"))
        finding_message = str(finding.get("message", "No message"))
        rule_id = str(finding.get("rule_id", "unknown"))

        st.markdown(f"- `{severity}` - {finding_message} (`{rule_id}`)")

        evidence = finding.get("evidence")
        if isinstance(evidence, dict) and evidence:
            st.caption(", ".join(f"{key}: {value}" for key, value in evidence.items()))


def render_exchange_summary(
    exchange: dict[str, object],
    *,
    success_message: str,
    render_preprocessing: Callable[[dict[str, object]], None],
    render_judge_result: Callable[[dict[str, object]], None],
) -> None:
    """Render a generic judge API exchange with judge-specific sections."""
    response_status = exchange.get("response_status")
    response_body = exchange.get("response_body") or {}
    error = exchange.get("error")
    api_error_message = extract_api_error_message(response_body)

    render_status_banner(
        response_status,
        error,
        api_error_message,
        success_message,
    )

    if not isinstance(response_body, dict):
        st.warning("Response body is not a JSON object.")
        with st.expander("Show raw API exchange"):
            st.json(exchange)
        return

    rule_resolution = response_body.get("rule_resolution")
    preprocessing = response_body.get("preprocessing")
    judge_result = response_body.get("judge_result")
    response_message = response_body.get("message")

    if response_message:
        st.caption(str(response_message))

    st.markdown("#### Pipeline steps")

    if isinstance(rule_resolution, dict):
        render_rule_resolution_section(rule_resolution)

    if isinstance(preprocessing, dict):
        render_preprocessing(preprocessing)

    if isinstance(judge_result, dict):
        render_judge_result(judge_result)

    with st.expander("Show raw API exchange"):
        st.json(exchange)

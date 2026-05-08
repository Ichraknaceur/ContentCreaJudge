from __future__ import annotations

from typing import TYPE_CHECKING, Any

import requests
import streamlit as st

if TYPE_CHECKING:
    from contentcreajudge.ui.viewmodels.judge_playground_vm import JudgeWorkbenchItem


def read_uploaded_text_file(uploaded_file: Any) -> str:  # noqa: ANN401
    """Read an uploaded text-based file and return its UTF-8 content."""
    if uploaded_file is None:
        return ""

    file_bytes = uploaded_file.read()
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


_HTTP_SUCCESS_MIN = 200
_HTTP_SUCCESS_MAX = 300


def render_status_banner(
    response_status: object,
    error: object,
    api_error_message: str | None,
    success_message: str = "Typography judge executed successfully.",
) -> None:
    """Render the top-level status banner for the exchange."""
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


def render_preprocessing_section(preprocessing: dict[str, object]) -> None:
    """Render the preprocessing pipeline step."""
    st.markdown("**Preprocessing**")
    pre_left, pre_right = st.columns(2)
    with pre_left:
        st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))
        st.metric("BR tag count", str(preprocessing.get("br_tag_count", "n/a")))
    with pre_right:
        st.metric("Anchor tag count", str(preprocessing.get("anchor_tag_count", "n/a")))
        st.metric("Decoded lines", len(preprocessing.get("decoded_lines", [])))
    with st.expander("Show preprocessing text signals"):
        st.json(
            {
                "text_without_html": preprocessing.get("text_without_html", ""),
                "decoded_text": preprocessing.get("decoded_text", ""),
                "normalized_text": preprocessing.get("normalized_text", ""),
                "decoded_text_no_newlines": preprocessing.get(
                    "decoded_text_no_newlines",
                    "",
                ),
            },
        )


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


def render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render the judge result pipeline step."""
    st.markdown("**Judge result**")
    judge_left, judge_right = st.columns(2)
    with judge_left:
        st.metric("Judge status", str(judge_result.get("status", "unknown")))
    with judge_right:
        st.metric("Judge score", str(judge_result.get("score", "n/a")))

    applied_rule = judge_result.get("applied_rule")
    if applied_rule:
        with st.expander("Show applied rule"):
            st.json(applied_rule)

    render_findings_section(judge_result.get("findings", []))


def render_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the API response in a readable way."""
    response_status = exchange.get("response_status")
    response_body = exchange.get("response_body") or {}
    error = exchange.get("error")
    api_error_message = extract_api_error_message(response_body)

    render_status_banner(response_status, error, api_error_message)

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
        render_preprocessing_section(preprocessing)

    if isinstance(judge_result, dict):
        render_judge_result_section(judge_result)

    with st.expander("Show raw API exchange"):
        st.json(exchange)


def render_typography_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the typography judge form."""
    st.markdown("### Typography test input")

    if "typography_content_input" not in st.session_state:
        st.session_state["typography_content_input"] = ""

    with st.form("typography_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="typography_content_file_uploader",
        )

        content_value = st.session_state["typography_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Typography Judge")

    st.session_state["typography_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "locale": locale.strip() or None,
        },
    }

    st.session_state["typography_payload"] = payload
    st.session_state["typography_run_requested"] = True


def render_typography_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the API response."""
    st.markdown(
        '<div class="section-label">Typography result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("typography_payload")

    if not payload:
        st.info("Fill the form and run the Typography judge to see the response here.")
        return

    should_run = st.session_state.get("typography_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_typography_exchange")
        if last_exchange:
            render_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    context = payload.get("context", {})
    locale = context.get("locale", "") if isinstance(context, dict) else ""

    if not str(content).strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["typography_run_requested"] = False
        return

    if not str(locale).strip():
        st.warning("Please provide the locale.")
        st.session_state["typography_run_requested"] = False
        return

    endpoint = f"{api_url.rstrip('/')}{selected_item.endpoint}"

    try:
        response = requests.post(endpoint, json=payload, timeout=30)
    except requests.RequestException as exc:
        exchange = {
            "request_payload": payload,
            "response_status": None,
            "response_body": None,
            "error": f"API request failed: {exc}",
        }
        st.session_state["last_typography_exchange"] = exchange
        render_exchange_summary(exchange)
        st.session_state["typography_run_requested"] = False
        return

    try:
        response_data = response.json()
    except ValueError:
        exchange = {
            "request_payload": payload,
            "response_status": response.status_code,
            "response_body": response.text,
            "error": "The API returned a non-JSON response.",
        }
        st.session_state["last_typography_exchange"] = exchange
        render_exchange_summary(exchange)
        st.session_state["typography_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Typography judge request failed.",
    }
    st.session_state["last_typography_exchange"] = exchange
    render_exchange_summary(exchange)

    st.session_state["typography_run_requested"] = False

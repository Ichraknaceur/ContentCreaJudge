from typing import TYPE_CHECKING

import requests
import streamlit as st

from contentcreajudge.ui.components.judges.shared import (
    read_uploaded_text_file,
    render_exchange_summary,
    render_findings_section,
)

if TYPE_CHECKING:
    from contentcreajudge.ui.viewmodels.judge_playground_vm import JudgeWorkbenchItem


def _render_preprocessing_section(preprocessing: dict[str, object]) -> None:
    """Render the structure preprocessing pipeline step."""
    st.markdown("**Preprocessing**")

    expected = preprocessing.get("expected", {})
    generated = preprocessing.get("generated", {})

    expected = expected if isinstance(expected, dict) else {}
    generated = generated if isinstance(generated, dict) else {}

    pre_left, pre_right = st.columns(2)

    with pre_left:
        st.metric(
            "Expected headings",
            str(expected.get("heading_count", "n/a")),
        )
        st.metric(
            "Generated headings",
            str(generated.get("heading_count", "n/a")),
        )

    with pre_right:
        st.metric("Has h1", str(generated.get("has_h1", "n/a")))
        st.metric("Has script", str(generated.get("has_script", "n/a")))

    with st.expander("Show extracted headings"):
        st.markdown("**Expected headings**")
        st.json(expected.get("headings", []))
        st.markdown("**Generated headings**")
        st.json(generated.get("headings", []))

    with st.expander("Show generated HTML signals"):
        st.json(
            {
                "used_tags": generated.get("used_tags", []),
                "has_span": generated.get("has_span"),
                "has_inline_style_outside_tables": generated.get(
                    "has_inline_style_outside_tables",
                ),
                "has_internal_outline_comments_exposed": generated.get(
                    "has_internal_outline_comments_exposed",
                ),
                "detected_internal_comment_patterns": generated.get(
                    "detected_internal_comment_patterns",
                    [],
                ),
            },
        )


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render the structure judge result pipeline step."""
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


def _render_structure_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the Structure API response."""
    render_exchange_summary(
        exchange,
        success_message="Structure judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def render_structure_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the structure judge form."""
    st.markdown("### Structure test input")

    if "structure_generated_html_input" not in st.session_state:
        st.session_state["structure_generated_html_input"] = ""

    if "structure_expected_outline_input" not in st.session_state:
        st.session_state["structure_expected_outline_input"] = ""

    with st.form("structure_judge_form"):
        st.markdown("**Generated content**")
        uploaded_generated_file = st.file_uploader(
            "Upload generated HTML/text file",
            type=["html", "htm", "txt"],
            key="structure_generated_file_uploader",
        )

        generated_value = st.session_state["structure_generated_html_input"]
        if uploaded_generated_file is not None:
            generated_value = read_uploaded_text_file(uploaded_generated_file)

        content = st.text_area(
            "Generated HTML to evaluate",
            height=260,
            placeholder="Paste the generated HTML here...",
            value=generated_value,
        )

        st.markdown("**Expected structure**")
        uploaded_expected_file = st.file_uploader(
            "Upload expected outline HTML/text file",
            type=["html", "htm", "txt"],
            key="structure_expected_file_uploader",
        )

        expected_value = st.session_state["structure_expected_outline_input"]
        if uploaded_expected_file is not None:
            expected_value = read_uploaded_text_file(uploaded_expected_file)

        expected_outline_html = st.text_area(
            "Expected outline HTML",
            height=260,
            placeholder="Paste the expected outline HTML here...",
            value=expected_value,
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Structure Judge")

    st.session_state["structure_generated_html_input"] = content
    st.session_state["structure_expected_outline_input"] = expected_outline_html

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "expected_outline_html": expected_outline_html,
            "locale": locale.strip() or None,
        },
    }

    st.session_state["structure_payload"] = payload
    st.session_state["structure_run_requested"] = True


def render_structure_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the API response."""
    st.markdown(
        '<div class="section-label">Structure result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("structure_payload")

    if not payload:
        st.info("Fill the form and run the Structure judge to see the response here.")
        return

    should_run = st.session_state.get("structure_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_structure_exchange")
        if last_exchange:
            _render_structure_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    context = payload.get("context", {})
    expected_outline_html = (
        context.get("expected_outline_html", "") if isinstance(context, dict) else ""
    )

    if not str(content).strip():
        st.warning("Please provide generated HTML to evaluate.")
        st.session_state["structure_run_requested"] = False
        return

    if not str(expected_outline_html).strip():
        st.warning("Please provide the expected outline HTML.")
        st.session_state["structure_run_requested"] = False
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
        st.session_state["last_structure_exchange"] = exchange
        _render_structure_exchange_summary(exchange)
        st.session_state["structure_run_requested"] = False
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
        st.session_state["last_structure_exchange"] = exchange
        _render_structure_exchange_summary(exchange)
        st.session_state["structure_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Structure judge request failed.",
    }
    st.session_state["last_structure_exchange"] = exchange
    _render_structure_exchange_summary(exchange)

    st.session_state["structure_run_requested"] = False

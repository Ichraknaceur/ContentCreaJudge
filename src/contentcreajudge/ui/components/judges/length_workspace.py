from __future__ import annotations

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
    """Render the preprocessing pipeline step."""
    st.markdown("**Preprocessing**")

    pre_left, pre_right = st.columns(2)
    with pre_left:
        st.metric("Word count", str(preprocessing.get("word_count", "n/a")))
    with pre_right:
        st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render the length judge result pipeline step."""
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


def _render_length_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the Length API response."""
    render_exchange_summary(
        exchange,
        success_message="Length judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def render_length_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the length judge form."""
    st.markdown("### Length test input")

    if "length_content_input" not in st.session_state:
        st.session_state["length_content_input"] = ""

    with st.form("length_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="length_content_file_uploader",
        )

        content_value = st.session_state["length_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        expected_length = st.selectbox(
            "Expected format",
            options=["SIMPLE", "MEDIUM", "LONG"],
            index=1,
        )

        content_type = st.selectbox(
            "Content type",
            options=[
                "articles",
                "questAnswers",
                "practicalGuide",
                "audioScript",
                "videoScript",
                "caseStudy",
                "whiteBook",
                "comparative",
                "quiz",
            ],
            index=0,
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Length Judge")

    st.session_state["length_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "content_type": content_type,
            "expected_length": expected_length,
            "locale": locale.strip() or None,
        },
    }

    st.session_state["length_payload"] = payload
    st.session_state["length_run_requested"] = True


def render_length_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the Length API response."""
    st.markdown(
        '<div class="section-label">Length result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("length_payload")

    if not payload:
        st.info("Fill the form and run the Length judge to see the response here.")
        return

    should_run = st.session_state.get("length_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_length_exchange")
        if last_exchange:
            _render_length_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["length_run_requested"] = False
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
        st.session_state["last_length_exchange"] = exchange
        _render_length_exchange_summary(exchange)
        st.session_state["length_run_requested"] = False
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
        st.session_state["last_length_exchange"] = exchange
        _render_length_exchange_summary(exchange)
        st.session_state["length_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Length judge request failed.",
    }
    st.session_state["last_length_exchange"] = exchange
    _render_length_exchange_summary(exchange)

    st.session_state["length_run_requested"] = False

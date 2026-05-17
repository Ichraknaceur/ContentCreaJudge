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
    """Render the Sources preprocessing pipeline step."""
    st.markdown("**Preprocessing**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Links", str(preprocessing.get("links_count", "n/a")))
    with col2:
        st.metric(
            "External links",
            str(preprocessing.get("external_links_count", "n/a")),
        )
    with col3:
        st.metric("Raw URLs", str(preprocessing.get("raw_urls_count", "n/a")))

    with st.expander("Show extracted links"):
        st.json(preprocessing.get("links", []))


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render the Sources judge result pipeline step."""
    st.markdown("**Judge result**")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Judge status", str(judge_result.get("status", "unknown")))
    with col2:
        st.metric("Judge score", str(judge_result.get("score", "n/a")))

    applied_rule = judge_result.get("applied_rule")
    if applied_rule:
        with st.expander("Show applied rule"):
            st.json(applied_rule)

    render_findings_section(judge_result.get("findings", []))


def _render_sources_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the Sources API response."""
    render_exchange_summary(
        exchange,
        success_message="Sources judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )

    response_body = exchange.get("response_body") or {}
    if not isinstance(response_body, dict):
        return

    url_validation = response_body.get("url_validation")
    if isinstance(url_validation, list):
        st.markdown("**URL validation**")
        with st.expander("Show URL validation results"):
            st.json(url_validation)


def render_sources_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the Sources judge form."""
    st.markdown("### Sources test input")

    if "sources_content_input" not in st.session_state:
        st.session_state["sources_content_input"] = ""

    with st.form("sources_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="sources_content_file_uploader",
        )

        content_value = st.session_state["sources_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste HTML content with sources here...",
            value=content_value,
        )

        expected_length = st.selectbox(
            "Expected length",
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

        organization_website = st.text_input(
            "Organization website",
            value="https://contentcrea.com",
            placeholder="https://contentcrea.com",
            help="Internal domain used to validate Lecture complémentaire links.",
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        require_sources = st.checkbox(
            "Require external sources",
            value=True,
        )

        submitted = st.form_submit_button("Run Sources Judge")

    st.session_state["sources_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "content_type": content_type,
            "expected_length": expected_length,
            "organization_website": organization_website.strip()
            or "https://contentcrea.com",
            "locale": locale.strip() or None,
            "require_sources": require_sources,
        },
    }

    st.session_state["sources_payload"] = payload
    st.session_state["sources_run_requested"] = True


def render_sources_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the Sources payload and display the API response."""
    st.markdown(
        '<div class="section-label">Sources result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("sources_payload")

    if not payload:
        st.info("Fill the form and run the Sources judge to see the response here.")
        return

    should_run = st.session_state.get("sources_run_requested", False)

    if not should_run:
        last_exchange = st.session_state.get("last_sources_exchange")
        if last_exchange:
            _render_sources_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")

    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["sources_run_requested"] = False
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
        st.session_state["last_sources_exchange"] = exchange
        _render_sources_exchange_summary(exchange)
        st.session_state["sources_run_requested"] = False
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
        st.session_state["last_sources_exchange"] = exchange
        _render_sources_exchange_summary(exchange)
        st.session_state["sources_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Sources judge request failed.",
    }

    st.session_state["last_sources_exchange"] = exchange
    _render_sources_exchange_summary(exchange)
    st.session_state["sources_run_requested"] = False

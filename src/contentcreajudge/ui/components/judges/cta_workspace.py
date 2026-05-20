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
    """Render the CTA preprocessing pipeline step."""
    st.markdown("**Preprocessing**")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("CTA count", str(preprocessing.get("cta_count", "n/a")))
    with col2:
        st.metric(
            "Complementary reading",
            str(preprocessing.get("has_complementary_reading", "n/a")),
        )
    with col3:
        st.metric(
            "Quiz correction",
            str(preprocessing.get("has_quiz_correction", "n/a")),
        )

    cta_texts = preprocessing.get("cta_texts", [])
    if cta_texts:
        st.markdown("**Detected CTA text(s)**")
        st.write(cta_texts)


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render the CTA judge result pipeline step."""
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


def _render_cta_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the CTA API response."""
    render_exchange_summary(
        exchange,
        success_message="CTA judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def render_cta_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the CTA judge form."""
    st.markdown("### CTA test input")

    if "cta_content_input" not in st.session_state:
        st.session_state["cta_content_input"] = ""

    st.markdown("**Content input**")

    uploaded_content_file = st.file_uploader(
        "Upload content file",
        type=["html", "htm", "txt"],
        key="cta_content_file_uploader",
    )

    if uploaded_content_file is not None:
        st.session_state["cta_content_input"] = read_uploaded_text_file(
            uploaded_content_file,
        )

    with st.form("cta_judge_form"):
        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder=('<p>Intro</p>\n<p class="cta"><strong>Read more</strong></p>'),
            key="cta_content_input",
        )

        expected_cta = st.text_input(
            "Expected CTA",
            value="Read more",
            placeholder="Read more",
        )

        funnel_stage = st.selectbox(
            "Funnel stage",
            options=["AWARENESS", "CONSIDERATION", "DECISION"],
            index=0,
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

        content_purpose = st.text_input(
            "Content purpose",
            value="Sensibilisation",
            placeholder="Sensibilisation",
        )

        language = st.selectbox(
            "Language",
            options=["fr", "en"],
            index=0,
        )

        submitted = st.form_submit_button("Run CTA Judge")

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "content_type": content_type,
            "funnel_stage": funnel_stage,
            "expected_cta": expected_cta.strip() or None,
            "content_purpose": content_purpose.strip() or None,
            "language": language,
        },
    }

    st.session_state["cta_payload"] = payload
    st.session_state["cta_run_requested"] = True


def render_cta_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the CTA API response."""
    st.markdown(
        '<div class="section-label">CTA result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("cta_payload")

    if not payload:
        st.info("Fill the form and run the CTA judge to see the response here.")
        return

    should_run = st.session_state.get("cta_run_requested", False)

    if not should_run:
        last_exchange = st.session_state.get("last_cta_exchange")
        if last_exchange:
            _render_cta_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")

    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["cta_run_requested"] = False
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
        st.session_state["last_cta_exchange"] = exchange
        _render_cta_exchange_summary(exchange)
        st.session_state["cta_run_requested"] = False
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
        st.session_state["last_cta_exchange"] = exchange
        _render_cta_exchange_summary(exchange)
        st.session_state["cta_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The CTA judge request failed.",
    }

    st.session_state["last_cta_exchange"] = exchange
    _render_cta_exchange_summary(exchange)
    st.session_state["cta_run_requested"] = False

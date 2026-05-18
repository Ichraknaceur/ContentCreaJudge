"""Global evaluation page for the Streamlit UI."""

from __future__ import annotations

# ruff: noqa: C901, D202, I001, PLR0915

import streamlit as st

from contentcreajudge.ui.components.judges.shared import read_uploaded_text_file
from contentcreajudge.ui.services.api_client import request_json


def render_global_evaluation(*, api_url: str) -> None:
    """Render the global evaluation workspace."""
    st.markdown(
        '<div class="section-label">Payload composer</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">Global evaluation</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="payload-note">
            This workspace represents the future full product flow. It already
            submits a stable payload to the global evaluation endpoint and shows
            the transport exchange end to end.
        </div>
        """,
        unsafe_allow_html=True,
    )

    form_column, result_column = st.columns([1.05, 0.95], gap="large")
    with form_column, st.form("global-evaluation-form"):
        st.text_input("Request ID", key="request_id", placeholder="demo-001")
        st.text_input(
            "Content title",
            key="content_title",
            placeholder="How to build a durable editorial workflow",
        )
        selection_left, selection_right = st.columns(2)
        with selection_left:
            st.selectbox(
                "Profile",
                options=["default", "blog", "landing-page"],
                key="profile",
            )
            st.selectbox(
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
                key="content_type",
            )
            st.selectbox(
                "Expected length",
                options=["SIMPLE", "MEDIUM", "LONG"],
                index=1,
                key="expected_length",
            )
            st.selectbox(
                "Funnel stage",
                options=["AWARENESS", "CONSIDERATION", "DECISION"],
                key="funnel_stage",
            )
        with selection_right:
            st.text_input("Channel", key="channel", placeholder="website")
            st.selectbox(
                "Locale",
                options=["fr-FR"],
                key="locale",
            )

            st.text_input(
                "Organization domain",
                key="organization_domain",
                value="https://contentcrea.com",
            )

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["txt", "html", "md"],
            key="global_content_file",
        )

        if uploaded_content_file is not None:
            uploaded_file_name = uploaded_content_file.name

            if st.session_state.get("last_uploaded_content_file") != uploaded_file_name:
                uploaded_content = read_uploaded_text_file(uploaded_content_file)

                if uploaded_content:
                    st.session_state["content"] = uploaded_content
                    st.session_state["last_uploaded_content_file"] = uploaded_file_name
        st.text_area(
            "Content",
            key="content",
            height=300,
            placeholder=(
                "Paste the editorial content here. This input will later be "
                "sent through preprocessing, mini-judges, and aggregation."
            ),
        )
        st.text_input(
            "Main keyword",
            key="main_keyword",
            placeholder="différenciation éditoriale en contexte saturé",
        )
        st.text_area(
            "Declared sources",
            key="declared_sources",
            height=110,
            placeholder="One source URL per line",
        )
        submitted = st.form_submit_button("Run global evaluation")

    with result_column:
        st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">API output</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h3 class="section-title">Response console</h3>',
            unsafe_allow_html=True,
        )
        if submitted:
            payload = _build_evaluation_payload()
            result = request_json(
                f"{api_url}/api/v1/evaluations",
                method="POST",
                payload=payload,
            )
            st.session_state["last_evaluation_exchange"] = {
                "request_payload": payload,
                "response_status": result.status_code,
                "response_body": result.payload,
                "error": result.error,
            }
            if result.ok:
                st.success("Payload accepted by the global evaluation endpoint.")
            else:
                st.error(result.error or "The evaluation request failed.")
        else:
            st.info(
                "Use the form to send a payload. The console will preserve the "
                "latest backend exchange during your demo.",
            )

        exchange = st.session_state.get("last_evaluation_exchange")
        if exchange:
            response_body = exchange.get("response_body")
            _render_global_evaluation_report(response_body)

            with st.expander("Show raw API exchange"):
                st.json(exchange)
        else:
            st.markdown(
                """
                <div class="payload-note">
                    This panel is ready to show the request payload, the backend
                    response, and later the judge-by-judge breakdown with final
                    aggregation.
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def _build_evaluation_payload() -> dict[str, object]:
    """Build the global evaluation payload from the current form state."""

    context = {
        "content_type": st.session_state.get("content_type", "articles"),
        "expected_length": st.session_state.get("expected_length", "MEDIUM"),
        "locale": st.session_state.get("locale", "fr-FR"),
        "funnel_stage": st.session_state.get("funnel_stage", "AWARENESS"),
        "main_keyword": st.session_state.get("main_keyword", ""),
        "secondary_keywords": [],
        "long_tail_keywords": [],
        "organization_domain": st.session_state.get(
            "organization_domain",
            "https://contentcrea.com",
        ),
    }

    payload: dict[str, object] = {
        "content": st.session_state.get("content", ""),
        "profile": st.session_state.get("profile", "default"),
        "context": context,
        "enabled_judges": ["length", "typography", "seo"],
    }

    request_id = st.session_state.get("request_id", "")
    if request_id:
        payload["request_id"] = request_id

    return payload


def _render_global_evaluation_report(response_body: object) -> None:
    """Render a readable global evaluation report."""

    if not isinstance(response_body, dict):
        st.warning("Response body is not a JSON object.")
        return

    st.markdown("### Global evaluation report")

    status = response_body.get("status", "unknown")
    score = response_body.get("score", "n/a")
    summary = response_body.get("summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Global status", str(status))

    with col2:
        st.metric("Global score", str(score))

    if summary:
        st.caption(str(summary))

    judge_results = response_body.get("judge_results", [])

    if not isinstance(judge_results, list) or not judge_results:
        st.info("No judge result available yet.")
        return

    st.markdown("#### Judge results")

    for judge_result in judge_results:
        if not isinstance(judge_result, dict):
            continue

        judge_name = str(judge_result.get("judge", "unknown"))
        judge_status = str(judge_result.get("status", "unknown"))
        judge_score = judge_result.get("score", "n/a")

        st.markdown(f"**{judge_name}**")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Status", judge_status)

        with col2:
            st.metric("Score", str(judge_score))

        subscores = judge_result.get("subscores")

        if isinstance(subscores, dict) and subscores:
            displayed_subscores = {
                key: value
                for key, value in subscores.items()
                if key != "overoptimization_applicable"
            }

            if displayed_subscores:
                st.markdown("**Subscores**")
                columns = st.columns(len(displayed_subscores))

                for column, (name, value) in zip(
                    columns,
                    displayed_subscores.items(),
                    strict=False,
                ):
                    with column:
                        st.metric(str(name), str(value))

        findings = judge_result.get("findings", [])
        if not isinstance(findings, list):
            findings = []

        if findings:
            with st.expander(f"Findings — {judge_name}"):
                st.json(findings)

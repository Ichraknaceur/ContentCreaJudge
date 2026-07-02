"""Global evaluation page for the Streamlit UI."""

from __future__ import annotations

# ruff: noqa: C901, D202, I001, PLR0912, PLR0915

import streamlit as st

from contentcreajudge.application.orchestration.company_context_resolver import (
    build_global_payload_from_content,
    list_exported_contents,
    load_company_export_from_zip,
)
from contentcreajudge.ui.components.judges.shared import read_uploaded_text_file
from contentcreajudge.ui.services.api_client import request_json


ENABLED_GLOBAL_JUDGES = [
    "length",
    "typography",
    "seo",
    "structure",
    "sources",
]


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

    with form_column:
        uploaded_company_zip = st.file_uploader(
            "Upload company export ZIP",
            type=["zip"],
            key="global_company_export_zip",
        )

        if uploaded_company_zip is not None:
            zip_name = uploaded_company_zip.name

            if st.session_state.get("last_uploaded_company_zip") != zip_name:
                try:
                    company_export = load_company_export_from_zip(
                        uploaded_company_zip.getvalue(),
                    )
                except ValueError as error:
                    st.error(f"Invalid company export ZIP: {error}")
                else:
                    st.session_state["company_export"] = company_export
                    st.session_state["last_uploaded_company_zip"] = zip_name

        company_export = st.session_state.get("company_export")

        if isinstance(company_export, dict):
            exported_contents = list_exported_contents(company_export)

            if exported_contents:
                selected_label = st.selectbox(
                    "Select exported content",
                    options=[
                        content.get("label", content.get("id", "Untitled content"))
                        for content in exported_contents
                    ],
                    key="selected_exported_content_label",
                )

                selected_content = next(
                    (
                        content
                        for content in exported_contents
                        if content.get("label") == selected_label
                    ),
                    None,
                )

                if selected_content:
                    selected_content_id = selected_content.get("id")

                    if selected_content_id:
                        st.session_state["selected_exported_content_id"] = (
                            selected_content_id
                        )

                        preview_payload = build_global_payload_from_content(
                            company_export=company_export,
                            content_id=str(selected_content_id),
                            profile=st.session_state.get("profile", "default"),
                            request_id=st.session_state.get("request_id") or None,
                        )

                        preview_context = preview_payload.get("context", {})

                        if isinstance(preview_context, dict):
                            _hydrate_session_state_from_preview(
                                preview_payload,
                                preview_context,
                            )
                            _render_context_preview(preview_payload, preview_context)

    with form_column, st.form("global-evaluation-form"):
        st.text_input("Request ID", key="request_id", placeholder="demo-001")

        with st.expander("Advanced manual overrides"):
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
                    "Organization website",
                    key="organization_website",
                    value="https://contentcrea.com",
                )
                st.checkbox(
                    "Require external sources",
                    key="require_sources",
                    value=True,
                )

            uploaded_content_file = st.file_uploader(
                "Upload content file",
                type=["txt", "html", "md"],
                key="global_content_file",
            )

            if uploaded_content_file is not None:
                uploaded_file_name = uploaded_content_file.name

                if st.session_state.get("last_uploaded_content_file") != (
                    uploaded_file_name
                ):
                    uploaded_content = read_uploaded_text_file(uploaded_content_file)

                    if uploaded_content:
                        st.session_state["content"] = uploaded_content
                        st.session_state["last_uploaded_content_file"] = (
                            uploaded_file_name
                        )

            st.text_area(
                "Content",
                key="content",
                height=300,
                placeholder=(
                    "Paste the editorial content here. This input will later be "
                    "sent through preprocessing, mini-judges, and aggregation."
                ),
            )

            uploaded_outline_file = st.file_uploader(
                "Upload expected outline file",
                type=["txt", "html", "md"],
                key="global_expected_outline_file",
            )

            if uploaded_outline_file is not None:
                uploaded_outline_file_name = uploaded_outline_file.name

                if (
                    st.session_state.get("last_uploaded_expected_outline_file")
                    != uploaded_outline_file_name
                ):
                    uploaded_outline = read_uploaded_text_file(uploaded_outline_file)

                    if uploaded_outline:
                        st.session_state["expected_outline_html"] = uploaded_outline
                        st.session_state["last_uploaded_expected_outline_file"] = (
                            uploaded_outline_file_name
                        )

            st.text_area(
                "Expected outline HTML",
                key="expected_outline_html",
                height=180,
                placeholder=(
                    "Paste the expected structure/outline HTML here. "
                    "Example: <p>Intro...</p><h2>Section</h2><h3>Subsection</h3>"
                ),
            )
            st.text_input(
                "Main keyword",
                key="main_keyword",
                placeholder="différenciation éditoriale en contexte saturé",
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


def _hydrate_session_state_from_preview(
    preview_payload: dict[str, object],
    preview_context: dict[str, object],
) -> None:
    """Hydrate manual override fields from the selected ZIP content."""

    st.session_state["content"] = str(preview_payload.get("content", ""))
    st.session_state["content_type"] = str(
        preview_context.get("content_type", "articles"),
    )
    st.session_state["expected_length"] = str(
        preview_context.get("expected_length", "MEDIUM"),
    )
    st.session_state["funnel_stage"] = str(
        preview_context.get("funnel_stage", "AWARENESS"),
    )
    st.session_state["main_keyword"] = str(
        preview_context.get("main_keyword", ""),
    )
    st.session_state["expected_outline_html"] = str(
        preview_context.get("expected_outline_html", ""),
    )
    st.session_state["organization_website"] = str(
        preview_context.get("organization_website", "https://contentcrea.com"),
    )
    st.session_state["require_sources"] = bool(
        preview_context.get("require_sources", True),
    )


def _render_context_preview(
    preview_payload: dict[str, object],
    preview_context: dict[str, object],
) -> None:
    """Render a compact preview of the auto-filled evaluation context."""

    with st.expander("Preview auto-filled evaluation context", expanded=True):
        st.json(
            {
                "content_type": preview_context.get("content_type"),
                "expected_length": preview_context.get("expected_length"),
                "funnel_stage": preview_context.get("funnel_stage"),
                "main_keyword": preview_context.get("main_keyword"),
                "organization_website": preview_context.get("organization_website"),
                "expected_cta": preview_context.get("expected_cta"),
                "evergreen": preview_context.get("evergreen"),
                "content_loaded": bool(preview_payload.get("content")),
                "expected_outline_loaded": bool(
                    preview_context.get("expected_outline_html"),
                ),
            },
        )


def _build_evaluation_payload() -> dict[str, object]:
    """Build the global evaluation payload from the current form state."""

    company_export = st.session_state.get("company_export")

    if isinstance(company_export, dict):
        exported_contents = list_exported_contents(company_export)
        selected_label = st.session_state.get("selected_exported_content_label")

        selected_content = next(
            (
                content
                for content in exported_contents
                if content.get("label") == selected_label
            ),
            None,
        )

        if selected_content:
            selected_content_id = selected_content.get("id")

            if selected_content_id:
                payload = build_global_payload_from_content(
                    company_export=company_export,
                    content_id=str(selected_content_id),
                    profile=st.session_state.get("profile", "default"),
                    request_id=st.session_state.get("request_id") or None,
                )

                payload["enabled_judges"] = ENABLED_GLOBAL_JUDGES

                return payload

    context = {
        "content_type": st.session_state.get("content_type", "articles"),
        "expected_length": st.session_state.get("expected_length", "MEDIUM"),
        "locale": st.session_state.get("locale", "fr-FR"),
        "funnel_stage": st.session_state.get("funnel_stage", "AWARENESS"),
        "main_keyword": st.session_state.get("main_keyword", ""),
        "secondary_keywords": [],
        "long_tail_keywords": [],
        "expected_outline_html": st.session_state.get("expected_outline_html", ""),
        "require_sources": st.session_state.get("require_sources", True),
        "organization_website": st.session_state.get(
            "organization_website",
            "https://contentcrea.com",
        ),
    }

    payload: dict[str, object] = {
        "content": st.session_state.get("content", ""),
        "profile": st.session_state.get("profile", "default"),
        "context": context,
        "enabled_judges": ENABLED_GLOBAL_JUDGES,
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

    technical_errors = response_body.get("technical_errors", [])
    if isinstance(technical_errors, list) and technical_errors:
        with st.expander("Technical errors", expanded=True):
            st.json(technical_errors)

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
                for finding in findings:
                    if not isinstance(finding, dict):
                        continue

                    rule_id = str(finding.get("rule_id", "unknown"))
                    severity = str(finding.get("severity", "unknown"))
                    message = str(finding.get("message", "No message"))

                    st.markdown(f"**{rule_id}** — `{severity}`")
                    st.write(message)

                    evidence = finding.get("evidence")
                    if isinstance(evidence, dict) and evidence:
                        st.json(evidence)

        if judge_name == "seo":
            _render_seo_details(judge_result)


def _render_seo_details(judge_result: dict[str, object]) -> None:
    """Render SEO-specific details in the global report."""

    semantic_signals = judge_result.get("semantic_signals")
    semantic_compensation = judge_result.get("semantic_compensation")
    overoptimization_signals = judge_result.get("overoptimization_signals")

    if isinstance(semantic_signals, dict) and semantic_signals:
        with st.expander("SEO semantic details"):
            st.json(semantic_signals)

    if isinstance(semantic_compensation, dict) and semantic_compensation:
        with st.expander("SEO semantic compensation"):
            st.json(semantic_compensation)

    if isinstance(overoptimization_signals, dict) and overoptimization_signals:
        with st.expander("SEO overoptimization details"):
            st.json(overoptimization_signals)

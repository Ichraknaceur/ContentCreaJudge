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


def _parse_keywords(raw_value: str) -> list[str]:
    """Parse a textarea value into a clean keyword list."""
    keywords: list[str] = []

    for line in raw_value.splitlines():
        cleaned = line.strip()
        if cleaned:
            keywords.append(cleaned)

    return keywords


def _render_preprocessing_section(preprocessing: dict[str, object]) -> None:
    """Render the preprocessing pipeline step."""
    st.markdown("**Preprocessing**")

    pre_left, pre_right = st.columns(2)

    with pre_left:
        st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))

    with pre_right:
        headings = preprocessing.get("headings_h2_h3", [])
        heading_count = len(headings) if isinstance(headings, list) else "n/a"
        st.metric("H2/H3 count", str(heading_count))

    lexical_signals = preprocessing.get("lexical_signals")
    if lexical_signals:
        with st.expander("Show lexical signals"):
            st.json(lexical_signals)

    semantic_inputs = preprocessing.get("semantic_inputs")
    if semantic_inputs:
        with st.expander("Show semantic inputs"):
            st.json(semantic_inputs)


def _render_subscores_section(subscores: dict[str, object]) -> None:
    """Render SEO subscores."""
    st.markdown("**Subscores**")

    sub_left, sub_middle, sub_right = st.columns(3)

    with sub_left:
        st.metric("Lexical score", str(subscores.get("lexical", "n/a")))

    with sub_middle:
        st.metric("Semantic score", str(subscores.get("semantic", "n/a")))

    with sub_right:
        if subscores.get("overoptimization_applicable") is False:
            st.metric("Overoptimization score", "n/a")
        else:
            st.metric(
                "Overoptimization score",
                str(subscores.get("overoptimization", "n/a")),
            )


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render the SEO judge result pipeline step."""
    st.markdown("**Judge result**")

    judge_left, judge_right = st.columns(2)
    with judge_left:
        st.metric("Judge status", str(judge_result.get("status", "unknown")))
    with judge_right:
        st.metric("Judge score", str(judge_result.get("score", "n/a")))

    subscores = judge_result.get("subscores")
    if isinstance(subscores, dict):
        _render_subscores_section(subscores)

    semantic_signals = judge_result.get("semantic_signals")
    if semantic_signals:
        with st.expander("Show semantic signals"):
            st.json(semantic_signals)

    overoptimization_signals = judge_result.get("overoptimization_signals")
    if overoptimization_signals:
        with st.expander("Show overoptimization signals"):
            st.json(overoptimization_signals)

    applied_rule = judge_result.get("applied_rule")
    if applied_rule:
        with st.expander("Show applied rule"):
            st.json(applied_rule)

    render_findings_section(judge_result.get("findings", []))


def _render_seo_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the SEO API response."""
    render_exchange_summary(
        exchange,
        success_message="SEO judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def render_seo_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the SEO judge form."""
    st.markdown("### SEO test input")

    if "seo_content_input" not in st.session_state:
        st.session_state["seo_content_input"] = ""

    with st.form("seo_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="seo_content_file_uploader",
        )

        content_value = st.session_state["seo_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
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

        expected_length = st.selectbox(
            "Expected length",
            options=["SIMPLE", "MEDIUM", "LONG"],
            index=1,
        )

        funnel_stage = st.selectbox(
            "Funnel stage",
            options=["AWARENESS", "CONSIDERATION", "DECISION"],
            index=0,
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        main_keyword = st.text_input(
            "Main keyword",
            placeholder="Enter the main keyword",
        )

        secondary_keywords_raw = st.text_area(
            "Secondary keywords (one per line)",
            height=120,
            placeholder="Keyword 1\nKeyword 2\nKeyword 3",
        )

        long_tail_keywords_raw = st.text_area(
            "Long-tail keywords (one per line)",
            height=120,
            placeholder="Long-tail keyword 1\nLong-tail keyword 2",
        )

        submitted = st.form_submit_button("Run SEO Judge")

    st.session_state["seo_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "content_type": content_type,
            "expected_length": expected_length,
            "funnel_stage": funnel_stage,
            "locale": locale.strip() or None,
            "main_keyword": main_keyword.strip(),
            "secondary_keywords": _parse_keywords(secondary_keywords_raw),
            "long_tail_keywords": _parse_keywords(long_tail_keywords_raw),
        },
    }

    st.session_state["seo_payload"] = payload
    st.session_state["seo_run_requested"] = True


def render_seo_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the SEO API response."""
    st.markdown(
        '<div class="section-label">SEO result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("seo_payload")

    if not payload:
        st.info("Fill the form and run the SEO judge to see the response here.")
        return

    should_run = st.session_state.get("seo_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_seo_exchange")
        if last_exchange:
            _render_seo_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    context = payload.get("context", {})
    main_keyword = context.get("main_keyword", "") if isinstance(context, dict) else ""

    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["seo_run_requested"] = False
        return

    if not str(main_keyword).strip():
        st.warning("Please provide the main keyword.")
        st.session_state["seo_run_requested"] = False
        return

    endpoint = f"{api_url.rstrip('/')}{selected_item.endpoint}"

    try:
        response = requests.post(endpoint, json=payload, timeout=60)
    except requests.RequestException as exc:
        exchange = {
            "request_payload": payload,
            "response_status": None,
            "response_body": None,
            "error": f"API request failed: {exc}",
        }
        st.session_state["last_seo_exchange"] = exchange
        _render_seo_exchange_summary(exchange)
        st.session_state["seo_run_requested"] = False
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
        st.session_state["last_seo_exchange"] = exchange
        _render_seo_exchange_summary(exchange)
        st.session_state["seo_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The SEO judge request failed.",
    }
    st.session_state["last_seo_exchange"] = exchange
    _render_seo_exchange_summary(exchange)

    st.session_state["seo_run_requested"] = False

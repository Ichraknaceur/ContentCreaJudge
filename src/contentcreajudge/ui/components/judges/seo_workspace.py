from __future__ import annotations

from typing import Any

import requests
import streamlit as st


def _parse_keywords(raw_value: str) -> list[str]:
    """Parse a textarea value into a clean keyword list."""
    keywords: list[str] = []

    for line in raw_value.splitlines():
        cleaned = line.strip()
        if cleaned:
            keywords.append(cleaned)

    return keywords


def _render_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the SEO API response in a readable way."""
    response_status = exchange.get("response_status")
    response_body = exchange.get("response_body") or {}
    error = exchange.get("error")

    if error:
        st.error(str(error))
    elif response_status and 200 <= int(response_status) < 300:
        st.success("SEO judge executed successfully.")
    else:
        st.error(f"Request failed with status {response_status}.")

    if not isinstance(response_body, dict):
        st.warning("Response body is not a JSON object.")
        with st.expander("Show raw API exchange"):
            st.json(exchange)
        return

    rule_resolution = response_body.get("rule_resolution")
    preprocessing = response_body.get("preprocessing")
    judge_result = response_body.get("judge_result")
    #aggregation = response_body.get("aggregation")
    response_message = response_body.get("message")

    if response_message:
        st.caption(str(response_message))

    st.markdown("#### Pipeline steps")

    if isinstance(rule_resolution, dict):
        st.markdown(
            f"**Rule resolution** - profile: "
            f"`{rule_resolution.get('profile', 'unknown')}`"
        )

        judge_rules = rule_resolution.get("judge_rules")
        if judge_rules:
            with st.expander("Show resolved rules"):
                st.json(judge_rules)

    if isinstance(preprocessing, dict):
        st.markdown("**Preprocessing**")
        pre_left, pre_right = st.columns(2)
        with pre_left:
            st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))
        with pre_right:
            headings = preprocessing.get("headings_h2_h3", [])
            st.metric("H2/H3 count", str(len(headings) if isinstance(headings, list) else "n/a"))

        lexical_signals = preprocessing.get("lexical_signals")
        if lexical_signals:
            with st.expander("Show lexical signals"):
                st.json(lexical_signals)

        semantic_inputs = preprocessing.get("semantic_inputs")
        if semantic_inputs:
            with st.expander("Show semantic inputs"):
                st.json(semantic_inputs)

        thematic_signals = preprocessing.get("thematic_signals")
        if thematic_signals:
            with st.expander("Show thematic signals"):
                st.json(thematic_signals)

    if isinstance(judge_result, dict):
        st.markdown("**Judge result**")
        judge_left, judge_right = st.columns(2)
        with judge_left:
            st.metric("Judge status", str(judge_result.get("status", "unknown")))
        with judge_right:
            st.metric("Judge score", str(judge_result.get("score", "n/a")))

        subscores = judge_result.get("subscores")
        if isinstance(subscores, dict):
            st.markdown("**Subscores**")
            sub_left, sub_middle, sub_right = st.columns(3)

            with sub_left:
                st.metric("Lexical score", str(subscores.get("lexical", "n/a")))

            with sub_middle:
                st.metric("Semantic score", str(subscores.get("semantic", "n/a")))

            with sub_right:
                st.metric("Thematic score", str(subscores.get("thematic", "n/a")))

        semantic_signals = judge_result.get("semantic_signals")
        if semantic_signals:
            with st.expander("Show semantic signals"):
                st.json(semantic_signals)

        semantic_compensation = judge_result.get("semantic_compensation")
        if semantic_compensation:
            with st.expander("Show semantic compensation"):
                st.json(semantic_compensation)

        thematic_signals = judge_result.get("thematic_signals")
        if thematic_signals:
            with st.expander("Show thematic judge signals"):
                st.json(thematic_signals)

        applied_rule = judge_result.get("applied_rule")
        if applied_rule:
            with st.expander("Show applied rule"):
                st.json(applied_rule)

        findings = judge_result.get("findings", [])
        if findings:
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
                    st.caption(
                        ", ".join(
                            f"{key}: {value}" for key, value in evidence.items()
                        )
                    )

    with st.expander("Show raw API exchange"):
        st.json(exchange)


def render_seo_form(selected_item: Any) -> None:
    """Render the SEO judge form."""
    st.markdown("### SEO test input")

    with st.form("seo_judge_form"):
        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
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


def render_seo_result(api_url: str, selected_item: Any) -> None:
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
            _render_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
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
        _render_exchange_summary(exchange)
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
        _render_exchange_summary(exchange)
        st.session_state["seo_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The SEO judge request failed.",
    }
    st.session_state["last_seo_exchange"] = exchange
    _render_exchange_summary(exchange)

    st.session_state["seo_run_requested"] = False
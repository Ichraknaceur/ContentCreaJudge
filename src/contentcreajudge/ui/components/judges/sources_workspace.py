from __future__ import annotations

from typing import Any

import requests
import streamlit as st


def _render_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the API response for the Sources judge."""

    response_status = exchange.get("response_status")
    response_body = exchange.get("response_body") or {}
    error = exchange.get("error")

    if error:
        st.error(str(error))
    elif response_status and 200 <= int(response_status) < 300:
        st.success("Sources judge executed successfully.")
    else:
        st.error(f"Request failed with status {response_status}.")

    if not isinstance(response_body, dict):
        st.warning("Response body is not a JSON object.")
        with st.expander("Show raw API exchange"):
            st.json(exchange)
        return

    rule_resolution = response_body.get("rule_resolution")
    preprocessing = response_body.get("preprocessing")
    url_validation = response_body.get("url_validation")
    judge_result = response_body.get("judge_result")
    aggregation = response_body.get("aggregation")
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
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Links", str(preprocessing.get("links_count", "n/a")))
        with col2:
            st.metric(
                "External links",
                str(preprocessing.get("external_links_count", "n/a")),
            )
        with col3:
            st.metric(
                "Raw URLs",
                str(preprocessing.get("raw_urls_count", "n/a")),
            )

        with st.expander("Show extracted links"):
            st.json(preprocessing.get("links", []))

    if isinstance(url_validation, list):
        st.markdown("**URL validation**")
        with st.expander("Show URL validation results"):
            st.json(url_validation)

    if isinstance(judge_result, dict):
        st.markdown("**Judge result**")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Judge status", str(judge_result.get("status", "unknown")))
        with col2:
            st.metric("Judge score", str(judge_result.get("score", "n/a")))

        findings = judge_result.get("findings", [])
        if findings:
            st.markdown("**Findings**")
            for finding in findings:
                if not isinstance(finding, dict):
                    continue

                severity = str(finding.get("severity", "unknown"))
                message = str(finding.get("message", "No message"))
                rule_id = str(finding.get("rule_id", "unknown"))

                st.markdown(f"- `{severity}` - {message} (`{rule_id}`)")

                evidence = finding.get("evidence")
                if isinstance(evidence, dict) and evidence:
                    st.caption(
                        ", ".join(
                            f"{key}: {value}" for key, value in evidence.items()
                        )
                    )

    if isinstance(aggregation, dict):
        st.markdown("**Aggregation**")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Global status", str(aggregation.get("status", "unknown")))
        with col2:
            st.metric("Global score", str(aggregation.get("score", "n/a")))

        summary = aggregation.get("summary")
        if summary:
            st.caption(str(summary))

    with st.expander("Show raw API exchange"):
        st.json(exchange)


def render_sources_form(selected_item: Any) -> None:
    """Render the Sources judge form."""

    st.markdown("### Sources test input")

    with st.form("sources_judge_form"):
        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste HTML content with sources here...",
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

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "content_type": content_type,
            "expected_length": expected_length,
            "locale": locale.strip() or None,
            "require_sources": require_sources,
        },
    }

    st.session_state["sources_payload"] = payload
    st.session_state["sources_run_requested"] = True


def render_sources_result(api_url: str, selected_item: Any) -> None:
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
            _render_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")

    if not str(content).strip():
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
        _render_exchange_summary(exchange)
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
        _render_exchange_summary(exchange)
        st.session_state["sources_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Sources judge request failed.",
    }

    st.session_state["last_sources_exchange"] = exchange
    _render_exchange_summary(exchange)
    st.session_state["sources_run_requested"] = False
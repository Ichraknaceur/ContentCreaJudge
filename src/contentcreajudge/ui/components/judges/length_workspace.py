from __future__ import annotations

from typing import Any

import requests
import streamlit as st


def _render_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the API response in a much more readable way"""
    response_status = exchange.get("response_status")
    response_body = exchange.get("response_body") or {}
    error = exchange.get("error")

    if error:
        st.error(str(error))
    elif response_status and 200 <= int(response_status) < 300:
        st.success("Length judge executed successfully.")
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
            st.metric("Word count", str(preprocessing.get("word_count", "n/a")))
        with pre_right:
            st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))

    if isinstance(judge_result, dict):
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


def render_length_form(selected_item: Any) -> None:
    """Render the length judge form"""
    st.markdown("### Length test input")

    with st.form("length_judge_form"):
        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
        )

        expected_format = st.selectbox(
            "Expected format",
            options=["SIMPLE", "MEDIUM", "LONG"],
            index=1,
        )

        content_type = st.selectbox(
            "Content type",
            options=["articles", "questAnswers", "practicalGuide", "audioScript", "videoScript",
                     "caseStudy", "whiteBook", "comparative", "quiz"],
            index=0,
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Length Judge")

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "content_type": content_type,
            "expected_length": expected_format,
            "locale": locale.strip() or None,
        },
    }

    st.session_state["length_payload"] = payload
    st.session_state["length_run_requested"] = True


def render_length_result(api_url: str, selected_item: Any) -> None:
    """Read the payload and display the API response"""
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
            _render_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not content.strip():
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
        _render_exchange_summary(exchange)
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
        _render_exchange_summary(exchange)
        st.session_state["length_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Length judge request failed.",
    }
    st.session_state["last_length_exchange"] = exchange
    _render_exchange_summary(exchange)

    st.session_state["length_run_requested"] = False

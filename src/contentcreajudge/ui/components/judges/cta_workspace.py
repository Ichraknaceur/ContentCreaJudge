from __future__ import annotations

from typing import Any, Protocol

import requests
import streamlit as st

class UploadedTextFile(Protocol):
    """Readable uploaded file interface used by Streamlit."""

    def read(self) -> bytes:
        """Read uploaded file bytes."""


def _read_uploaded_text_file(uploaded_file: UploadedTextFile | None) -> str:
    """Read an uploaded text-based file and return its UTF-8 content."""
    if uploaded_file is None:
        return ""

    file_bytes = uploaded_file.read()
    if not file_bytes:
        return ""

    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("utf-8", errors="replace")

def _render_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the CTA API response in a readable way."""

    response_status = exchange.get("response_status")
    response_body = exchange.get("response_body") or {}
    error = exchange.get("error")

    if error:
        st.error(str(error))
    elif response_status and 200 <= int(response_status) < 300:
        st.success("CTA judge executed successfully.")
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

    if isinstance(judge_result, dict):
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
            st.info(str(summary))

    with st.expander("Show raw API exchange"):
        st.json(exchange)


def render_cta_form(selected_item: Any) -> None:
    """Render the CTA judge form."""
    del selected_item

    st.markdown("### CTA test input")

    if "cta_content_input" not in st.session_state:
        st.session_state["cta_content_input"] = ""

    with st.form("cta_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="cta_content_file_uploader",
        )

        content_value = st.session_state["cta_content_input"]
        if uploaded_content_file is not None:
            content_value = _read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder=(
                '<p>Intro</p>\n'
                '<p class="cta"><strong>Read more</strong></p>'
            ),
            value=content_value,
        )

        cta_options = [
            # Awareness
            "En savoir plus",
            "Lire la suite",
            "Découvrir",
            "Explorer",
            "Consulter",
            "Learn more",
            "Read more",
            "Discover",
            "Explore",
            "View more",

            # Consideration
            "Comparer",
            "Télécharger",
            "Nous contacter",
            "Soumettre un formulaire",
            "Demander une démo",
            "Compare",
            "Download",
            "Contact us",
            "Submit a form",
            "Request a demo",

            # Decision
            "Souscrire",
            "S'inscrire",
            "S'enregistrer",
            "Réserver",
            "Commencer",
            "Subscribe",
            "Sign up",
            "Register",
            "Book",
            "Get started",

            # Option vide (important)
            "— Aucun CTA —"
        ]

        expected_cta = st.selectbox(
            "Expected CTA",
            options=cta_options,
            index=6,  # "Read more" par défaut
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

    st.session_state["cta_content_input"] = content

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


def render_cta_result(api_url: str, selected_item: Any) -> None:
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
            _render_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")

    if not str(content).strip():
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
        _render_exchange_summary(exchange)
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
        _render_exchange_summary(exchange)
        st.session_state["cta_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The CTA judge request failed.",
    }

    st.session_state["last_cta_exchange"] = exchange
    _render_exchange_summary(exchange)
    st.session_state["cta_run_requested"] = False
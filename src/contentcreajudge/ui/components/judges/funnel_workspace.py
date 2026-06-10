from __future__ import annotations

from typing import TYPE_CHECKING

import requests
import streamlit as st

from contentcreajudge.ui.components.judges.shared import (
    read_uploaded_text_file,
    render_exchange_summary,
)

if TYPE_CHECKING:
    from contentcreajudge.ui.viewmodels.judge_playground_vm import JudgeWorkbenchItem


def _safe_progress_score(value: object) -> float:
    """Return a Streamlit progress-compatible score."""
    try:
        score = int(value)
    except TypeError, ValueError:
        return 0.0

    return max(0, min(100, score)) / 100


def _render_preprocessing_section(preprocessing: dict[str, object]) -> None:
    """Render the preprocessing pipeline step."""
    st.markdown("**Preprocessing**")

    pre_left, pre_right = st.columns(2)
    with pre_left:
        st.metric("Word count", str(preprocessing.get("word_count", "n/a")))
    with pre_right:
        st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))


def _render_scores_with_progress(scores: object, label: str) -> None:
    """Render a score mapping with progress bars."""
    if not isinstance(scores, dict) or not scores:
        return

    st.markdown(f"**{label}**")

    for name, score in scores.items():
        st.progress(_safe_progress_score(score))
        st.caption(f"{name}: {score}/100")


def _render_signal_list(title: str, signals: object) -> None:
    """Render a list of funnel signals."""
    if not isinstance(signals, list) or not signals:
        return

    st.markdown(f"**{title}**")
    for signal in signals:
        st.markdown(f"- {signal}")


def _render_blind_detection_summary(phase_1: dict[str, object]) -> None:
    """Render blind funnel detection in a readable way."""
    st.markdown("##### Détection naturelle du funnel")

    detected_funnel = str(phase_1.get("detected_funnel", "unknown"))

    st.metric("Funnel détecté", detected_funnel)

    _render_scores_with_progress(
        phase_1.get("scores_by_funnel"),
        "Scores par funnel",
    )

    cols = st.columns(2)
    with cols[0]:
        _render_signal_list("Signaux dominants", phase_1.get("dominant_signals"))
    with cols[1]:
        _render_signal_list("Signaux secondaires", phase_1.get("secondary_signals"))


def _render_criteria_scores_table(criteria_scores: object) -> None:
    """Render criteria scores as a compact table."""
    if not isinstance(criteria_scores, dict) or not criteria_scores:
        return

    st.markdown("**Scores par critère**")

    rows = [
        {
            "Critère": criterion,
            "Score": f"{score}/100",
        }
        for criterion, score in criteria_scores.items()
    ]

    st.table(rows)


def _render_expected_funnel_summary(phase_2: dict[str, object]) -> None:
    """Render expected funnel evaluation in a readable way."""
    st.markdown("##### Évaluation du funnel attendu")

    cols = st.columns(4)
    cols[0].metric("Funnel attendu", str(phase_2.get("expected_funnel", "unknown")))
    cols[1].metric("Score critères", str(phase_2.get("expected_funnel_score", "n/a")))
    cols[2].metric("Alignement", str(phase_2.get("funnel_alignment_score", "n/a")))
    cols[3].metric("Score final", str(phase_2.get("final_score", "n/a")))

    _render_criteria_scores_table(phase_2.get("criteria_scores"))

    cols = st.columns(2)
    with cols[0]:
        _render_signal_list("Points forts", phase_2.get("strengths"))
    with cols[1]:
        _render_signal_list("Points faibles", phase_2.get("weaknesses"))


def _render_funnel_findings_section(findings: object) -> None:
    """Render funnel findings with their custom schema."""
    if not isinstance(findings, list) or not findings:
        st.info("No findings reported.")
        return

    for finding in findings:
        if not isinstance(finding, dict):
            continue

        severity = str(finding.get("severity", "unknown"))
        criterion = str(finding.get("criterion", "unknown"))
        observation = str(finding.get("observation", "No observation"))
        explanation = str(finding.get("explanation", ""))
        excerpt = str(finding.get("excerpt", ""))

        st.markdown(f"**{severity.upper()} — {criterion}**")
        st.write(observation)

        if explanation:
            st.caption(explanation)

        if excerpt:
            st.code(excerpt, language="text")


def _render_provider_raw_json(
    provider_label: str,
    phase_1: object,
    phase_2: object,
    applied_rule: object,
) -> None:
    """Render all raw JSON debug data for one provider in one collapse."""
    with st.expander(f"{provider_label} — JSON brut"):
        st.markdown("##### Détection naturelle du funnel")
        if isinstance(phase_1, dict):
            st.json(phase_1)
        else:
            st.info("No phase 1 JSON available.")

        st.markdown("##### Évaluation du funnel attendu")
        if isinstance(phase_2, dict):
            st.json(phase_2)
        else:
            st.info("No phase 2 JSON available.")

        st.markdown("##### Règles appliquées")
        if applied_rule:
            st.json(applied_rule)
        else:
            st.info("No applied rule available.")


def _render_provider_result(provider: str, judge_result: dict[str, object]) -> None:
    """Render one provider funnel judge result."""
    provider_label = provider.upper()

    st.markdown("---")
    st.markdown(f"### {provider_label}")

    col_status, col_score = st.columns(2)
    with col_status:
        st.metric("Statut", str(judge_result.get("status", "unknown")))
    with col_score:
        st.metric("Score", str(judge_result.get("score", "n/a")))

    phase_1 = judge_result.get("phase_1")
    phase_2 = judge_result.get("phase_2")

    if isinstance(phase_1, dict):
        _render_blind_detection_summary(phase_1)

    st.markdown("")

    if isinstance(phase_2, dict):
        _render_expected_funnel_summary(phase_2)

    with st.expander(f"{provider_label} — Findings détaillés"):
        _render_funnel_findings_section(judge_result.get("findings", []))

    _render_provider_raw_json(
        provider_label=provider_label,
        phase_1=phase_1,
        phase_2=phase_2,
        applied_rule=judge_result.get("applied_rule"),
    )


def _render_judge_results_section(response_body: dict[str, object]) -> None:
    """Render OpenAI and Mistral judge results."""
    st.markdown("**Judge results**")

    judge_results = response_body.get("judge_results")
    if not isinstance(judge_results, dict):
        st.warning("No provider judge results found.")
        return

    openai_result = judge_results.get("openai")
    mistral_result = judge_results.get("mistral")

    if isinstance(openai_result, dict):
        _render_provider_result("openai", openai_result)

    if isinstance(mistral_result, dict):
        _render_provider_result("mistral", mistral_result)


def _render_funnel_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the Funnel API response."""
    response_body = exchange.get("response_body")

    render_exchange_summary(
        exchange,
        success_message="Funnel judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=None,
    )

    if isinstance(response_body, dict):
        _render_judge_results_section(response_body)

        aggregations = response_body.get("aggregations")
        if isinstance(aggregations, dict):
            with st.expander("Aggregations JSON"):
                st.json(aggregations)


def render_funnel_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the funnel judge form."""
    st.markdown("### Funnel test input")

    if "funnel_content_input" not in st.session_state:
        st.session_state["funnel_content_input"] = ""

    with st.form("funnel_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="funnel_content_file_uploader",
        )

        content_value = st.session_state["funnel_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        expected_funnel = st.selectbox(
            "Expected funnel",
            options=["awareness", "consideration", "decision", "loyalty"],
            index=0,
        )

        submitted = st.form_submit_button("Run Funnel Judge")

    st.session_state["funnel_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "expected_funnel": expected_funnel,
        },
    }

    st.session_state["funnel_payload"] = payload
    st.session_state["funnel_run_requested"] = True


def render_funnel_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the Funnel API response."""
    st.markdown(
        '<div class="section-label">Funnel result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("funnel_payload")

    if not payload:
        st.info("Fill the form and run the Funnel judge to see the response here.")
        return

    should_run = st.session_state.get("funnel_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_funnel_exchange")
        if last_exchange:
            _render_funnel_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["funnel_run_requested"] = False
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
        st.session_state["last_funnel_exchange"] = exchange
        _render_funnel_exchange_summary(exchange)
        st.session_state["funnel_run_requested"] = False
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
        st.session_state["last_funnel_exchange"] = exchange
        _render_funnel_exchange_summary(exchange)
        st.session_state["funnel_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Funnel judge request failed.",
    }
    st.session_state["last_funnel_exchange"] = exchange
    _render_funnel_exchange_summary(exchange)

    st.session_state["funnel_run_requested"] = False

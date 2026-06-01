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
    """Render the preprocessing pipeline step."""
    st.markdown("**Preprocessing**")

    pre_left, pre_middle, pre_right = st.columns(3)
    with pre_left:
        st.metric("Word count", str(preprocessing.get("word_count", "n/a")))
    with pre_middle:
        st.metric("Characters", str(preprocessing.get("char_count", "n/a")))
    with pre_right:
        st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))


def _get_provider_result(
    judge_result: dict[str, object],
    provider_name: str,
) -> dict[str, object]:
    """Return one provider result safely."""
    provider_results = judge_result.get("provider_results")

    if not isinstance(provider_results, dict):
        return {}

    result = provider_results.get(provider_name)

    if not isinstance(result, dict):
        return {}

    return result


def _render_tone_summary(judge_result: dict[str, object]) -> None:
    """Render the final tone result summary."""
    st.markdown("### Tone Result")

    agreement = judge_result.get("agreement")
    if not isinstance(agreement, dict):
        agreement = {}

    col_status, col_score, col_agreement = st.columns(3)

    with col_status:
        st.metric(
            "Final status",
            str(judge_result.get("status", "unknown")).upper(),
        )

    with col_score:
        st.metric(
            "Final score",
            str(judge_result.get("score", "n/a")),
        )

    with col_agreement:
        status_match = agreement.get("status_match")
        agreement_label = "Yes" if status_match is True else "No"
        st.metric("Agreement", agreement_label)

    summary = judge_result.get("summary")
    if summary:
        st.caption(str(summary))


def _render_provider_comparison_table(judge_result: dict[str, object]) -> None:
    """Render OpenAI and Mistral comparison table."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    if not openai_result and not mistral_result:
        return

    st.markdown("### Provider comparison")

    comparison_data = {
        "Metric": [
            "Status",
            "Score",
            "Confidence",
            "Detected tone",
        ],
        "OpenAI": [
            openai_result.get("status", "n/a"),
            openai_result.get("score", "n/a"),
            openai_result.get("confidence", "n/a"),
            openai_result.get("detected_tone", "n/a"),
        ],
        "Mistral": [
            mistral_result.get("status", "n/a"),
            mistral_result.get("score", "n/a"),
            mistral_result.get("confidence", "n/a"),
            mistral_result.get("detected_tone", "n/a"),
        ],
    }

    st.table(comparison_data)


def _render_criterion_comparison_table(judge_result: dict[str, object]) -> None:
    """Render criterion scores comparison table."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    openai_scores = openai_result.get("criterion_scores")
    mistral_scores = mistral_result.get("criterion_scores")

    if not isinstance(openai_scores, dict):
        openai_scores = {}

    if not isinstance(mistral_scores, dict):
        mistral_scores = {}

    criterion_ids = sorted(set(openai_scores.keys()) | set(mistral_scores.keys()))

    if not criterion_ids:
        return

    st.markdown("### Criterion comparison")

    table_data = {
        "Criterion": [],
        "OpenAI": [],
        "Mistral": [],
    }

    for criterion_id in criterion_ids:
        table_data["Criterion"].append(criterion_id)
        table_data["OpenAI"].append(openai_scores.get(criterion_id, "n/a"))
        table_data["Mistral"].append(mistral_scores.get(criterion_id, "n/a"))

    st.table(table_data)


def _render_agreement_details(judge_result: dict[str, object]) -> None:
    """Render detailed agreement information."""
    agreement = judge_result.get("agreement")

    if not isinstance(agreement, dict) or not agreement:
        return

    with st.expander("Show agreement details"):
        st.json(agreement)


def _render_provider_details(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render detailed provider result in a collapsed expander."""
    if not provider_result:
        return

    with st.expander(f"{provider_label} details", expanded=False):
        col_status, col_score, col_confidence = st.columns(3)

        with col_status:
            st.metric("Status", str(provider_result.get("status", "unknown")))
        with col_score:
            st.metric("Score", str(provider_result.get("score", "n/a")))
        with col_confidence:
            st.metric("Confidence", str(provider_result.get("confidence", "n/a")))

        detected_tone = provider_result.get("detected_tone")
        if detected_tone:
            st.caption(f"Detected tone: {detected_tone}")

        summary = provider_result.get("summary")
        if summary:
            st.write(str(summary))

        criterion_scores = provider_result.get("criterion_scores")
        if isinstance(criterion_scores, dict) and criterion_scores:
            st.markdown("**Criterion scores**")
            st.json(criterion_scores)

        st.markdown("**Findings**")
        render_findings_section(provider_result.get("findings", []))

        with st.expander(f"Show raw {provider_label} result"):
            st.json(provider_result)


def _render_provider_details_section(judge_result: dict[str, object]) -> None:
    """Render OpenAI and Mistral detailed results."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    st.markdown("### Provider details")

    _render_provider_details("OpenAI", openai_result)
    _render_provider_details("Mistral", mistral_result)


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render the tone judge result pipeline step."""
    _render_tone_summary(judge_result)
    _render_agreement_details(judge_result)

    _render_provider_comparison_table(judge_result)
    _render_criterion_comparison_table(judge_result)

    st.markdown("### Merged findings")
    render_findings_section(judge_result.get("findings", []))

    applied_rule = judge_result.get("applied_rule")
    if applied_rule:
        with st.expander("Show applied rule"):
            st.json(applied_rule)

    _render_provider_details_section(judge_result)


def _render_tone_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the Tone API response."""
    render_exchange_summary(
        exchange,
        success_message="Tone judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def render_tone_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the tone judge form."""
    st.markdown("### Tone test input")

    if "tone_content_input" not in st.session_state:
        st.session_state["tone_content_input"] = ""

    with st.form("tone_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="tone_content_file_uploader",
        )

        content_value = st.session_state["tone_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        expected_tone = st.text_input(
            "Expected tone",
            value="Didactique",
            placeholder="Didactique, Neutre, Pédagogique...",
        )

        organization_voice = st.text_input(
            "Organization voice",
            value="structurée, équilibrée, accessible",
        )

        organization_voice_description = st.text_area(
            "Organization voice description",
            height=100,
            placeholder="Describe the editorial voice...",
        )

        writing_style = st.text_area(
            "Writing style rules",
            height=120,
            placeholder="Paste writing style rules here...",
        )

        funnel_stage = st.selectbox(
            "Funnel stage",
            options=["Awareness", "Consideration", "Decision", "Loyalty"],
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

        persona = st.text_area(
            "Persona",
            height=120,
            placeholder="Paste persona context here...",
        )

        brief = st.text_area(
            "Brief",
            height=120,
            placeholder="Paste editorial brief here...",
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Tone Judge")

    st.session_state["tone_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "expected_tone": expected_tone.strip(),
            "organization_voice": organization_voice.strip() or None,
            "organization_voice_description": (
                organization_voice_description.strip() or None
            ),
            "writing_style": writing_style.strip() or None,
            "funnel_stage": funnel_stage,
            "persona": persona.strip() or None,
            "content_type": content_type,
            "brief": brief.strip() or None,
            "locale": locale.strip() or None,
        },
    }

    st.session_state["tone_payload"] = payload
    st.session_state["tone_run_requested"] = True


def render_tone_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the Tone API response."""
    st.markdown(
        '<div class="section-label">Tone result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("tone_payload")

    if not payload:
        st.info("Fill the form and run the Tone judge to see the response here.")
        return

    should_run = st.session_state.get("tone_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_tone_exchange")
        if last_exchange:
            _render_tone_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["tone_run_requested"] = False
        return

    context = payload.get("context", {})
    expected_tone = context.get("expected_tone") if isinstance(context, dict) else None

    if not isinstance(expected_tone, str) or not expected_tone.strip():
        st.warning("Please provide the expected tone.")
        st.session_state["tone_run_requested"] = False
        return

    endpoint = f"{api_url.rstrip('/')}{selected_item.endpoint}"

    try:
        response = requests.post(endpoint, json=payload, timeout=90)
    except requests.RequestException as exc:
        exchange = {
            "request_payload": payload,
            "response_status": None,
            "response_body": None,
            "error": f"API request failed: {exc}",
        }
        st.session_state["last_tone_exchange"] = exchange
        _render_tone_exchange_summary(exchange)
        st.session_state["tone_run_requested"] = False
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
        st.session_state["last_tone_exchange"] = exchange
        _render_tone_exchange_summary(exchange)
        st.session_state["tone_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Tone judge request failed.",
    }

    st.session_state["last_tone_exchange"] = exchange
    _render_tone_exchange_summary(exchange)

    st.session_state["tone_run_requested"] = False

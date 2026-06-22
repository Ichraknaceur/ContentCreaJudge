from __future__ import annotations

import json
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
    """Render editorial style preprocessing."""
    st.markdown("**Preprocessing**")

    content_stats = preprocessing.get("content_stats")
    style_stats = preprocessing.get("style_stats")

    if isinstance(content_stats, dict):
        col_1, col_2, col_3, col_4 = st.columns(4)
        with col_1:
            st.metric("Words", str(content_stats.get("word_count", "n/a")))
        with col_2:
            st.metric("Sentences", str(content_stats.get("sentence_count", "n/a")))
        with col_3:
            st.metric("Paragraphs", str(content_stats.get("paragraph_count", "n/a")))
        with col_4:
            st.metric("Is empty", str(content_stats.get("is_empty", "n/a")))

    if isinstance(style_stats, dict):
        missing_fields = style_stats.get("missing_style_fields", [])
        if missing_fields:
            st.warning(
                "Missing style fields: "
                + ", ".join(str(field) for field in missing_fields)
            )


def _get_provider_result(
    judge_result: dict[str, object],
    provider_name: str,
) -> dict[str, object]:
    """Return one provider result safely."""
    providers = judge_result.get("providers")

    if not isinstance(providers, dict):
        return {}

    result = providers.get(provider_name)

    return result if isinstance(result, dict) else {}


def _render_editorial_style_summary(judge_result: dict[str, object]) -> None:
    """Render final editorial style result."""
    st.markdown("### Editorial Style Result")

    col_status, col_score, col_agreement, col_gap = st.columns(4)

    with col_status:
        st.metric("Final status", str(judge_result.get("status", "unknown")).upper())
    with col_score:
        st.metric("Final score", str(judge_result.get("score", "n/a")))
    with col_agreement:
        agreement = judge_result.get("agreement")
        st.metric("Agreement", "Yes" if agreement is True else "No")
    with col_gap:
        st.metric("Score gap", str(judge_result.get("score_gap", "n/a")))

    summary = judge_result.get("summary")
    if summary:
        st.caption(str(summary))


def _render_provider_comparison_table(judge_result: dict[str, object]) -> None:
    """Render OpenAI/Mistral comparison."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    if not openai_result and not mistral_result:
        return


def _render_criteria_scores(judge_result: dict[str, object]) -> None:
    """Render final criteria scores."""
    criteria_scores = judge_result.get("criteria_scores")

    if not isinstance(criteria_scores, dict) or not criteria_scores:
        return

    st.markdown("### Editorial style criterion scores")

    st.table(
        {
            "Criterion": list(criteria_scores.keys()),
            "Final score": list(criteria_scores.values()),
        }
    )


def _render_provider_criteria_comparison(judge_result: dict[str, object]) -> None:
    """Render provider criteria score comparison."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    openai_scores = openai_result.get("criteria_scores")
    mistral_scores = mistral_result.get("criteria_scores")

    if not isinstance(openai_scores, dict):
        openai_scores = {}
    if not isinstance(mistral_scores, dict):
        mistral_scores = {}

    criterion_ids = sorted(set(openai_scores.keys()) | set(mistral_scores.keys()))

    if not criterion_ids:
        return

    st.markdown("### Provider criterion comparison")

    st.table(
        {
            "Criterion": criterion_ids,
            "OpenAI": [
                openai_scores.get(criterion, "n/a") for criterion in criterion_ids
            ],
            "Mistral": [
                mistral_scores.get(criterion, "n/a") for criterion in criterion_ids
            ],
        }
    )


def _render_provider_details(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render provider details."""
    if not provider_result:
        return

    with st.expander(f"{provider_label} details", expanded=False):
        summary = provider_result.get("summary")
        if summary:
            st.write(str(summary))

        criteria_scores = provider_result.get("criteria_scores")
        if isinstance(criteria_scores, dict) and criteria_scores:
            st.markdown("**Criteria scores**")
            st.table(
                {
                    "Criterion": list(criteria_scores.keys()),
                    "Score": list(criteria_scores.values()),
                }
            )

        render_findings_section(provider_result.get("findings", []))

        with st.expander(f"Show raw {provider_label} result"):
            st.json(provider_result)


def _render_provider_details_section(judge_result: dict[str, object]) -> None:
    """Render provider details section."""
    st.markdown("### Provider details")

    _render_provider_details("OpenAI", _get_provider_result(judge_result, "openai"))
    _render_provider_details("Mistral", _get_provider_result(judge_result, "mistral"))


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render editorial style judge result."""
    _render_editorial_style_summary(judge_result)
    _render_provider_comparison_table(judge_result)
    _render_criteria_scores(judge_result)
    _render_provider_criteria_comparison(judge_result)

    render_findings_section(judge_result.get("findings", []))

    applied_rule = judge_result.get("applied_rule")
    if applied_rule:
        with st.expander("Show applied rule"):
            st.json(applied_rule)

    _render_provider_details_section(judge_result)


def _render_editorial_style_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the editorial style API response."""
    render_exchange_summary(
        exchange,
        success_message="Editorial style judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def _extract_editorial_style_from_organization(
    uploaded_file: object,
) -> dict[str, str]:
    """Extract editorial style fields from an organization JSON file."""
    if uploaded_file is None:
        return {}

    try:
        raw_content = uploaded_file.read()
        payload = json.loads(raw_content.decode("utf-8"))
    except AttributeError, UnicodeDecodeError, json.JSONDecodeError:
        return {}

    data = payload.get("data")
    if not isinstance(data, dict):
        return {}

    style_payload = data.get("style")
    if not isinstance(style_payload, dict):
        return {}

    return {
        "writingStyle": str(style_payload.get("writingStyle", "")),
        "writeLikeThis": str(style_payload.get("writeLikeThis", "")),
        "notLikeThis": str(style_payload.get("notLikeThis", "")),
    }


def render_editorial_style_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the editorial style judge form."""
    st.markdown("### Editorial style test input")

    organization_file = st.file_uploader(
        "Upload organization JSON",
        type=["json"],
        key="editorial_style_organization_uploader",
    )

    organization_style = _extract_editorial_style_from_organization(organization_file)

    if "editorial_style_content_input" not in st.session_state:
        st.session_state["editorial_style_content_input"] = ""

    with st.form("editorial_style_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="editorial_style_content_file_uploader",
        )

        content_value = st.session_state["editorial_style_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        writing_style = st.text_area(
            "Writing style rules",
            height=180,
            value=organization_style.get("writingStyle", ""),
            placeholder="Paste writingStyle here...",
        )

        write_like_this = st.text_area(
            "Write like this",
            height=140,
            value=organization_style.get("writeLikeThis", ""),
            placeholder="Paste compliant example here...",
        )

        not_like_this = st.text_area(
            "Do not write like this",
            height=140,
            value=organization_style.get("notLikeThis", ""),
            placeholder="Paste non-compliant example here...",
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

        funnel_stage = st.selectbox(
            "Funnel stage",
            options=["Awareness", "Consideration", "Decision", "Loyalty"],
            index=0,
        )

        organization_name = st.text_input(
            "Organization name",
            value="",
            placeholder="ContentCrea, LIRIS...",
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Editorial Style Judge")

    st.session_state["editorial_style_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "editorial_style": {
            "writingStyle": writing_style.strip(),
            "writeLikeThis": write_like_this.strip(),
            "notLikeThis": not_like_this.strip(),
        },
        "context": {
            "content_type": content_type,
            "funnel_stage": funnel_stage,
            "organization_name": organization_name.strip() or None,
            "locale": locale.strip() or None,
        },
    }

    st.session_state["editorial_style_payload"] = payload
    st.session_state["editorial_style_run_requested"] = True


def render_editorial_style_result(
    api_url: str,
    selected_item: JudgeWorkbenchItem,
) -> None:
    """Read the payload and display the editorial style API response."""
    st.markdown(
        '<div class="section-label">Editorial style result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("editorial_style_payload")

    if not payload:
        st.info(
            "Fill the form and run the Editorial Style judge to see the response here."
        )
        return

    should_run = st.session_state.get("editorial_style_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_editorial_style_exchange")
        if last_exchange:
            _render_editorial_style_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["editorial_style_run_requested"] = False
        return

    editorial_style = payload.get("editorial_style", {})
    if not isinstance(editorial_style, dict):
        editorial_style = {}

    if not any(
        str(editorial_style.get(field, "")).strip()
        for field in [
            "writingStyle",
            "writeLikeThis",
            "notLikeThis",
        ]
    ):
        st.warning("Please provide at least one editorial style field.")
        st.session_state["editorial_style_run_requested"] = False
        return

    endpoint = f"{api_url.rstrip('/')}{selected_item.endpoint}"

    try:
        response = requests.post(endpoint, json=payload, timeout=120)
    except requests.RequestException as exc:
        exchange = {
            "request_payload": payload,
            "response_status": None,
            "response_body": None,
            "error": f"API request failed: {exc}",
        }
        st.session_state["last_editorial_style_exchange"] = exchange
        _render_editorial_style_exchange_summary(exchange)
        st.session_state["editorial_style_run_requested"] = False
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
        st.session_state["last_editorial_style_exchange"] = exchange
        _render_editorial_style_exchange_summary(exchange)
        st.session_state["editorial_style_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Editorial Style judge request failed.",
    }

    st.session_state["last_editorial_style_exchange"] = exchange
    _render_editorial_style_exchange_summary(exchange)

    st.session_state["editorial_style_run_requested"] = False

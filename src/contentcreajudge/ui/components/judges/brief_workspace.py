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
        st.metric(
            "Article words",
            str(preprocessing.get("article_word_count", "n/a")),
        )

    with pre_middle:
        st.metric(
            "Brief words",
            str(preprocessing.get("brief_word_count", "n/a")),
        )

    with pre_right:
        st.metric(
            "Article empty",
            str(preprocessing.get("is_article_empty", "n/a")),
        )

    if preprocessing.get("is_brief_empty") is True:
        st.warning("The brief is empty.")


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


def _render_brief_summary(judge_result: dict[str, object]) -> None:
    """Render the final Brief result summary."""
    st.markdown("### Brief Result")

    agreement = judge_result.get("agreement")
    if not isinstance(agreement, dict):
        agreement = {}

    col_status, col_score, col_confidence, col_agreement = st.columns(4)

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

    with col_confidence:
        st.metric(
            "Confidence",
            str(judge_result.get("confidence", "n/a")),
        )

    with col_agreement:
        status_match = agreement.get("status_match")
        agreement_label = "Yes" if status_match is True else "No"
        st.metric("Agreement", agreement_label)

    summary = judge_result.get("summary")
    if summary:
        st.caption(str(summary))


def _render_agreement_details(judge_result: dict[str, object]) -> None:
    """Render detailed agreement information."""
    agreement = judge_result.get("agreement")

    if not isinstance(agreement, dict) or not agreement:
        return

    with st.expander("Show agreement details"):
        st.json(agreement)


def _render_provider_comparison_table(judge_result: dict[str, object]) -> None:
    """Render OpenAI and Mistral comparison table."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    if not openai_result and not mistral_result:
        return

    st.markdown("### Provider comparison")

    comparison_data = {
        "Metric": [
            "Backend status",
            "Backend score",
            "Confidence",
        ],
        "OpenAI": [
            openai_result.get("status", "n/a"),
            openai_result.get("score", "n/a"),
            openai_result.get("confidence", "n/a"),
        ],
        "Mistral": [
            mistral_result.get("status", "n/a"),
            mistral_result.get("score", "n/a"),
            mistral_result.get("confidence", "n/a"),
        ],
    }

    st.table(comparison_data)


def _get_evaluation_block(provider_result: dict[str, object]) -> dict[str, object]:
    """Return the provider evaluation block safely."""
    evaluation = provider_result.get("evaluation")

    if not isinstance(evaluation, dict):
        return {}

    return evaluation


def _get_criterion_score(
    provider_result: dict[str, object],
    criterion_id: str,
) -> object:
    """Return one criterion score safely."""
    evaluation = _get_evaluation_block(provider_result)
    criterion_result = evaluation.get(criterion_id)

    if not isinstance(criterion_result, dict):
        return "n/a"

    if (
        criterion_id == "specific_element_integration"
        and criterion_result.get("applicable") is False
    ):
        return "not applicable"

    return criterion_result.get("score", "n/a")


def _get_criterion_confidence(
    provider_result: dict[str, object],
    criterion_id: str,
) -> object:
    """Return one criterion confidence safely."""
    evaluation = _get_evaluation_block(provider_result)
    criterion_result = evaluation.get(criterion_id)

    if not isinstance(criterion_result, dict):
        return "n/a"

    if (
        criterion_id == "specific_element_integration"
        and criterion_result.get("applicable") is False
    ):
        return "not applicable"

    return criterion_result.get("confidence", "n/a")


def _render_criterion_score_table(judge_result: dict[str, object]) -> None:
    """Render criterion score comparison table."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    if not openai_result and not mistral_result:
        return

    st.markdown("### Brief criterion scores")

    criterion_ids = [
        "angle_alignment",
        "axis_development",
        "intended_understanding",
        "scope_adherence",
        "specific_element_integration",
    ]

    table_data = {
        "Criterion": [],
        "OpenAI score": [],
        "Mistral score": [],
        "OpenAI confidence": [],
        "Mistral confidence": [],
    }

    for criterion_id in criterion_ids:
        table_data["Criterion"].append(criterion_id)
        table_data["OpenAI score"].append(
            _get_criterion_score(openai_result, criterion_id)
        )
        table_data["Mistral score"].append(
            _get_criterion_score(mistral_result, criterion_id)
        )
        table_data["OpenAI confidence"].append(
            _get_criterion_confidence(openai_result, criterion_id)
        )
        table_data["Mistral confidence"].append(
            _get_criterion_confidence(mistral_result, criterion_id)
        )

    st.table(table_data)


def _render_brief_decomposition(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render brief decomposition returned by one provider."""
    brief_decomposition = provider_result.get("brief_decomposition")

    if not isinstance(brief_decomposition, dict) or not brief_decomposition:
        return

    st.markdown(f"**{provider_label} brief decomposition**")

    for key, value in brief_decomposition.items():
        st.markdown(f"- **{key}**: {value}")


def _render_distinctive_elements_review(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render distinctive elements review returned by one provider."""
    review = provider_result.get("distinctive_elements_review")

    if not isinstance(review, dict):
        return

    elements = review.get("elements")

    if not isinstance(elements, list) or not elements:
        return

    st.markdown(f"**{provider_label} distinctive elements review**")

    table_data = {
        "Element": [],
        "Presence": [],
        "Evidence": [],
        "Impact on score": [],
    }

    for item in elements:
        if not isinstance(item, dict):
            continue

        table_data["Element"].append(item.get("element", "n/a"))
        table_data["Presence"].append(item.get("presence_in_article", "n/a"))
        table_data["Evidence"].append(item.get("evidence", "n/a"))
        table_data["Impact on score"].append(item.get("impact_on_score", "n/a"))

    st.table(table_data)


def _render_criterion_details(provider_result: dict[str, object]) -> None:
    """Render detailed criterion evaluation for one provider."""
    evaluation = _get_evaluation_block(provider_result)

    if not evaluation:
        return

    st.markdown("**Criterion details**")

    for criterion_id, criterion_result in evaluation.items():
        if not isinstance(criterion_result, dict):
            continue

        with st.expander(str(criterion_id), expanded=False):
            if criterion_id == "specific_element_integration":
                st.caption(f"Applicable: {criterion_result.get('applicable', 'n/a')}")

            st.metric("Score", str(criterion_result.get("score", "n/a")))
            st.metric("Confidence", str(criterion_result.get("confidence", "n/a")))

            justification = criterion_result.get("justification")
            if justification:
                st.write(str(justification))

            evidence = criterion_result.get("evidence")
            if isinstance(evidence, list) and evidence:
                st.markdown("Evidence")
                for item in evidence:
                    st.markdown(f"- {item}")


def _render_provider_details(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render detailed provider result in a collapsed expander."""
    if not provider_result:
        return

    with st.expander(f"{provider_label} details", expanded=False):
        st.metric(
            "Status",
            str(provider_result.get("status", "unknown")).upper(),
        )
        st.metric(
            "Score",
            str(provider_result.get("score", "n/a")),
        )
        st.metric(
            "Confidence",
            str(provider_result.get("confidence", "n/a")),
        )

        summary = provider_result.get("summary")
        if summary:
            st.write(str(summary))

        _render_brief_decomposition(provider_label, provider_result)
        _render_distinctive_elements_review(provider_label, provider_result)
        _render_criterion_details(provider_result)
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
    """Render the Brief judge result pipeline step."""
    _render_brief_summary(judge_result)
    _render_agreement_details(judge_result)
    _render_provider_comparison_table(judge_result)
    _render_criterion_score_table(judge_result)

    applied_rule = judge_result.get("applied_rule")
    if applied_rule:
        with st.expander("Show applied rule"):
            st.json(applied_rule)

    _render_provider_details_section(judge_result)


def _render_brief_exchange_summary(exchange: dict[str, object]) -> None:
    """Render the Brief API response."""
    render_exchange_summary(
        exchange,
        success_message="Brief judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def render_brief_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the Brief judge form."""
    st.markdown("### Brief test input")

    if "brief_content_input" not in st.session_state:
        st.session_state["brief_content_input"] = ""

    if "brief_input" not in st.session_state:
        st.session_state["brief_input"] = ""

    with st.form("brief_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="brief_content_file_uploader",
        )

        content_value = st.session_state["brief_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        uploaded_brief_file = st.file_uploader(
            "Upload brief file",
            type=["txt", "md"],
            key="brief_file_uploader",
        )

        brief_value = st.session_state["brief_input"]
        if uploaded_brief_file is not None:
            brief_value = read_uploaded_text_file(uploaded_brief_file)

        brief = st.text_area(
            "Editorial brief",
            height=220,
            placeholder="Paste the editorial brief here...",
            value=brief_value,
        )

        submitted = st.form_submit_button("Run Brief Judge")

    st.session_state["brief_content_input"] = content
    st.session_state["brief_input"] = brief

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "brief": brief.strip(),
        },
    }

    st.session_state["brief_payload"] = payload
    st.session_state["brief_run_requested"] = True


def render_brief_result(api_url: str, selected_item: JudgeWorkbenchItem) -> None:
    """Read the payload and display the Brief API response."""
    st.markdown(
        '<div class="section-label">Brief result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("brief_payload")

    if not payload:
        st.info("Fill the form and run the Brief judge to see the response here.")
        return

    should_run = st.session_state.get("brief_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_brief_exchange")
        if last_exchange:
            _render_brief_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["brief_run_requested"] = False
        return

    context = payload.get("context", {})
    brief = context.get("brief") if isinstance(context, dict) else None

    if not isinstance(brief, str) or not brief.strip():
        st.warning("Please provide the editorial brief.")
        st.session_state["brief_run_requested"] = False
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
        st.session_state["last_brief_exchange"] = exchange
        _render_brief_exchange_summary(exchange)
        st.session_state["brief_run_requested"] = False
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
        st.session_state["last_brief_exchange"] = exchange
        _render_brief_exchange_summary(exchange)
        st.session_state["brief_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Brief judge request failed.",
    }

    st.session_state["last_brief_exchange"] = exchange
    _render_brief_exchange_summary(exchange)

    st.session_state["brief_run_requested"] = False

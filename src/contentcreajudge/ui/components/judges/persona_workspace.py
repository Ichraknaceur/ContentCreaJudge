from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import requests
import streamlit as st

from contentcreajudge.ui.components.judges.shared import (
    read_uploaded_text_file,
    render_exchange_summary,
    render_findings_section,
)

if TYPE_CHECKING:
    from contentcreajudge.ui.viewmodels.judge_playground_vm import JudgeWorkbenchItem


def _extract_persona_id(persona: dict[str, Any]) -> str:
    """Extract persona id from platform persona format."""
    persona_id = persona.get("persona_id") or persona.get("uuid")

    if persona_id:
        return str(persona_id)

    data = persona.get("data")
    if isinstance(data, dict):
        nested_id = data.get("persona_id") or data.get("uuid")
        if nested_id:
            return str(nested_id)

    return "unknown"


def _extract_persona_label(persona: dict[str, Any]) -> str:
    """Build a readable persona label."""
    persona_id = _extract_persona_id(persona)

    data = persona.get("data")
    if not isinstance(data, dict):
        data = {}

    first_name = data.get("firstName") or persona.get("first_name") or ""
    function = data.get("function") or persona.get("function") or "Unknown function"

    label = f"{function} — {persona_id}"

    if first_name:
        label = f"{first_name} | {label}"

    return label


def _extract_persona_identity(persona: dict[str, Any]) -> dict[str, str]:
    """Extract readable identity from a persona."""
    data = persona.get("data")
    if not isinstance(data, dict):
        data = {}

    return {
        "first_name": str(data.get("firstName") or persona.get("first_name") or ""),
        "function": str(data.get("function") or persona.get("function") or ""),
    }


def _build_persona_lookup(
    personas: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    """Build persona lookup by id for UI display."""
    return {
        _extract_persona_id(persona): _extract_persona_identity(persona)
        for persona in personas
    }


def _persona_display_name(
    persona_id: object,
    persona_lookup: dict[str, dict[str, str]],
) -> str:
    """Return a readable persona name from an id."""
    persona_id_str = str(persona_id or "")
    persona = persona_lookup.get(persona_id_str)

    if not persona:
        return persona_id_str or "n/a"

    first_name = persona.get("first_name", "")
    function = persona.get("function", "")

    if first_name and function:
        return f"{first_name} ({function})"

    if first_name:
        return first_name

    if function:
        return function

    return persona_id_str or "n/a"


def _parse_uploaded_personas(uploaded_persona_files: list[Any]) -> list[dict[str, Any]]:
    """Read and parse uploaded persona JSON files."""
    personas: list[dict[str, Any]] = []

    for uploaded_file in uploaded_persona_files:
        raw_content = read_uploaded_text_file(uploaded_file)

        try:
            parsed_content = json.loads(raw_content)
        except json.JSONDecodeError:
            st.warning(f"Invalid JSON ignored: {uploaded_file.name}")
            continue

        if isinstance(parsed_content, list):
            personas.extend(
                persona for persona in parsed_content if isinstance(persona, dict)
            )
        elif isinstance(parsed_content, dict):
            personas.append(parsed_content)

    return personas


def _get_provider_result(
    judge_result: dict[str, object],
    provider_name: str,
) -> dict[str, object]:
    """Return one provider result safely."""
    provider_results = judge_result.get("provider_results")

    if isinstance(provider_results, list):
        for result in provider_results:
            if not isinstance(result, dict):
                continue

            result_provider = str(result.get("provider", "")).lower()
            if result_provider == provider_name:
                return result

    if isinstance(provider_results, dict):
        result = provider_results.get(provider_name)
        if isinstance(result, dict):
            return result

    return {}


def _render_preprocessing_section(preprocessing: dict[str, object]) -> None:
    """Render preprocessing summary."""
    st.markdown("**Preprocessing**")

    persona_lookup = st.session_state.get("persona_lookup", {})
    if not isinstance(persona_lookup, dict):
        persona_lookup = {}

    personas = preprocessing.get("personas", [])
    personas_count = len(personas) if isinstance(personas, list) else 0
    normalized_text = str(preprocessing.get("normalized_text", ""))

    col_empty, col_chars, col_personas = st.columns(3)

    with col_empty:
        st.metric("Is empty", str(preprocessing.get("is_empty", "n/a")))

    with col_chars:
        st.metric("Characters", str(len(normalized_text)))

    with col_personas:
        st.metric("Personas", str(personas_count))

    expected_persona_id = preprocessing.get("expected_persona_id")
    if expected_persona_id:
        expected_label = _persona_display_name(expected_persona_id, persona_lookup)
        st.caption(f"Expected persona: `{expected_label}`")


def _render_persona_summary(judge_result: dict[str, object]) -> None:
    """Render final persona summary."""
    st.markdown("### Persona Result")

    agreement = judge_result.get("agreement")
    if not isinstance(agreement, dict):
        agreement = {}

    col_status, col_score, col_gap = st.columns(3)

    with col_status:
        st.metric("Final status", str(judge_result.get("status", "unknown")).upper())

    with col_score:
        st.metric("Final score", str(judge_result.get("score", "n/a")))

    with col_gap:
        st.metric("Score gap", str(agreement.get("score_gap", "n/a")))

    detected_agreement = agreement.get("detected_persona_agreement")
    status_agreement = agreement.get("status_agreement")

    st.caption(
        f"Status agreement: {'Yes' if status_agreement else 'No'} · "
        f"Detected persona agreement: {'Yes' if detected_agreement else 'No'}"
    )


def _render_provider_comparison_table(judge_result: dict[str, object]) -> None:
    """Render provider comparison."""
    persona_lookup = st.session_state.get("persona_lookup", {})
    if not isinstance(persona_lookup, dict):
        persona_lookup = {}

    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    if not openai_result and not mistral_result:
        return

    st.markdown("### Provider comparison")

    comparison_data = {
        "Metric": [
            "Status",
            "Score",
            "Expected persona",
            "Detected persona",
            "Persona match",
        ],
        "OpenAI": [
            openai_result.get("status", "n/a"),
            openai_result.get("score", "n/a"),
            _persona_display_name(
                openai_result.get("expected_persona_id"),
                persona_lookup,
            ),
            _persona_display_name(
                openai_result.get("detected_persona_id"),
                persona_lookup,
            ),
            openai_result.get("persona_match", "n/a"),
        ],
        "Mistral": [
            mistral_result.get("status", "n/a"),
            mistral_result.get("score", "n/a"),
            _persona_display_name(
                mistral_result.get("expected_persona_id"),
                persona_lookup,
            ),
            _persona_display_name(
                mistral_result.get("detected_persona_id"),
                persona_lookup,
            ),
            mistral_result.get("persona_match", "n/a"),
        ],
    }

    st.table(comparison_data)


def _render_distribution_table(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render persona distribution for one provider."""
    persona_lookup = st.session_state.get("persona_lookup", {})
    if not isinstance(persona_lookup, dict):
        persona_lookup = {}

    distribution = provider_result.get("persona_distribution")

    if not isinstance(distribution, list) or not distribution:
        return

    st.markdown(f"#### {provider_label} persona distribution")

    table_data = {
        "Persona": [],
        "Score": [],
        "Reason": [],
    }

    for item in distribution:
        if not isinstance(item, dict):
            continue

        table_data["Persona"].append(
            _persona_display_name(item.get("persona_id"), persona_lookup)
        )
        table_data["Score"].append(item.get("score", "n/a"))
        table_data["Reason"].append(item.get("reason", ""))

    st.table(table_data)


def _render_distributions(judge_result: dict[str, object]) -> None:
    """Render OpenAI and Mistral distributions."""
    st.markdown("### Persona distribution")

    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    _render_distribution_table("OpenAI", openai_result)
    _render_distribution_table("Mistral", mistral_result)


def _get_evaluation(
    provider_result: dict[str, object],
    evaluation_key: str,
) -> dict[str, object]:
    """Return detected or expected evaluation safely."""
    evaluation = provider_result.get(evaluation_key)

    if isinstance(evaluation, dict):
        return evaluation

    return {}


def _render_evaluation_comparison_table(judge_result: dict[str, object]) -> None:
    """Render detected vs expected persona evaluations."""
    persona_lookup = st.session_state.get("persona_lookup", {})
    if not isinstance(persona_lookup, dict):
        persona_lookup = {}

    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    openai_detected = _get_evaluation(openai_result, "detected_persona_evaluation")
    openai_expected = _get_evaluation(openai_result, "expected_persona_evaluation")

    mistral_detected = _get_evaluation(mistral_result, "detected_persona_evaluation")
    mistral_expected = _get_evaluation(mistral_result, "expected_persona_evaluation")

    st.markdown("### Detected vs expected evaluation")

    comparison_data = {
        "Metric": [
            "Detected persona",
            "Detected score",
            "Expected persona",
            "Expected score",
        ],
        "OpenAI": [
            _persona_display_name(openai_detected.get("persona_id"), persona_lookup),
            openai_detected.get("score", "n/a"),
            _persona_display_name(openai_expected.get("persona_id"), persona_lookup),
            openai_expected.get("score", "n/a"),
        ],
        "Mistral": [
            _persona_display_name(mistral_detected.get("persona_id"), persona_lookup),
            mistral_detected.get("score", "n/a"),
            _persona_display_name(mistral_expected.get("persona_id"), persona_lookup),
            mistral_expected.get("score", "n/a"),
        ],
    }

    st.table(comparison_data)


def _render_criterion_scores_table(
    title: str,
    openai_evaluation: dict[str, object],
    mistral_evaluation: dict[str, object],
) -> None:
    """Render criterion scores comparison table for one evaluation type."""
    openai_scores = openai_evaluation.get("criteria_scores")
    mistral_scores = mistral_evaluation.get("criteria_scores")

    if not isinstance(openai_scores, dict):
        openai_scores = {}

    if not isinstance(mistral_scores, dict):
        mistral_scores = {}

    criterion_ids = sorted(set(openai_scores.keys()) | set(mistral_scores.keys()))

    if not criterion_ids:
        return

    st.markdown(f"**{title}**")

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


def _render_criterion_comparison_table(judge_result: dict[str, object]) -> None:
    """Render detected and expected persona criterion scores."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    openai_detected = _get_evaluation(openai_result, "detected_persona_evaluation")
    mistral_detected = _get_evaluation(mistral_result, "detected_persona_evaluation")

    openai_expected = _get_evaluation(openai_result, "expected_persona_evaluation")
    mistral_expected = _get_evaluation(mistral_result, "expected_persona_evaluation")

    with st.expander("Detected persona criterion comparison", expanded=False):
        _render_criterion_scores_table(
            "Detected persona criterion comparison",
            openai_detected,
            mistral_detected,
        )

    with st.expander("Expected persona criterion comparison", expanded=True):
        _render_criterion_scores_table(
            "Expected persona criterion comparison",
            openai_expected,
            mistral_expected,
        )


def _render_agreement_details(judge_result: dict[str, object]) -> None:
    """Render agreement details."""
    agreement = judge_result.get("agreement")

    if not isinstance(agreement, dict) or not agreement:
        return

    with st.expander("Show agreement details"):
        st.json(agreement)


def _render_evaluation_details(
    title: str,
    evaluation: dict[str, object],
) -> None:
    """Render one evaluation details block."""
    if not evaluation:
        return

    st.markdown(f"**{title}**")
    st.metric("Score", str(evaluation.get("score", "n/a")))

    summary = evaluation.get("summary")
    if summary:
        st.write(str(summary))

    criteria_scores = evaluation.get("criteria_scores")
    if isinstance(criteria_scores, dict) and criteria_scores:
        st.markdown("Criterion scores")
        st.json(criteria_scores)

    identified_elements = evaluation.get("identified_persona_elements")
    if isinstance(identified_elements, dict) and identified_elements:
        st.markdown("Identified persona elements")
        st.json(identified_elements)


def _render_provider_details(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render detailed provider result."""
    if not provider_result:
        return

    with st.expander(f"{provider_label} details", expanded=False):
        col_status, col_score, col_match = st.columns(3)

        with col_status:
            st.metric("Status", str(provider_result.get("status", "unknown")))

        with col_score:
            st.metric("Score", str(provider_result.get("score", "n/a")))

        with col_match:
            st.metric("Persona match", str(provider_result.get("persona_match", "n/a")))

        persona_lookup = st.session_state.get("persona_lookup", {})
        if not isinstance(persona_lookup, dict):
            persona_lookup = {}

        expected_label = _persona_display_name(
            provider_result.get("expected_persona_id"),
            persona_lookup,
        )
        detected_label = _persona_display_name(
            provider_result.get("detected_persona_id"),
            persona_lookup,
        )

        st.caption(f"Expected: `{expected_label}`")
        st.caption(f"Detected: `{detected_label}`")

        with st.expander("Show technical persona ids"):
            st.json(
                {
                    "expected_persona_id": provider_result.get("expected_persona_id"),
                    "detected_persona_id": provider_result.get("detected_persona_id"),
                }
            )

        summary = provider_result.get("summary")
        if summary:
            st.write(str(summary))

        _render_distribution_table(provider_label, provider_result)

        _render_evaluation_details(
            "Detected persona evaluation",
            _get_evaluation(provider_result, "detected_persona_evaluation"),
        )

        _render_evaluation_details(
            "Expected persona evaluation",
            _get_evaluation(provider_result, "expected_persona_evaluation"),
        )

        st.markdown("**Findings**")
        render_findings_section(provider_result.get("findings", []))

        with st.expander(f"Show raw {provider_label} result"):
            st.json(provider_result)


def _render_provider_details_section(judge_result: dict[str, object]) -> None:
    """Render provider details."""
    st.markdown("### Provider details")

    _render_provider_details(
        "OpenAI",
        _get_provider_result(judge_result, "openai"),
    )
    _render_provider_details(
        "Mistral",
        _get_provider_result(judge_result, "mistral"),
    )


def _render_provider_findings_section(judge_result: dict[str, object]) -> None:
    """Render OpenAI and Mistral findings separately."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    st.markdown("### Provider findings")

    with st.expander("OpenAI findings", expanded=True):
        render_findings_section(openai_result.get("findings", []))

    with st.expander("Mistral findings", expanded=True):
        render_findings_section(mistral_result.get("findings", []))

    with st.expander("Show merged findings"):
        render_findings_section(judge_result.get("findings", []))


def _render_judge_result_section(judge_result: dict[str, object]) -> None:
    """Render persona judge result."""
    _render_persona_summary(judge_result)
    _render_agreement_details(judge_result)
    _render_provider_comparison_table(judge_result)
    _render_distributions(judge_result)
    _render_evaluation_comparison_table(judge_result)
    _render_criterion_comparison_table(judge_result)
    _render_provider_findings_section(judge_result)

    applied_rule = judge_result.get("applied_rule")
    if applied_rule:
        with st.expander("Show applied rule"):
            st.json(applied_rule)

    _render_provider_details_section(judge_result)


def _render_persona_exchange_summary(exchange: dict[str, object]) -> None:
    """Render Persona API response."""
    render_exchange_summary(
        exchange,
        success_message="Persona judge executed successfully.",
        render_preprocessing=_render_preprocessing_section,
        render_judge_result=_render_judge_result_section,
    )


def render_persona_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render persona judge form."""
    st.markdown("### Persona test input")

    if "persona_content_input" not in st.session_state:
        st.session_state["persona_content_input"] = ""

    st.markdown("**Organization personas**")

    uploaded_persona_files = st.file_uploader(
        "Upload persona JSON files",
        type=["json", "txt"],
        accept_multiple_files=True,
        key="persona_files_uploader",
    )

    personas = _parse_uploaded_personas(uploaded_persona_files or [])
    st.session_state["persona_lookup"] = _build_persona_lookup(personas)

    if personas:
        st.caption(f"{len(personas)} persona file(s) loaded.")

    persona_options = {
        _extract_persona_label(persona): _extract_persona_id(persona)
        for persona in personas
    }

    selected_persona_label = None
    if persona_options:
        selected_persona_label = st.selectbox(
            "Expected persona",
            options=list(persona_options.keys()),
            index=0,
            key="persona_expected_selectbox",
        )

    expected_persona_id = ""

    if selected_persona_label:
        expected_persona_id = persona_options.get(selected_persona_label, "")
        st.caption(f"Expected persona id: `{expected_persona_id}`")
    else:
        expected_persona_id = st.text_input(
            "Expected persona id",
            value="",
            placeholder="Paste expected persona uuid if no file is selected",
            key="persona_expected_id_input",
        )

    with st.form("persona_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="persona_content_file_uploader",
        )

        content_value = st.session_state["persona_content_input"]
        if uploaded_content_file is not None:
            content_value = read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        st.markdown("**Content context**")

        business_type = st.selectbox(
            "Business type",
            options=["B2B", "B2C", "B2B2C"],
            index=0,
        )

        funnel_stage = st.selectbox(
            "Funnel stage",
            options=["AWARENESS", "CONSIDERATION", "DECISION", "LOYALTY"],
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

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Persona Judge")

    st.session_state["persona_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "personas": personas,
            "expected_persona_id": expected_persona_id.strip(),
            "business_type": business_type,
            "content_type": content_type,
            "funnel_stage": funnel_stage,
            "locale": locale.strip() or None,
        },
    }

    st.session_state["persona_payload"] = payload
    st.session_state["persona_run_requested"] = True


def render_persona_result(  # noqa: C901, PLR0911
    api_url: str,
    selected_item: JudgeWorkbenchItem,
) -> None:
    """Read the payload and display Persona API response."""
    st.markdown(
        '<div class="section-label">Persona result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("persona_payload")

    if not payload:
        st.info("Fill the form and run the Persona judge to see the response here.")
        return

    should_run = st.session_state.get("persona_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_persona_exchange")
        if last_exchange:
            _render_persona_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    if not isinstance(content, str) or not content.strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["persona_run_requested"] = False
        return

    context = payload.get("context", {})
    if not isinstance(context, dict):
        st.warning("Please provide a valid context.")
        st.session_state["persona_run_requested"] = False
        return

    personas = context.get("personas")
    if not isinstance(personas, list) or not personas:
        st.warning("Please upload at least one persona JSON file.")
        st.session_state["persona_run_requested"] = False
        return

    expected_persona_id = context.get("expected_persona_id")
    if not isinstance(expected_persona_id, str) or not expected_persona_id.strip():
        st.warning("Please provide the expected persona id.")
        st.session_state["persona_run_requested"] = False
        return

    business_type = context.get("business_type")
    if not isinstance(business_type, str) or not business_type.strip():
        st.warning("Please provide the business type.")
        st.session_state["persona_run_requested"] = False
        return

    endpoint = f"{api_url.rstrip('/')}{selected_item.endpoint}"

    try:
        response = requests.post(endpoint, json=payload, timeout=180)
    except requests.RequestException as exc:
        exchange = {
            "request_payload": payload,
            "response_status": None,
            "response_body": None,
            "error": f"API request failed: {exc}",
        }
        st.session_state["last_persona_exchange"] = exchange
        _render_persona_exchange_summary(exchange)
        st.session_state["persona_run_requested"] = False
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
        st.session_state["last_persona_exchange"] = exchange
        _render_persona_exchange_summary(exchange)
        st.session_state["persona_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Persona judge request failed.",
    }

    st.session_state["last_persona_exchange"] = exchange
    _render_persona_exchange_summary(exchange)
    st.session_state["persona_run_requested"] = False

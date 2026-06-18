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


def _get_perceived_tone(provider_result: dict[str, object]) -> str:
    """Return perceived tone from blind observation."""
    blind_observation = provider_result.get("blind_observation")

    if not isinstance(blind_observation, dict):
        return "n/a"

    perceived_tone = blind_observation.get("perceived_tone")

    return str(perceived_tone) if perceived_tone else "n/a"


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
            "Backend status",
            "Backend score",
            "Confidence",
            "Perceived tone",
        ],
        "OpenAI": [
            openai_result.get("status", "n/a"),
            openai_result.get("score", "n/a"),
            openai_result.get("confidence", "n/a"),
            _get_perceived_tone(openai_result),
        ],
        "Mistral": [
            mistral_result.get("status", "n/a"),
            mistral_result.get("score", "n/a"),
            mistral_result.get("confidence", "n/a"),
            _get_perceived_tone(mistral_result),
        ],
    }

    st.table(comparison_data)


def _get_criterion_score_block(
    provider_result: dict[str, object],
    block_name: str,
) -> dict[str, object]:
    """Return one criterion score block safely."""
    criterion_scores = provider_result.get("criterion_scores")

    if not isinstance(criterion_scores, dict):
        return {}

    score_block = criterion_scores.get(block_name)

    if not isinstance(score_block, dict):
        return {}

    return score_block


def _render_criterion_score_table(
    *,
    title: str,
    openai_scores: dict[str, object],
    mistral_scores: dict[str, object],
) -> None:
    """Render one criterion score comparison table."""
    criterion_ids = sorted(set(openai_scores.keys()) | set(mistral_scores.keys()))

    if not criterion_ids:
        return

    st.markdown(title)

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


def _render_detected_tone_criterion_table(judge_result: dict[str, object]) -> None:
    """Render detected tone criterion scores comparison table."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    _render_criterion_score_table(
        title="### Detected tone criterion",
        openai_scores=_get_criterion_score_block(openai_result, "detected_tone"),
        mistral_scores=_get_criterion_score_block(mistral_result, "detected_tone"),
    )


def _render_expected_tone_criterion_table(judge_result: dict[str, object]) -> None:
    """Render expected tone criterion scores comparison table."""
    openai_result = _get_provider_result(judge_result, "openai")
    mistral_result = _get_provider_result(judge_result, "mistral")

    _render_criterion_score_table(
        title="### Expected tone criterion",
        openai_scores=_get_criterion_score_block(openai_result, "expected_tone"),
        mistral_scores=_get_criterion_score_block(mistral_result, "expected_tone"),
    )


def _render_agreement_details(judge_result: dict[str, object]) -> None:
    """Render detailed agreement information."""
    agreement = judge_result.get("agreement")

    if not isinstance(agreement, dict) or not agreement:
        return

    with st.expander("Show agreement details"):
        st.json(agreement)


def _render_blind_observation(provider_result: dict[str, object]) -> None:
    """Render blind tone observation."""
    blind_observation = provider_result.get("blind_observation")

    if not isinstance(blind_observation, dict) or not blind_observation:
        return

    st.markdown("**Blind observation**")

    perceived_tone = blind_observation.get("perceived_tone")
    if perceived_tone:
        st.caption(f"Perceived tone: {perceived_tone}")

    lexical_evidence = blind_observation.get("lexical_evidence")
    if isinstance(lexical_evidence, list) and lexical_evidence:
        st.markdown("Lexical evidence")
        for evidence in lexical_evidence:
            st.markdown(f"- {evidence}")

    tone_presence = blind_observation.get("tone_presence")
    if isinstance(tone_presence, dict) and tone_presence:
        st.markdown("Tone presence")
        st.table(
            {
                "Tone": list(tone_presence.keys()),
                "Presence (%)": list(tone_presence.values()),
            }
        )


def _render_tone_distribution(provider_result: dict[str, object]) -> None:
    """Render tone distribution."""
    ton_distribution = provider_result.get("ton_distribution")

    if not isinstance(ton_distribution, list) or not ton_distribution:
        return

    st.markdown("**Tone distribution**")

    for distribution_entry in ton_distribution:
        if not isinstance(distribution_entry, dict):
            continue

        source_tone = distribution_entry.get("source_tone", "unknown")
        source_score = distribution_entry.get("source_score", "n/a")
        in_org_list = distribution_entry.get("in_org_list", False)
        sum_check = distribution_entry.get("sum_check", "n/a")

        st.caption(
            f"Source tone: {source_tone} | "
            f"Source score: {source_score} | "
            f"In organization tones: {in_org_list} | "
            f"Sum check: {sum_check}"
        )

        distribution = distribution_entry.get("distribution")
        if isinstance(distribution, list) and distribution:
            table_data = {
                "Tone": [],
                "Score": [],
                "Justification": [],
            }

            for item in distribution:
                if not isinstance(item, dict):
                    continue

                table_data["Tone"].append(item.get("tone", "n/a"))
                table_data["Score"].append(item.get("score", "n/a"))
                table_data["Justification"].append(item.get("justification", "n/a"))

            st.table(table_data)
        else:
            st.info("This detected tone is not distributed across organization tones.")


def _render_semantic_mapping(provider_result: dict[str, object]) -> None:
    """Render semantic mapping between detected tones and organization tones."""
    semantic_mapping = provider_result.get("semantic_mapping")

    if not isinstance(semantic_mapping, dict) or not semantic_mapping:
        return

    st.markdown("**Semantic mapping**")

    real_tones = semantic_mapping.get("level_1_real_tones")
    if isinstance(real_tones, dict) and real_tones:
        st.markdown("Real detected tones")
        st.table(
            {
                "Tone": list(real_tones.keys()),
                "Score": list(real_tones.values()),
            }
        )

    mappings = semantic_mapping.get("level_2_mapping")
    if isinstance(mappings, list) and mappings:
        st.markdown("Tone mapping")
        table_data = {
            "Source tone": [],
            "Source score": [],
            "Mapped tone": [],
            "Similarity": [],
            "In org vocabulary": [],
            "Justification": [],
        }

        for item in mappings:
            if not isinstance(item, dict):
                continue

            table_data["Source tone"].append(item.get("source_tone", "n/a"))
            table_data["Source score"].append(item.get("source_score", "n/a"))
            table_data["Mapped tone"].append(item.get("mapped_tone", "n/a"))
            table_data["Similarity"].append(item.get("semantic_similarity", "n/a"))
            table_data["In org vocabulary"].append(item.get("in_org_vocabulary", "n/a"))
            table_data["Justification"].append(item.get("justification", "n/a"))

        st.table(table_data)

    org_scores = semantic_mapping.get("level_3_org_scores")
    if isinstance(org_scores, dict) and org_scores:
        st.markdown("Organization tone scores")
        st.table(
            {
                "Organization tone": list(org_scores.keys()),
                "Score": list(org_scores.values()),
            }
        )


def _render_provider_details(
    provider_label: str,
    provider_result: dict[str, object],
) -> None:
    """Render detailed provider result in a collapsed expander."""
    if not provider_result:
        return

    with st.expander(f"{provider_label} details", expanded=False):
        st.metric(
            "Confidence",
            str(provider_result.get("confidence", "n/a")),
        )

        summary = provider_result.get("summary")
        if summary:
            st.write(str(summary))

        _render_blind_observation(provider_result)
        _render_semantic_mapping(provider_result)
        _render_tone_distribution(provider_result)

        criterion_scores = provider_result.get("criterion_scores")
        if isinstance(criterion_scores, dict) and criterion_scores:
            st.markdown("**Criterion scores**")
            st.json(criterion_scores)

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
    _render_detected_tone_criterion_table(judge_result)
    _render_expected_tone_criterion_table(judge_result)

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


def _extract_organization_context(uploaded_file: object) -> dict[str, str]:
    """Extract tone judge context fields from an organization JSON file."""
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

    tones_payload = data.get("tones") or {}
    voices_payload = data.get("voices") or {}
    style_payload = data.get("style") or {}

    tones = tones_payload.get("tones") if isinstance(tones_payload, dict) else []
    voices = voices_payload.get("voices") if isinstance(voices_payload, dict) else []

    return {
        "org_tones": ", ".join(tones) if isinstance(tones, list) else "",
        "organization_voice": (", ".join(voices) if isinstance(voices, list) else ""),
        "organization_voice_description": (
            str(voices_payload.get("comment", ""))
            if isinstance(voices_payload, dict)
            else ""
        ),
        "writing_style": (
            str(style_payload.get("writingStyle", ""))
            if isinstance(style_payload, dict)
            else ""
        ),
    }


def _extract_persona_context(uploaded_file: object) -> str:
    """Extract persona context from a persona JSON file."""
    if uploaded_file is None:
        return ""

    try:
        raw_content = uploaded_file.read()
        payload = json.loads(raw_content.decode("utf-8"))
    except AttributeError, UnicodeDecodeError, json.JSONDecodeError:
        return ""

    data = payload.get("data")
    if not isinstance(data, dict):
        return ""

    persona_fields = data.get("personaFields")
    if not isinstance(persona_fields, dict):
        return ""

    parts = []

    function = data.get("function")
    if function:
        parts.append(f"Fonction : {function}")

    field_labels = {
        "professionalObjectives": "Objectifs professionnels",
        "problemsFrustrations": "Problèmes et frustrations",
        "decisionMakingInfluence": "Processus de décision",
        "psychologicalProfile": "Profil psychologique",
        "touchPoint": "Points de contact",
        "valuesEthic": "Valeurs et éthique",
        "informationFeeds": "Sources d’influence",  # noqa: RUF001
        "educationLevel": "Niveau de formation",
        "organizationType": "Type d’organisation",  # noqa: RUF001
        "personaType": "Rôle dans le processus d’achat",  # noqa: RUF001
    }

    for field_name, label in field_labels.items():
        value = persona_fields.get(field_name)
        if value:
            parts.append(f"{label} : {value}")

    return "\n\n".join(parts)


def render_tone_form(selected_item: JudgeWorkbenchItem) -> None:  # noqa: ARG001
    """Render the tone judge form."""
    st.markdown("### Tone test input")

    organization_context_file = st.file_uploader(
        "Upload organization JSON",
        type=["json"],
        key="tone_organization_context_uploader",
    )

    organization_context = _extract_organization_context(organization_context_file)

    persona_context_file = st.file_uploader(
        "Upload persona JSON",
        type=["json"],
        key="tone_persona_context_uploader",
    )

    persona_context = _extract_persona_context(persona_context_file)

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

        org_tones = st.text_input(
            "Organization tones",
            value=organization_context.get(
                "org_tones",
                "posé, pédagogique, convaincant",
            ),
        )

        organization_voice = st.text_input(
            "Organization voice",
            value=organization_context.get(
                "organization_voice",
                "structurée, équilibrée, accessible",
            ),
        )

        organization_voice_description = st.text_area(
            "Organization voice description",
            height=100,
            value=organization_context.get("organization_voice_description", ""),
            placeholder="Describe the editorial voice...",
        )

        writing_style = st.text_area(
            "Writing style rules",
            height=120,
            value=organization_context.get("writing_style", ""),
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
            height=180,
            value=persona_context,
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
            "org_tones": [
                tone.strip() for tone in org_tones.split(",") if tone.strip()
            ],
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

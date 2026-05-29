from __future__ import annotations

from typing import TYPE_CHECKING

import requests
import streamlit as st

if TYPE_CHECKING:
    from contentcreajudge.ui.viewmodels.judge_playground_vm import JudgeWorkbenchItem


HTTP_SUCCESS_MIN = 200
HTTP_REDIRECT_MIN = 300


def _read_uploaded_text_file(uploaded_file: object) -> str:
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


def _render_exchange_summary(exchange: dict[str, object]) -> None:  # noqa: C901, PLR0912, PLR0915
    """Render the API response in a readable way."""
    response_status = exchange.get("response_status")
    response_body = exchange.get("response_body") or {}
    error = exchange.get("error")

    if error:
        st.error(str(error))
    elif (
        response_status and HTTP_SUCCESS_MIN <= int(response_status) < HTTP_REDIRECT_MIN
    ):
        st.success("Evergreen judge executed successfully.")
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
            f"`{rule_resolution.get('profile', 'unknown')}`",
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
            st.metric(
                "Temporal references",
                str(preprocessing.get("temporal_references_count", "n/a")),
            )

        with pre_right:
            st.metric("Locale key", str(preprocessing.get("locale_key", "n/a")))

        with st.expander("Show detected temporal references"):
            st.json(preprocessing.get("temporal_references", []))

        with st.expander("Show preprocessing text signals"):
            st.json(
                {
                    "normalized_text": preprocessing.get("normalized_text", ""),
                },
            )

    if isinstance(judge_result, dict):
        st.markdown("**Judge result**")
        judge_left, judge_right = st.columns(2)

        with judge_left:
            st.metric("Judge status", str(judge_result.get("status", "unknown")))

        with judge_right:
            st.metric("Judge score", str(judge_result.get("score", "n/a")))

        llm_evaluation = judge_result.get("llm_evaluation")
        if isinstance(llm_evaluation, dict) and llm_evaluation:
            st.markdown("**LLM Evergreen evaluation**")

            level = llm_evaluation.get("niveau")
            if level:
                st.metric("Evergreen level", str(level))

            llm_evaluation = judge_result.get("llm_evaluation")

            if isinstance(llm_evaluation, dict) and llm_evaluation:
                with st.expander("Show LLM evaluation results"):
                    scores = llm_evaluation.get("scores", {})

                    if isinstance(scores, dict) and scores:
                        score_rows = [
                            {
                                "Critère": "Dépendance temporelle",
                                "Score": scores.get("dependance_temporelle"),
                            },
                            {
                                "Critère": "Stabilité des informations",
                                "Score": scores.get("stabilite_informations"),
                            },
                            {
                                "Critère": "Utilité durable",
                                "Score": scores.get("utilite_durable"),
                            },
                            {
                                "Critère": "Besoin de mise à jour",
                                "Score": scores.get("besoin_mise_a_jour"),
                            },
                            {
                                "Critère": "Réutilisabilité éditoriale",
                                "Score": scores.get("reutilisabilite_editoriale"),
                            },
                        ]

                        st.dataframe(score_rows, use_container_width=True)

                    score_col, level_col = st.columns(2)

                    with score_col:
                        st.metric(
                            "Score global evergreen",
                            llm_evaluation.get("score_global_evergreen", "n/a"),
                        )

                    with level_col:
                        st.metric(
                            "Niveau",
                            llm_evaluation.get("niveau", "n/a"),
                        )

            justification = llm_evaluation.get("justification_courte")
            if justification:
                st.info(str(justification))

            informations = llm_evaluation.get("informations_a_surveiller")
            if isinstance(informations, list) and informations:
                st.markdown("**Informations à surveiller**")
                for item in informations:
                    st.markdown(f"- {item}")

            recommandations = llm_evaluation.get("recommandations")
            if isinstance(recommandations, list) and recommandations:
                st.markdown("**Recommandations**")
                for item in recommandations:
                    st.markdown(f"- {item}")

            passages = llm_evaluation.get("passages_problematiques")
            if isinstance(passages, list) and passages:
                st.markdown("**Passages problématiques**")
                for passage in passages:
                    if not isinstance(passage, dict):
                        continue

                    st.warning(
                        f"{passage.get('extrait', '')} — "
                        f"{passage.get('probleme', '')} "
                        f"({passage.get('gravite', 'n/a')})",
                    )
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
                        ", ".join(f"{key}: {value}" for key, value in evidence.items()),
                    )

    with st.expander("Show raw API exchange"):
        st.json(exchange)


def render_evergreen_form(selected_item: JudgeWorkbenchItem) -> None:
    """Render the evergreen judge form."""
    del selected_item

    st.markdown("### Evergreen test input")

    if "evergreen_content_input" not in st.session_state:
        st.session_state["evergreen_content_input"] = ""

    with st.form("evergreen_judge_form"):
        st.markdown("**Content input**")

        uploaded_content_file = st.file_uploader(
            "Upload content file",
            type=["html", "htm", "txt"],
            key="evergreen_content_file_uploader",
        )

        content_value = st.session_state["evergreen_content_input"]
        if uploaded_content_file is not None:
            content_value = _read_uploaded_text_file(uploaded_content_file)

        content = st.text_area(
            "Content to evaluate",
            height=260,
            placeholder="Paste the content to evaluate here...",
            value=content_value,
        )

        evergreen = st.checkbox(
            "Evergreen required",
            value=True,
        )

        st.caption(
            "If enabled, the judge detects temporal references that may make "
            "the content quickly outdated.",
        )

        locale = st.text_input(
            "Locale",
            value="fr-FR",
            placeholder="fr-FR",
        )

        submitted = st.form_submit_button("Run Evergreen Judge")

    st.session_state["evergreen_content_input"] = content

    if not submitted:
        return

    payload = {
        "content": content,
        "profile": "default",
        "context": {
            "evergreen": evergreen,
            "locale": locale.strip() or None,
        },
    }

    st.session_state["evergreen_payload"] = payload
    st.session_state["evergreen_run_requested"] = True


def render_evergreen_result(
    api_url: str,
    selected_item: JudgeWorkbenchItem,
) -> None:
    """Read the payload and display the API response."""
    st.markdown(
        '<div class="section-label">Evergreen result</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">API response</h3>',
        unsafe_allow_html=True,
    )

    payload = st.session_state.get("evergreen_payload")

    if not payload:
        st.info("Fill the form and run the Evergreen judge to see the response here.")
        return

    should_run = st.session_state.get("evergreen_run_requested", False)
    if not should_run:
        last_exchange = st.session_state.get("last_evergreen_exchange")
        if last_exchange:
            _render_exchange_summary(last_exchange)
        return

    content = payload.get("content", "")
    context = payload.get("context", {})
    locale = context.get("locale", "") if isinstance(context, dict) else ""

    if not str(content).strip():
        st.warning("Please provide content to evaluate.")
        st.session_state["evergreen_run_requested"] = False
        return

    if not str(locale).strip():
        st.warning("Please provide the locale.")
        st.session_state["evergreen_run_requested"] = False
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
        st.session_state["last_evergreen_exchange"] = exchange
        _render_exchange_summary(exchange)
        st.session_state["evergreen_run_requested"] = False
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
        st.session_state["last_evergreen_exchange"] = exchange
        _render_exchange_summary(exchange)
        st.session_state["evergreen_run_requested"] = False
        return

    exchange = {
        "request_payload": payload,
        "response_status": response.status_code,
        "response_body": response_data,
        "error": None if response.ok else "The Evergreen judge request failed.",
    }

    st.session_state["last_evergreen_exchange"] = exchange
    _render_exchange_summary(exchange)

    st.session_state["evergreen_run_requested"] = False

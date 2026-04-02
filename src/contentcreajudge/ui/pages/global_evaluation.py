"""Global evaluation page for the Streamlit UI."""

from __future__ import annotations

import streamlit as st

from contentcreajudge.ui.services.api_client import request_json


def render_global_evaluation(*, api_url: str) -> None:
    """Render the global evaluation workspace."""
    st.markdown(
        '<div class="section-label">Payload composer</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">Global evaluation</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="payload-note">
            This workspace represents the future full product flow. It already
            submits a stable payload to the global evaluation endpoint and shows
            the transport exchange end to end.
        </div>
        """,
        unsafe_allow_html=True,
    )

    form_column, result_column = st.columns([1.05, 0.95], gap="large")
    with form_column, st.form("global-evaluation-form"):
        st.text_input("Request ID", key="request_id", placeholder="demo-001")
        st.text_input(
            "Content title",
            key="content_title",
            placeholder="How to build a durable editorial workflow",
        )
        selection_left, selection_right = st.columns(2)
        with selection_left:
            st.selectbox(
                "Profile",
                options=["default", "blog", "landing-page"],
                key="profile",
            )
            st.text_input(
                "Content type",
                key="content_type",
                placeholder="article",
            )
        with selection_right:
            st.text_input("Channel", key="channel", placeholder="website")
            st.text_input("Locale", key="locale", placeholder="en-US")

        st.text_area(
            "Content",
            key="content",
            height=300,
            placeholder=(
                "Paste the editorial content here. This input will later be "
                "sent through preprocessing, mini-judges, and aggregation."
            ),
        )
        st.text_input(
            "Target keywords",
            key="target_keywords",
            placeholder="editorial workflow, content quality, SEO",
        )
        st.text_area(
            "Declared sources",
            key="declared_sources",
            height=110,
            placeholder="One source URL per line",
        )
        submitted = st.form_submit_button("Run global evaluation")

    with result_column:
        st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">API output</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h3 class="section-title">Response console</h3>',
            unsafe_allow_html=True,
        )
        if submitted:
            payload = _build_evaluation_payload()
            result = request_json(
                f"{api_url}/api/v1/evaluations",
                method="POST",
                payload=payload,
            )
            st.session_state["last_evaluation_exchange"] = {
                "request_payload": payload,
                "response_status": result.status_code,
                "response_body": result.payload,
                "error": result.error,
            }
            if result.ok:
                st.success("Payload accepted by the global evaluation endpoint.")
            else:
                st.error(result.error or "The evaluation request failed.")
        else:
            st.info(
                "Use the form to send a payload. The console will preserve the "
                "latest backend exchange during your demo.",
            )

        exchange = st.session_state.get("last_evaluation_exchange")
        if exchange:
            st.json(exchange)
        else:
            st.markdown(
                """
                <div class="payload-note">
                    This panel is ready to show the request payload, the backend
                    response, and later the judge-by-judge breakdown with final
                    aggregation.
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def _build_evaluation_payload() -> dict[str, object]:
    """Build the global evaluation payload from the current form state."""
    keywords = [
        keyword.strip()
        for keyword in st.session_state["target_keywords"].split(",")
        if keyword.strip()
    ]
    declared_sources = [
        source.strip()
        for source in st.session_state["declared_sources"].splitlines()
        if source.strip()
    ]

    payload: dict[str, object] = {
        "content": st.session_state["content"],
        "profile": st.session_state["profile"],
        "target_keywords": keywords,
        "declared_sources": declared_sources,
    }
    optional_fields = {
        "content_title": st.session_state["content_title"],
        "content_type": st.session_state["content_type"],
        "channel": st.session_state["channel"],
        "locale": st.session_state["locale"],
        "request_id": st.session_state["request_id"],
    }
    payload.update(
        {
            field_name: field_value
            for field_name, field_value in optional_fields.items()
            if field_value
        },
    )
    return payload

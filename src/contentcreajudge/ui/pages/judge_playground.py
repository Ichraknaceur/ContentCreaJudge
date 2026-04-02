"""Judge playground page for the Streamlit UI."""

from __future__ import annotations

import html

import streamlit as st

from contentcreajudge.ui.viewmodels.judge_playground_vm import (
    get_judge_by_key,
    get_judge_workbench_items,
)


def render_judge_playground() -> None:
    """Render the judge-by-judge demo workspace."""
    st.markdown(
        '<div class="section-label">Judge playground</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">Mini-judge workspace</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="payload-note">
            This screen is intentionally architecture-first. It reserves a clean
            workspace for dedicated judge endpoints without freezing their
            business-specific input and output contracts too early.
        </div>
        """,
        unsafe_allow_html=True,
    )

    items = get_judge_workbench_items()
    selected_key = st.selectbox(
        "Mini-judge",
        options=[item.key for item in items],
        format_func=lambda key: get_judge_by_key(key).title,
    )
    selected_item = get_judge_by_key(selected_key)

    cards = st.columns(3, gap="large")
    for index, item in enumerate(items):
        with cards[index % 3]:
            st.markdown(
                f"""
                <div class="judge-card">
                    <div class="judge-badge">{html.escape(item.status)}</div>
                    <h4>{html.escape(item.title)}</h4>
                    <p>{html.escape(item.summary)}</p>
                    <div class="judge-endpoint">{html.escape(item.endpoint)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    left_column, right_column = st.columns([1.05, 0.95], gap="large")
    with left_column:
        st.markdown('<div class="judge-stage-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">Selected judge</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h4>{html.escape(selected_item.title)}</h4>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p>{html.escape(selected_item.summary)}</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="judge-endpoint">{html.escape(selected_item.endpoint)}</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="payload-note">
                Les inputs et outputs détaillés de ce judge seront définis dans
                la prochaine phase. L'interface est volontairement déjà prête
                pour accueillir ce contrat sans mélanger la logique métier dans
                la couche UI.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_column:
        st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">Planned interaction</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h3 class="section-title">Future test flow</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <ul class="roadmap-list">
                <li>Select one mini-judge</li>
                <li>Fill the judge-specific input form</li>
                <li>Call the dedicated judge endpoint</li>
                <li>Display the isolated judge response</li>
                <li>Reuse the same judge logic in global evaluation</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )
        st.info(
            "This page is ready as a client demo surface and as a manual QA "
            "surface for the team. The business contract of each judge comes "
            "next.",
        )
        st.markdown("</div>", unsafe_allow_html=True)

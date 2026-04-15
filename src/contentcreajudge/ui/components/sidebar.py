"""Sidebar component for the Streamlit UI."""

from __future__ import annotations
from pathlib import Path

from pathlib import Path

import streamlit as st

LOGO_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "logo-fond-bleu-64x64.jpg"
)

def render_sidebar(default_api_url: str) -> str:
    """Render the sidebar configuration panel."""
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-badge">ContentCrea</div>',
            unsafe_allow_html=True,
        )
        _, logo_column, _ = st.columns([1, 1.8, 1])
        with logo_column:
            st.image(str(LOGO_PATH), width=148)
        st.markdown(
            """
            <div class="sidebar-brand">
                <h2>Evaluator</h2>
                <p>
                    Rule-based editorial evaluation inside the same visual
                    universe as ContentCrea.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="sidebar-section-title">API connection</div>',
            unsafe_allow_html=True,
        )
        api_url = st.text_input("API base URL", value=default_api_url)
        st.caption(
            "Launch the backend with `make run`, then open this workspace.",
        )
        st.markdown(
            '<div class="sidebar-section-title">V1 scope</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <ul class="sidebar-list">
                <li>Structure</li>
                <li>Length</li>
                <li>Typography</li>
                <li>Evergreen compliance</li>
                <li>CTA compliance</li>
                <li>Sources validation</li>
                <li>Basic SEO keyword presence</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )
    return api_url.rstrip("/")

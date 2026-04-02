"""Delivery view page for the Streamlit UI."""

from __future__ import annotations

import streamlit as st

from contentcreajudge.ui.components.surfaces import render_delivery_band


def render_delivery_view() -> None:
    """Render a client-facing progress view."""
    st.markdown(
        '<div class="section-label">Client narrative</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h3 class="section-title">Delivery view</h3>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Use this screen during demos to explain what is already live, what is "
        "next on the roadmap, and what belongs to V1 scope.",
    )

    built_column, next_column, scope_column = st.columns(3, gap="large")
    with built_column:
        render_delivery_band(
            "Built now",
            [
                "Backend API skeleton",
                "Health endpoint",
                "Evaluation endpoint placeholder",
                "Streamlit demonstration interface",
            ],
        )
    with next_column:
        render_delivery_band(
            "Next backend steps",
            [
                "Refine application orchestration",
                "Wire preprocessing layer",
                "Expose judge-specific endpoints",
                "Connect first real mini-judge",
            ],
        )
    with scope_column:
        render_delivery_band(
            "V1 evaluation dimensions",
            [
                "Structure",
                "Length",
                "Typography",
                "Evergreen compliance",
                "CTA compliance",
                "Sources validation",
                "Basic SEO keyword presence",
            ],
        )

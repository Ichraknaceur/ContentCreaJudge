"""Overview page for the Streamlit UI."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

import streamlit as st

from contentcreajudge.ui.components.surfaces import render_card

if TYPE_CHECKING:
    from contentcreajudge.ui.services.api_client import ApiCallResult
    from contentcreajudge.ui.viewmodels.overview_vm import OverviewViewModel

FOUNDATION_PROGRESS = 0.4


def render_overview(
    *,
    overview_vm: OverviewViewModel,
    health_result: ApiCallResult,
) -> None:
    """Render the overview dashboard."""
    st.markdown(
        '<div class="section-label">Service pulse</div>',
        unsafe_allow_html=True,
    )
    left_column, middle_column, right_column = st.columns(3, gap="large")

    with left_column:
        render_card(
            "API health",
            overview_vm.health_label,
            overview_vm.health_note,
            tone="tone-online" if health_result.ok else "tone-warning",
        )

    with middle_column:
        render_card(
            "Exposed endpoints",
            str(overview_vm.endpoint_count),
            "Registered backend routes",
        )

    with right_column:
        render_card(
            "Backend version",
            overview_vm.version,
            "Provided by /health",
        )

    detail_column, roadmap_column = st.columns([1.1, 0.9], gap="large")
    with detail_column:
        st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">System status</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h3 class="section-title">Operational status</h3>',
            unsafe_allow_html=True,
        )
        status_class = "" if health_result.ok else " offline"
        st.markdown(
            (
                f'<div class="status-line{status_class}">'
                f"{html.escape(overview_vm.status_message)}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        with st.expander("Latest health payload", expanded=health_result.ok):
            st.json(health_result.payload or {"error": health_result.error})
        st.markdown("</div>", unsafe_allow_html=True)

    with roadmap_column:
        st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-label">Delivery track</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<h3 class="section-title">Current delivery markers</h3>',
            unsafe_allow_html=True,
        )
        st.progress(FOUNDATION_PROGRESS, text="Foundation phase")
        st.markdown(
            """
            <ul class="roadmap-list">
                <li>API bootstrap ready</li>
                <li>Health monitoring ready</li>
                <li>Evaluation route ready</li>
                <li>UI theme aligned</li>
                <li>Mini-judge execution pending</li>
            </ul>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

"""Reusable visual surfaces for the Streamlit UI."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from contentcreajudge.ui.viewmodels.overview_vm import OverviewViewModel


def render_card(
    title: str,
    value: str,
    note: str,
    *,
    tone: str = "",
) -> None:
    """Render a custom KPI card."""
    tone_class = f" {tone}" if tone else ""
    st.markdown(
        f"""
        <div class="kpi-card{tone_class}">
            <div class="label">{html.escape(title)}</div>
            <div class="value">{html.escape(value)}</div>
            <div class="note">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_delivery_band(title: str, items: list[str]) -> None:
    """Render a delivery summary band."""
    items_html = "".join(f"<li>{html.escape(item)}</li>" for item in items)
    st.markdown(
        f"""
        <div class="delivery-band">
            <h4>{html.escape(title)}</h4>
            <ul class="delivery-grid">{items_html}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(overview_vm: OverviewViewModel) -> None:
    """Render the top hero section."""
    hero_column, spotlight_column = st.columns([1.35, 0.85], gap="large")
    with hero_column:
        st.markdown(
            """
            <div class="hero-shell">
                <div class="eyebrow">ContentCrea workspace</div>
                <h1>ContentCreaEvaluator</h1>
                <div class="hero-copy">
                    Clean review surface for the evaluator product. The UI now
                    follows the ContentCrea visual language while keeping the
                    evaluation workflow visible for demos and internal review.
                </div>
                <div class="chip-row">
                    <span class="chip">Rule-based V1</span>
                    <span class="chip">Shared ContentCrea theme</span>
                    <span class="chip">FastAPI + Streamlit</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with spotlight_column:
        st.markdown(
            f"""
            <div class="spotlight-card">
                <div class="eyebrow">Workspace status</div>
                <h3>{html.escape(overview_vm.status_label)}</h3>
                <p>{html.escape(overview_vm.status_note)}</p>
                <ul class="roadmap-list">
                    <li>Health endpoint available</li>
                    <li>Evaluation route connected</li>
                    <li>Theme aligned with ContentCrea</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

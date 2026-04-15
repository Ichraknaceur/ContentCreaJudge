"""Theme helpers for the ContentCrea-aligned Streamlit UI."""

from __future__ import annotations

import os

import streamlit as st

DEFAULT_API_URL = os.getenv("CONTENTCREAJUDGE_API_URL", "http://127.0.0.1:8000")


def initialize_ui() -> None:
    """Configure the Streamlit page and inject the UI theme."""
    _ensure_demo_defaults()
    st.set_page_config(
        page_title="ContentCreaEvaluator",
        page_icon="CC",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(_theme_css(), unsafe_allow_html=True)


def _ensure_demo_defaults() -> None:
    """Initialize helpful demo defaults for the UI state."""
    st.session_state.setdefault("request_id", "demo-001")
    st.session_state.setdefault(
        "content_title",
        "How to build an editorial workflow that stays evergreen",
    )
    st.session_state.setdefault("profile", "default")
    st.session_state.setdefault("content_type", "article")
    st.session_state.setdefault("channel", "website")
    st.session_state.setdefault("locale", "en-US")
    st.session_state.setdefault(
        "content",
        (
            "A strong editorial workflow begins with a stable structure, clear "
            "typography, and durable sources. The goal is to publish content "
            "that stays useful over time while preserving a visible call to "
            "action and target keyword coverage."
        ),
    )
    st.session_state.setdefault(
        "target_keywords",
        "editorial workflow, evergreen content, content quality",
    )
    st.session_state.setdefault(
        "declared_sources",
        "https://example.com/editorial-guidelines\nhttps://example.com/seo-playbook",
    )


def _theme_css() -> str:
    """Return the CSS theme injected into the Streamlit app."""
    return """
    <style>
    #MainMenu, footer, .stAppDeployButton {
        display: none;
    }
    header[data-testid="stHeader"] {
        background: transparent;
    }
    .stApp, [data-testid="stAppViewContainer"] {
        color: #1f2430;
    }
    .stApp {
        background: #f7f9fc;
        font-family: "Avenir Next", "Helvetica Neue", "Segoe UI", sans-serif;
    }
    .block-container {
        max-width: 1320px;
        padding-top: 1.6rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3, h4, .section-title {
        font-family: "Avenir Next", "Helvetica Neue", "Segoe UI", sans-serif;
        color: #232736;
        letter-spacing: -0.04em;
    }
    p, li, label, .stMarkdown, .stCaption {
        color: #657089;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4c73ea 0%, #4f78f2 100%);
        border-right: none;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff;
    }
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] .stMarkdown p {
        color: rgba(255, 255, 255, 0.84) !important;
    }
    [data-testid="stSidebar"] .stTextInput input {
        background: rgba(255, 255, 255, 0.14);
        border: 1px solid rgba(255, 255, 255, 0.28);
        color: #ffffff;
        border-radius: 12px;
    }
    .sidebar-badge {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.22);
        color: #ffffff;
        padding: 0.3rem 0.72rem;
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .sidebar-brand {
        padding-top: 1rem;
    }
    .sidebar-brand h2 {
        margin: 1rem 0 0.35rem;
        color: #ffffff;
        font-size: 2rem;
        font-weight: 500;
        letter-spacing: -0.05em;
    }
    .sidebar-brand p {
        max-width: 16rem;
        color: rgba(255, 255, 255, 0.82);
        line-height: 1.6;
    }
    .brand-mark {
        position: relative;
        width: 180px;
        height: 180px;
        margin: 4rem auto 3rem;
        border: 13px solid #ffffff;
        border-radius: 50%;
        box-sizing: border-box;
    }
    .brand-mark::before {
        content: "";
        position: absolute;
        inset: 18px;
        border: 10px solid #ffffff;
        border-right-color: transparent;
        border-bottom-color: transparent;
        border-radius: 50%;
    }
    .brand-mark::after {
        content: "";
        position: absolute;
        inset: 58px;
        border: 10px solid #ffffff;
        border-right-color: transparent;
        border-bottom-color: transparent;
        border-radius: 50%;
    }
    .sidebar-section-title {
        margin-top: 1.6rem;
        margin-bottom: 0.65rem;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.88);
    }
    .sidebar-list {
        margin: 0.4rem 0 0;
        padding: 0;
        list-style: none;
    }
    .sidebar-list li {
        padding: 0.55rem 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.14);
        color: rgba(255, 255, 255, 0.96);
    }
    .hero-shell {
        padding: 0.2rem 0 1.2rem;
        background: transparent;
    }
    .eyebrow {
        display: inline-block;
        margin-bottom: 0.6rem;
        color: #4f78f2;
        font-size: 0.76rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .hero-shell h1 {
        margin: 0;
        font-size: clamp(2.3rem, 4vw, 3.5rem);
        line-height: 1.02;
        font-weight: 500;
    }
    .hero-copy {
        max-width: 44rem;
        margin-top: 0.9rem;
        font-size: 1rem;
        line-height: 1.7;
        color: #6a748b;
    }
    .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
        margin-top: 1.1rem;
    }
    .chip {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 0.44rem 0.85rem;
        background: #ffffff;
        border: 1px solid #dfe5f2;
        color: #50607f;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .spotlight-card,
    .kpi-card,
    .panel-shell,
    .delivery-band,
    .judge-card,
    .judge-stage-card {
        background: #ffffff;
        border: 1px solid #e3e8f3;
        box-shadow: 0 12px 28px rgba(57, 75, 120, 0.06);
    }
    .spotlight-card {
        height: 100%;
        padding: 1.4rem;
        border-radius: 20px;
        color: #232736;
    }
    .spotlight-card h3 {
        margin: 0.15rem 0 0.7rem;
        color: #232736;
        font-size: 1.55rem;
        font-weight: 500;
    }
    .spotlight-card p, .spotlight-card li {
        color: #6b7590;
    }
    .section-label {
        margin-top: 0.4rem;
        margin-bottom: 0.9rem;
        color: #4f78f2;
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .kpi-card {
        padding: 1.25rem 1.2rem;
        border-radius: 18px;
    }
    .kpi-card .label {
        color: #7b859c;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .kpi-card .value {
        margin-top: 0.55rem;
        font-family: "Avenir Next", "Helvetica Neue", "Segoe UI", sans-serif;
        font-size: 2.1rem;
        line-height: 1;
        color: #232736;
        font-weight: 500;
    }
    .kpi-card .note {
        margin-top: 0.55rem;
        color: #7c869e;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .tone-online {
        box-shadow: inset 0 0 0 1px rgba(76, 114, 235, 0.16);
    }
    .tone-warning {
        box-shadow: inset 0 0 0 1px rgba(214, 153, 73, 0.18);
    }
    .panel-shell,
    .judge-stage-card {
        padding: 1.35rem;
        border-radius: 20px;
    }
    .section-title {
        margin: 0;
        font-size: 1.35rem;
        font-weight: 500;
    }
    .status-line {
        margin-top: 0.8rem;
        padding: 0.95rem 1rem;
        border-radius: 14px;
        background: rgba(79, 120, 242, 0.06);
        border: 1px solid rgba(79, 120, 242, 0.14);
        color: #3f5bb2;
        font-weight: 700;
    }
    .status-line.offline {
        border-color: rgba(214, 153, 73, 0.22);
        color: #af7e25;
    }
    .roadmap-list, .delivery-grid {
        margin: 0;
        padding: 0;
        list-style: none;
    }
    .roadmap-list li, .delivery-grid li {
        margin: 0.68rem 0;
        padding-left: 1rem;
        position: relative;
    }
    .roadmap-list li::before, .delivery-grid li::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0.62rem;
        width: 0.38rem;
        height: 0.38rem;
        border-radius: 50%;
        background: #4f78f2;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.7rem;
        padding: 0;
        background: transparent;
        border: none;
        border-bottom: 1px solid #e5e9f3;
        border-radius: 0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 2.85rem;
        padding: 0 0.1rem;
        margin-right: 1.4rem;
        border-radius: 0;
        color: #8c95aa;
        font-weight: 800;
        border-bottom: 2px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background: transparent !important;
        color: #4f78f2 !important;
        border-bottom-color: #4f78f2 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {
        color: #7e879d !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div {
        background: #ffffff;
        border-radius: 10px !important;
        border: 1px solid #d9dfec !important;
        color: #232736 !important;
        box-shadow: none !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: rgba(79, 120, 242, 0.62) !important;
        box-shadow: 0 0 0 1px rgba(79, 120, 242, 0.28) !important;
    }
    .stForm {
        padding: 1.1rem 0.2rem 0.2rem;
        border-radius: 0;
        background: transparent;
        border: none;
        box-shadow: none;
    }
    .stButton button, .stFormSubmitButton button {
        min-height: 3rem;
        border-radius: 12px;
        border: 1px solid #8fb3ff;
        background: linear-gradient(180deg, #7fb0ff 0%, #5f95ff 100%);
        color: #ffffff;
        font-weight: 800;
        letter-spacing: 0.04em;
        box-shadow: 0 10px 20px rgba(95, 149, 255, 0.24);
        cursor: pointer;
        transition:
            background 0.18s ease,
            transform 0.18s ease,
            box-shadow 0.18s ease,
            border-color 0.18s ease;
    }
    .stButton button:hover, .stFormSubmitButton button:hover {
        border-color: #6f9fff;
        background: linear-gradient(180deg, #96beff 0%, #6ea0ff 100%);
        box-shadow: 0 14px 28px rgba(95, 149, 255, 0.3);
        transform: translateY(-1px);
    }
    .stButton button:focus, .stFormSubmitButton button:focus {
        outline: none;
        border-color: #4f78f2;
        box-shadow:
            0 0 0 3px rgba(79, 120, 242, 0.18),
            0 12px 24px rgba(95, 149, 255, 0.28);
    }
    .stAlert {
        border-radius: 14px;
    }
    [data-testid="stJson"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid #e3e8f3;
    }
    .payload-note {
        margin-top: 0.8rem;
        padding: 0.95rem 1rem;
        border-radius: 12px;
        background: rgba(79, 120, 242, 0.05);
        border: 1px solid rgba(79, 120, 242, 0.12);
        color: #5f6880;
    }
    .delivery-band {
        padding: 1rem 1.1rem;
        border-radius: 16px;
    }
    .delivery-band h4,
    .judge-card h4,
    .judge-stage-card h4 {
        margin: 0 0 0.7rem;
        font-size: 1.2rem;
        color: #232736;
        font-weight: 500;
    }
    .judge-card {
        padding: 1rem;
        border-radius: 16px;
    }
    .judge-badge {
        display: inline-flex;
        border-radius: 999px;
        padding: 0.28rem 0.68rem;
        background: rgba(79, 120, 242, 0.08);
        color: #4f78f2;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .judge-endpoint {
        margin-top: 0.8rem;
        padding: 0.7rem 0.8rem;
        border-radius: 12px;
        background: #f6f8fd;
        border: 1px solid #e0e6f3;
        color: #62708d;
        font-family: "SFMono-Regular", "Menlo", monospace;
        font-size: 0.82rem;
    }
    .stProgress > div > div > div > div {
        background-color: #4f78f2;
    }
    </style>
    """

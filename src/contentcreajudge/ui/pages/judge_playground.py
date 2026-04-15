"""Judge playground page for the Streamlit UI."""

from __future__ import annotations

import html
from importlib import import_module

import streamlit as st

from contentcreajudge.ui.viewmodels.judge_playground_vm import (
    get_judge_by_key,
    get_judge_workbench_items,
)

WORKSPACE_MODULES = {
    "length": "contentcreajudge.ui.components.judges.length_workspace",
    "structure": "contentcreajudge.ui.components.judges.structure_workspace",
    "typography": "contentcreajudge.ui.components.judges.typography_workspace",
}

def get_workspace_renderer_config(selected_key: str) -> dict[str, object] | None:
    """Dynamically load the selected mini-judge workspace and return its rendering functions"""
    module_path = WORKSPACE_MODULES.get(selected_key)
    if module_path is None:
        return None

    workspace_module = import_module(module_path)

    form_renderer = getattr(
        workspace_module,
        f"render_{selected_key}_form",
        getattr(workspace_module, "render_form", None),
    )
    result_renderer = getattr(
        workspace_module,
        f"render_{selected_key}_result",
        getattr(workspace_module, "render_result", None),
    )

    if form_renderer is None or result_renderer is None:
        return None

    return {
        "form": form_renderer,
        "result": result_renderer,
    }

def render_default_workspace() -> None:
    """Display a default workspace for mini-judges that are not implemented yet"""
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

    if "selected_judge_key" not in st.session_state:
        st.session_state["selected_judge_key"] = items[0].key
        
    selected_key = st.selectbox(
        "Mini-judge",
        options=[item.key for item in items],
        index=[item.key for item in items].index(st.session_state["selected_judge_key"]),
        format_func=lambda key: get_judge_by_key(key).title,
    )

    st.session_state["selected_judge_key"] = selected_key
    selected_item = get_judge_by_key(st.session_state["selected_judge_key"])

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
            if st.button(
                f"Open {item.title}",
                key=f"open_judge_{item.key}",
                use_container_width=True,
            ):
                st.session_state["selected_judge_key"] = item.key
                st.rerun()

    renderer_config = get_workspace_renderer_config(selected_item.key)

    left_column, right_column = st.columns([1.05, 0.95], gap="large")
    with left_column:
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
        if renderer_config is not None:
            renderer_config["form"](selected_item=selected_item)
        else:
            st.markdown(
                """
                <div class="payload-note">
                    Les inputs et outputs détaillés de ce judge seront définis
                    dans la prochaine phase. L'interface est volontairement déjà
                    prête pour accueillir ce contrat sans mélanger la logique
                    métier dans la couche UI.
                </div>
                """,
                unsafe_allow_html=True,
            )
    with right_column:
        if renderer_config is not None:
            renderer_config["result"](
                api_url="http://127.0.0.1:8000",
                selected_item=selected_item,
            )
        else:
            render_default_workspace()

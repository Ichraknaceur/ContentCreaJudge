"""Streamlit entrypoint for the ContentCreaEvaluator UI."""

import streamlit as st

from contentcreajudge.ui.components.sidebar import render_sidebar
from contentcreajudge.ui.components.surfaces import render_hero
from contentcreajudge.ui.pages.delivery import render_delivery_view
from contentcreajudge.ui.pages.global_evaluation import render_global_evaluation
from contentcreajudge.ui.pages.judge_playground import render_judge_playground
from contentcreajudge.ui.pages.overview import render_overview
from contentcreajudge.ui.services.api_client import request_json
from contentcreajudge.ui.theme.contentcrea import DEFAULT_API_URL, initialize_ui
from contentcreajudge.ui.viewmodels.overview_vm import build_overview_view_model


def main() -> None:
    """Run the Streamlit application."""
    initialize_ui()
    api_url = render_sidebar(DEFAULT_API_URL)
    health_result = request_json(f"{api_url}/health")
    root_result = request_json(f"{api_url}/")
    overview_vm = build_overview_view_model(
        health_result=health_result,
        root_result=root_result,
    )

    render_hero(overview_vm=overview_vm)
    overview_tab, global_tab, judge_tab, delivery_tab = st.tabs(
        [
            "Overview",
            "Global Evaluation",
            "Judge Playground",
            "Delivery View",
        ],
    )

    with overview_tab:
        render_overview(
            overview_vm=overview_vm,
            health_result=health_result,
        )
    with global_tab:
        render_global_evaluation(api_url=api_url)
    with judge_tab:
        render_judge_playground()
    with delivery_tab:
        render_delivery_view()


if __name__ == "__main__":
    main()

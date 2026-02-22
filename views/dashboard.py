"""
Dashboard — Orchestrator
========================

Thin wrapper that composes scan_view, result_view and detail_view.
Split from a 1,227-line monolith in Sprint P7.
Onboarding, quick-tips, summary card integrated in Sprint 7.

Public API:
    render_scanner_page()   — called by streamlit_app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .components.onboarding import (
    render_onboarding_modal,
    render_onboarding_sidebar_trigger,
    render_quick_tips,
    should_show_onboarding,
)
from .components.summary_card import render_summary_card
from .detail_view import render_ai_insights_panel, render_drl_signals_panel
from .result_view import render_tabs
from .scan_view import (
    _init_session_state,
    render_market_pulse,
    render_preset_selector,
    render_scan_controls,
    render_sidebar,
)


def render_scanner_page() -> None:
    """Main entry point for the scanner dashboard."""
    _init_session_state()

    # Sidebar settings
    ctx = render_sidebar()

    # Sidebar: onboarding guide trigger (always visible)
    render_onboarding_sidebar_trigger()

    # Show onboarding wizard for first-time users
    if should_show_onboarding():
        render_onboarding_modal()
        return  # Don't render dashboard behind the onboarding

    # Get current data
    df: pd.DataFrame = st.session_state.get("scan_df", pd.DataFrame())

    # Quick tip for experienced users
    render_quick_tips()

    # Dashboard summary hero card (3-second rule)
    render_summary_card(df)

    # Market pulse metrics bar
    render_market_pulse(df)

    # AI & DRL insight panels (with empty-state awareness)
    render_ai_insights_panel()
    if not df.empty and "symbol" in df.columns:
        render_drl_signals_panel(df["symbol"].tolist())

    # Preset selector
    render_preset_selector()

    # Scan controls & execution
    render_scan_controls(ctx["kelly_fraction"])

    # Content tabs
    render_tabs(df)

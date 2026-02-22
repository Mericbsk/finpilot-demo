"""
FinPilot Skeleton Loading Components
=====================================

Reusable skeleton placeholders displayed while data loads.
Uses CSS classes defined in styles.py (Sprint 7 — P6).

Usage:
    from views.components.skeleton import render_skeleton_cards, render_skeleton_metrics

    render_skeleton_cards(count=4)
    render_skeleton_metrics(count=4)
"""

from __future__ import annotations

import streamlit as st


def render_skeleton_cards(count: int = 4) -> None:
    """Render skeleton card placeholders in a column grid."""
    cols = st.columns(min(count, 4))
    for i in range(count):
        with cols[i % len(cols)]:
            st.markdown(
                """<div class='skeleton skeleton-card'>
                    <div class='skeleton skeleton-line medium' style='margin-top:20px; margin-left:16px;'></div>
                    <div class='skeleton skeleton-line short' style='margin-left:16px;'></div>
                    <div class='skeleton skeleton-line long' style='margin-left:16px; margin-right:16px;'></div>
                    <div class='skeleton skeleton-line medium' style='margin-left:16px;'></div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_skeleton_metrics(count: int = 4) -> None:
    """Render skeleton metric placeholders."""
    cols = st.columns(count)
    for i in range(count):
        with cols[i]:
            st.markdown(
                """<div style='padding: 12px;'>
                    <div class='skeleton skeleton-line short' style='margin-bottom:8px;'></div>
                    <div class='skeleton skeleton-metric'></div>
                </div>""",
                unsafe_allow_html=True,
            )


def render_skeleton_table(rows: int = 5) -> None:
    """Render a skeleton table placeholder."""
    st.markdown(
        "<div class='skeleton skeleton-line medium' style='margin-bottom:16px;'></div>",
        unsafe_allow_html=True,
    )
    for _ in range(rows):
        st.markdown(
            """<div style='display:flex; gap:12px; margin-bottom:8px;'>
                <div class='skeleton skeleton-line short'></div>
                <div class='skeleton skeleton-line medium'></div>
                <div class='skeleton skeleton-line short'></div>
            </div>""",
            unsafe_allow_html=True,
        )


__all__ = [
    "render_skeleton_cards",
    "render_skeleton_metrics",
    "render_skeleton_table",
]

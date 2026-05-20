"""
Dashboard Summary Card
======================

Renders a "Today's Summary" hero card at the top of the dashboard
after a scan completes. Addresses the 3-second rule by showing
the most important info upfront.

Sprint 7 — P8
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st


def render_summary_card(df: pd.DataFrame) -> None:
    """Render the dashboard summary hero card.

    Shows: best opportunity, total signals, market regime, last scan time.
    Only renders when scan data is available.
    """
    if df is None or df.empty:
        return

    # Calculate summary stats
    total = len(df)
    signal_count = 0
    best_symbol = "-"
    best_score = 0.0
    bull_pct = 0.0

    if "entry_ok" in df.columns:
        signal_count = int(df["entry_ok"].sum())

    if "recommendation_score" in df.columns:
        top = df.nlargest(1, "recommendation_score")
        if not top.empty:
            best_symbol = top.iloc[0].get("symbol", "-")
            best_score = top.iloc[0]["recommendation_score"]

    if "regime" in df.columns:
        bull_pct = (
            len(df[df["regime"].astype(str).str.contains("bull|trend", case=False, na=False)])
            / total
            * 100
        )

    regime_label = "Boğa 📈" if bull_pct > 50 else "Ayı 📉" if bull_pct < 30 else "Karışık ↔"
    scan_time = st.session_state.get("scan_time", datetime.now().strftime("%H:%M"))

    st.markdown(
        f"""
    <div style="
        background: linear-gradient(135deg, var(--bg-secondary, #1e293b) 0%, rgba(0,230,230,0.08) 100%);
        border: 1px solid var(--border-hover, rgba(56,189,248,0.25));
        border-radius: var(--radius-lg, 16px);
        padding: var(--space-6, 24px);
        margin-bottom: var(--space-6, 24px);
        box-shadow: var(--shadow-glow, 0 20px 48px -20px rgba(14,165,233,0.35));
    " role="region" aria-label="Günlük özet">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
            <div>
                <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em;
                            color: var(--text-muted, #94a3b8); margin-bottom: 4px;">
                    📊 Tarama Özeti — {scan_time}
                </div>
                <div style="font-size: 1.3rem; font-weight: 700; color: var(--text-primary, #f8fafc);">
                    {total} sembol tarandı, <span style="color: var(--color-primary, #00e6e6);">{signal_count} aktif sinyal</span>
                </div>
            </div>
            <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: var(--text-muted, #94a3b8);">
                        En Güçlü ▲
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: var(--color-success, #22c55e);">
                        {best_symbol}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary, #94a3b8);">
                        Skor: {best_score:.0f}/100
                    </div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 0.7rem; text-transform: uppercase; color: var(--text-muted, #94a3b8);">
                        Piyasa
                    </div>
                    <div style="font-size: 1.2rem; font-weight: 700; color: var(--text-primary, #f8fafc);">
                        {regime_label}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary, #94a3b8);">
                        %{bull_pct:.0f} Boğa
                    </div>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


__all__ = ["render_summary_card"]

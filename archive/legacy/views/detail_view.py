"""
Detail View — Top Cards & Detail Cards
=======================================

Sprint 10: DRL predictions, AI insights, and signal functions moved to
views/components/ai_signals.py (single source of truth).
This file retains only render_top_cards() and render_detail_card().
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def _render_fundamentals_row(symbol: str) -> None:
    """Show a compact fundamental‐data row below the header."""
    try:
        from drl.fundamentals import get_fundamentals

        fd = get_fundamentals(symbol)
    except Exception:
        return  # silently skip if unavailable

    # Only render if we got at least some data
    has_data = any(
        v is not None
        for v in [fd.pe_ratio, fd.forward_pe, fd.analyst_target_mean, fd.profit_margin]
    )
    if not has_data:
        return

    cols = st.columns(6)

    def _fmt(v, suffix=""):
        return f"{v:.1f}{suffix}" if v is not None else "—"

    def _fmt_pct(v):
        return f"{v * 100:.1f}%" if v is not None else "—"

    with cols[0]:
        st.metric("P/E", _fmt(fd.pe_ratio))
    with cols[1]:
        st.metric("Fwd P/E", _fmt(fd.forward_pe))
    with cols[2]:
        st.metric("PEG", _fmt(fd.peg_ratio))
    with cols[3]:
        st.metric("Profit Margin", _fmt_pct(fd.profit_margin))
    with cols[4]:
        st.metric(
            "Analyst Hedef",
            f"${fd.analyst_target_mean:.0f}" if fd.analyst_target_mean else "—",
        )
    with cols[5]:
        rec_map = {
            "buy": "🟢 Al",
            "strong_buy": "🟢 Güçlü Al",
            "hold": "🟡 Tut",
            "sell": "🔴 Sat",
            "strong_sell": "🔴 Güçlü Sat",
        }
        rec_label = rec_map.get(fd.recommendation or "", fd.recommendation or "—")
        st.metric("Tavsiye", rec_label)


# Sprint 10: Canonical re-exports so existing consumers don't break
from .components.ai_signals import (  # noqa: F401, E402
    get_drl_predictions,
    load_ai_signals,
    refresh_inference_json,
    render_ai_insights_panel,
    render_drl_signals_panel,
)

# Top Opportunity Cards
# ---------------------------------------------------------------------------


def render_top_cards(
    buyable: pd.DataFrame,
    drl_preds: dict[str, Any],
) -> None:
    """Render top 4 opportunity cards with score bars and DRL badges."""
    st.markdown("### 🔥 En Güçlü Fırsatlar (Top 4)")

    top_n = buyable.head(4)
    cols = st.columns(4)

    for i, (_idx, row) in enumerate(top_n.iterrows()):
        score = row["recommendation_score"]
        score_color = "#22c55e" if score >= 80 else "#eab308"
        symbol = row["symbol"]

        drl_info = drl_preds.get(symbol, {})
        drl_action = drl_info.get("action", "")
        drl_conf = drl_info.get("confidence", 0)
        has_ai_buy = drl_action == "BUY" and drl_conf > 0.5
        ai_badge = (
            '<span style="background: var(--color-ai); color: white; padding: 2px 6px; border-radius: var(--radius-sm); font-size: 0.7rem; margin-left: 5px;">🤖 AI</span>'
            if has_ai_buy
            else ""
        )

        with cols[i]:
            st.markdown(
                f"""
<div class="top-opportunity-card" role="article" aria-label="{symbol} fırsat kartı, skor {score:.0f}" style="background: linear-gradient(145deg, var(--bg-secondary), var(--bg-primary)); border-radius: var(--radius-md); padding: 1.5rem; border: 1px solid var(--border-default); box-shadow: var(--shadow-card); position: relative; overflow: hidden; transition: transform var(--transition-normal);">
<div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: {score_color};"></div>
<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
<div>
<h2 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: var(--text-primary);">{symbol}{ai_badge}</h2>
<span style="font-size: 0.9rem; color: var(--text-secondary);">{row.get("regime", "N/A")}</span>
</div>
<div style="text-align: right;">
<div style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary);">${row["price"]:.2f}</div>
</div>
</div>
<div style="margin-bottom: 1rem;">
<div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
<span style="font-size: 0.8rem; color: var(--text-secondary);">Sinyal Gücü</span>
<span style="font-size: 0.8rem; font-weight: 600; color: {score_color};">{score:.1f}/100</span>
</div>
<div style="width: 100%; height: 6px; background: var(--bg-tertiary); border-radius: 3px; overflow: hidden;" role="progressbar" aria-valuenow="{score:.0f}" aria-valuemin="0" aria-valuemax="100" aria-label="Sinyal gücü">
<div style="width: {score}%; height: 100%; background: {score_color}; border-radius: 3px;"></div>
</div>
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem;">
<div style="background: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: var(--radius-sm); text-align: center;">
<div style="color: var(--text-secondary); font-size: 0.7rem;">HEDEF ▲</div>
<div style="color: var(--color-success); font-weight: 600;">${row["take_profit"]:.2f}</div>
</div>
<div style="background: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: var(--radius-sm); text-align: center;">
<div style="color: var(--text-secondary); font-size: 0.7rem;">STOP ▼</div>
<div style="color: var(--color-error); font-weight: 600;">${row["stop_loss"]:.2f}</div>
</div>
</div>
</div>
""",
                unsafe_allow_html=True,
            )

            if st.button(
                "🧠 AI Analizi",
                key=f"btn_card_{row['symbol']}",
                use_container_width=True,
            ):
                st.session_state["selected_ai_symbol"] = row["symbol"]
                st.toast(f"{row['symbol']} AI Laboratuvarına aktarıldı.", icon="🤖")


# ---------------------------------------------------------------------------
# Stock Detail Card
# ---------------------------------------------------------------------------


def render_detail_card(
    row: pd.Series,
    market_avg_score: float,
) -> None:
    """Render the detailed analysis card for a selected stock."""
    edge_score = row["recommendation_score"] - market_avg_score
    edge_color = "#22c55e" if edge_score > 0 else "#ef4444"
    edge_text = f"+{edge_score:.1f}" if edge_score > 0 else f"{edge_score:.1f}"

    strategy_tag = row.get("strategy_tag", row.get("regime", "N/A"))

    st.markdown(
        f"""
    <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
            <div style="background: #3b82f6; color: white; width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;">
                {row["symbol"][0]}
            </div>
            <div>
                <h3 style="margin: 0; color: #f8fafc;">{row["symbol"]} Analiz Raporu</h3>
                <span style="color: #94a3b8; font-size: 0.9rem;">Strateji: <strong style="color: #facc15;">{strategy_tag}</strong> | Zaman: {st.session_state.get("scan_time", "Yeni")}</span>
            </div>
            <div style="margin-left: auto; text-align: right;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #22c55e;">${row["price"]:.2f}</div>
                <div style="color: #94a3b8; font-size: 0.8rem;">Anlık Fiyat</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # --- Fundamental data row ---
    _render_fundamentals_row(row["symbol"])

    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        st.markdown("#### 💡 Yapay Zeka Görüşü")
        reason = "Güçlü momentum ve pozitif trend."
        if row["recommendation_score"] > 80:
            reason = "Çok güçlü yükseliş trendi, hacim destekli ve risk düşük."
        elif row["recommendation_score"] > 60:
            reason = "Yükseliş potansiyeli var, ancak volatiliteye dikkat edilmeli."

        st.info(f"{reason}\n\n**Risk/Ödül Oranı:** {row['risk_reward']:.2f}")

        st.markdown(
            f"""
        <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-top: 10px; border-left: 4px solid {edge_color};">
            <strong style="color: #f8fafc;">🚀 FinPilot Edge:</strong>
            <span style="color: #94a3b8;">Piyasa ortalamasından</span>
            <strong style="color: {edge_color};">{edge_text} puan</strong>
            <span style="color: #94a3b8;">ayrışıyor.</span>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown("#### 🎯 Ticaret Planı")

        tp1 = row.get("tp1")
        tp2 = row.get("tp2")
        tp3 = row.get("tp3")

        if pd.notna(tp1) and pd.notna(tp2):
            st.markdown(
                f"""
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
                <span>TP1 (%50):</span> <strong style="color: #4ade80;">${tp1:.2f}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 5px;">
                <span>TP2 (%30):</span> <strong style="color: #22c55e;">${tp2:.2f}</strong>
            </div>
            """,
                unsafe_allow_html=True,
            )
            if pd.notna(tp3) and tp3 > 0:
                st.markdown(
                    f"""
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 10px;">
                    <span>TP3 (%20):</span> <strong style="color: #15803d;">🚀 Trailing Stop</strong>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; text-align: right;">(Ref: ${tp3:.2f})</div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.metric(
                "Hedef (TP)",
                f"${row['take_profit']:.2f}",
                delta=f"%{((row['take_profit'] - row['price']) / row['price'] * 100):.1f}",
                help="Take Profit: Kar alma hedef fiyatı.",
            )

        st.metric(
            "Stop (SL)",
            f"${row['stop_loss']:.2f}",
            delta=f"-%{((row['price'] - row['stop_loss']) / row['price'] * 100):.1f}",
            delta_color="inverse",
            help="Stop Loss: Zarar durdurma seviyesi.",
        )

        st.markdown("#### 📊 Teknik Göstergeler")
        st.markdown(
            f"""
        - **Rejim:** `{row.get("regime", "-")}`
        - **Volatilite:** `{row.get("atr", 0):.2f}`
        """
        )

    with c3:
        st.markdown("#### ⚡ Aksiyon")
        st.write("Bu hisse için daha derin bir araştırma yapmak ister misiniz?")
        if st.button(
            "🧠 AI Laboratuvarına Git",
            key=f"list_btn_{row['symbol']}",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["selected_ai_symbol"] = row["symbol"]
            st.toast(
                f"{row['symbol']} seçildi, AI sekmesine yönlendiriliyorsunuz...",
                icon="🚀",
            )


# NOTE: refresh_inference_json moved to views.components.ai_signals (Sprint 10).
# The re-export on line 24 ensures backward compatibility.

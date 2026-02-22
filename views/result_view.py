"""
Result View — Tab Rendering for Scanner Results
================================================

Extracted from dashboard.py (Sprint P7).
Renders the 6 main content tabs: Signals, Market, AI Lab, Performance, History, Education.
"""

from __future__ import annotations

import logging
import os

import pandas as pd
import streamlit as st
from scanner import compute_recommendation_score

from .components.export import render_export_panel
from .components.signal_tracker import render_signal_performance_tab
from .detail_view import get_drl_predictions, render_detail_card, render_top_cards
from .finsense import render_finsense_page
from .scan_history import render_scan_history_page
from .utils import get_gemini_research

logger = logging.getLogger(__name__)


def render_tabs(df: pd.DataFrame) -> None:
    """Render the 6 main content tabs."""
    st.markdown("---")
    tab_signals, tab_market, tab_ai, tab_perf, tab_history, tab_edu = st.tabs(
        [
            "🎯 Sinyaller (Action Zone)",
            "📊 Piyasa Tarayıcı",
            "🧠 AI Laboratuvarı",
            "📈 Performans & Geçmiş",
            "📋 Scanner Geçmişi",
            "🎓 FinSense Eğitim",
        ]
    )

    with tab_signals:
        _render_signal_tab(df)

    with tab_market:
        _render_market_tab(df)

    with tab_ai:
        _render_ai_lab_tab(df)

    with tab_perf:
        _render_performance_tab()

    with tab_history:
        render_scan_history_page()

    with tab_edu:
        render_finsense_page()


# ---------------------------------------------------------------------------
# TAB 1: Signals (Action Zone)
# ---------------------------------------------------------------------------


def _render_signal_tab(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("Veri yok. Lütfen taramayı çalıştırın.")
        return

    buyable = df[df["entry_ok"]].copy()

    if buyable.empty:
        st.warning(
            "Şu an kriterlere uyan aktif alım sinyali bulunmuyor. "
            "Ayarları gevşetmeyi (Agresif Mod) deneyebilirsiniz."
        )
        return

    buyable["recommendation_score"] = buyable.apply(compute_recommendation_score, axis=1)
    buyable = buyable.sort_values("recommendation_score", ascending=False)

    # Get DRL predictions for badge display
    drl_preds = get_drl_predictions(buyable["symbol"].tolist(), max_symbols=20)

    # Top Cards
    render_top_cards(buyable, drl_preds)

    # Detailed List
    st.markdown("### 📋 Tüm Alım Sinyalleri")
    st.caption("Listeden bir hisse seçerek detaylı analiz kartını görüntüleyebilirsiniz.")

    summary_df = buyable[
        ["symbol", "price", "recommendation_score", "risk_reward", "regime"]
    ].copy()
    summary_df["risk_reward"] = summary_df["risk_reward"].round(2)
    summary_df["recommendation_score"] = summary_df["recommendation_score"].round(1)

    # Market average for comparison
    if "recommendation_score" not in df.columns:
        df["recommendation_score"] = df.apply(compute_recommendation_score, axis=1)
    market_avg_score = df["recommendation_score"].mean()

    # Interactive table
    selection = st.dataframe(
        summary_df,
        column_config={
            "symbol": "Sembol",
            "price": st.column_config.NumberColumn("Fiyat", format="$%.2f"),
            "recommendation_score": st.column_config.ProgressColumn(
                "Sinyal Gücü", min_value=0, max_value=100, format="%.1f"
            ),
            "risk_reward": st.column_config.NumberColumn("Risk/Ödül", format="%.2f"),
            "regime": "Piyasa Rejimi",
        },
        use_container_width=True,
        hide_index=True,
        height=250,
        on_select="rerun",
        selection_mode="single-row",
        key="signal_list_table",
    )

    # Selection logic
    selected_symbol_detail = None
    if selection.selection.rows:
        selected_index = selection.selection.rows[0]
        selected_symbol_detail = summary_df.iloc[selected_index]["symbol"]
    elif not summary_df.empty:
        selected_symbol_detail = summary_df.iloc[0]["symbol"]

    if selected_symbol_detail:
        row = buyable[buyable["symbol"] == selected_symbol_detail].iloc[0]
        render_detail_card(row, market_avg_score)

    # Export
    st.markdown("---")
    render_export_panel(buyable)


# ---------------------------------------------------------------------------
# TAB 2: Market Scanner
# ---------------------------------------------------------------------------


def _render_market_tab(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("Veri yok.")
        return

    st.markdown("### 🔎 Tüm Piyasa Görünümü")

    search_term = st.text_input("Sembol Ara", placeholder="AAPL, TSLA...")

    market_df = df.copy()
    if search_term:
        market_df = market_df[market_df["symbol"].str.contains(search_term.upper())]

    if "recommendation_score" not in market_df.columns:
        market_df["recommendation_score"] = market_df.apply(compute_recommendation_score, axis=1)

    st.dataframe(
        market_df[
            ["symbol", "price", "recommendation_score", "entry_ok", "regime", "sentiment"]
        ],
        column_config={
            "symbol": "Sembol",
            "price": st.column_config.NumberColumn("Fiyat", format="$%.2f"),
            "recommendation_score": st.column_config.ProgressColumn(
                "Skor", min_value=0, max_value=100
            ),
            "entry_ok": st.column_config.CheckboxColumn("Al Sinyali?"),
            "regime": "Rejim",
            "sentiment": st.column_config.NumberColumn(
                "Sentiment", help="-1 (Negatif) ile +1 (Pozitif)"
            ),
        },
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# TAB 3: AI Lab
# ---------------------------------------------------------------------------


def _render_ai_lab_tab(df: pd.DataFrame) -> None:
    st.markdown("### 🧠 Yapay Zeka Araştırma Merkezi")
    st.caption("Google Gemini ve DuckDuckGo destekli derinlemesine analiz.")

    if df is None or df.empty:
        st.warning("Analiz için önce tarama yapmalısınız.")
        return

    symbol_list = df["symbol"].tolist()
    default_idx = 0
    if (
        "selected_ai_symbol" in st.session_state
        and st.session_state["selected_ai_symbol"] in symbol_list
    ):
        default_idx = symbol_list.index(st.session_state["selected_ai_symbol"])

    col_sym, col_lang = st.columns([3, 1])
    with col_sym:
        selected_ai_sym = st.selectbox(
            "Analiz edilecek hisseyi seçin:", symbol_list, index=default_idx
        )
    with col_lang:
        selected_lang = st.selectbox("Rapor Dili:", ["Türkçe", "English", "Deutsch"], index=0)

    lang_map = {"Türkçe": "tr", "English": "en", "Deutsch": "de"}

    if st.button(f"🚀 {selected_ai_sym} İçin Araştırmayı Başlat", type="primary"):
        with st.spinner("Yapay zeka interneti tarıyor ve raporu hazırlıyor..."):
            report = get_gemini_research(selected_ai_sym, language=lang_map[selected_lang])
            st.markdown("---")
            st.markdown(report)
            st.success("Analiz tamamlandı.")


# ---------------------------------------------------------------------------
# TAB 4: Performance
# ---------------------------------------------------------------------------


def _render_performance_tab() -> None:
    render_signal_performance_tab()

    with st.expander("📊 WFO Grid Search Sonuçları", expanded=False):
        wfo_path = os.path.join(os.getcwd(), "wfo_grid_search_results.csv")
        if os.path.exists(wfo_path):
            wfo_df = pd.read_csv(wfo_path)
            st.dataframe(wfo_df, use_container_width=True)
        else:
            st.info("WFO backtest sonuçları bulunamadı.")

# -*- coding: utf-8 -*-
"""
FinPilot Watchlist Component
=============================

Kullanıcı favori sembolleri yönetimi için UI bileşenleri.
Session state ile entegre çalışır.

Usage:
    from views.components.watchlist import render_watchlist_panel

    render_watchlist_panel()
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st

from core.session_state import get_session

# ============================================
# 📁 Watchlist Persistence
# ============================================

WATCHLIST_FILE = "data/watchlist.json"


def _load_watchlist_from_file() -> List[str]:
    """Load watchlist from JSON file."""
    try:
        path = Path(WATCHLIST_FILE)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("symbols", [])
    except Exception:
        pass
    return []


def _save_watchlist_to_file(symbols: List[str]) -> bool:
    """Save watchlist to JSON file."""
    try:
        path = Path(WATCHLIST_FILE)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {"symbols": symbols, "updated_at": datetime.now().isoformat()}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def initialize_watchlist() -> None:
    """Initialize watchlist from file if empty."""
    session = get_session()
    if not session.watchlist.symbols:
        saved_symbols = _load_watchlist_from_file()
        for symbol in saved_symbols:
            session.watchlist.add_symbol(symbol)


# ============================================
# 🎨 Watchlist UI Components
# ============================================


def render_watchlist_panel() -> None:
    """
    Render the main watchlist management panel.

    Includes:
    - Add symbol input
    - Current watchlist display
    - Quick actions (remove, clear)
    - Scan watchlist button
    """
    session = get_session()
    initialize_watchlist()

    st.markdown("### 📋 İzleme Listem")

    # Add symbol form
    col1, col2 = st.columns([3, 1])
    with col1:
        new_symbol = st.text_input(
            "Sembol Ekle",
            placeholder="AAPL, GOOGL, NVDA...",
            key="watchlist_add_input",
            label_visibility="collapsed",
        )
    with col2:
        add_clicked = st.button("➕ Ekle", key="watchlist_add_btn", use_container_width=True)

    if add_clicked and new_symbol:
        # Support comma-separated symbols
        symbols_to_add = [s.strip().upper() for s in new_symbol.split(",") if s.strip()]
        added = 0
        for symbol in symbols_to_add:
            if session.watchlist.add_symbol(symbol):
                added += 1

        if added > 0:
            _save_watchlist_to_file(session.watchlist.symbols)
            st.success(f"✅ {added} sembol eklendi")
            st.rerun()
        else:
            st.warning("⚠️ Sembol zaten listede veya geçersiz")

    # Display current watchlist
    if session.watchlist.symbols:
        st.markdown("---")

        # Stats row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Toplam", len(session.watchlist.symbols))
        with col2:
            if session.watchlist.last_updated:
                st.caption(f"Güncelleme: {session.watchlist.last_updated.strftime('%H:%M')}")
        with col3:
            if st.button("🗑️ Temizle", key="watchlist_clear"):
                session.watchlist.clear()
                _save_watchlist_to_file([])
                st.rerun()

        # Symbol chips
        st.markdown(
            """
            <style>
            .watchlist-chip {
                display: inline-flex;
                align-items: center;
                padding: 6px 12px;
                margin: 4px;
                background: rgba(59, 130, 246, 0.15);
                border: 1px solid rgba(59, 130, 246, 0.3);
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: 500;
                color: #93c5fd;
                cursor: pointer;
                transition: all 0.2s;
            }
            .watchlist-chip:hover {
                background: rgba(59, 130, 246, 0.25);
                border-color: rgba(59, 130, 246, 0.5);
            }
            .watchlist-chip .remove-btn {
                margin-left: 8px;
                opacity: 0.6;
            }
            .watchlist-chip .remove-btn:hover {
                opacity: 1;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Render chips with remove buttons
        cols = st.columns(4)
        for idx, symbol in enumerate(session.watchlist.symbols):
            with cols[idx % 4]:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(
                        f"<span class='watchlist-chip'>{symbol}</span>", unsafe_allow_html=True
                    )
                with col_b:
                    if st.button("✕", key=f"remove_{symbol}", help=f"{symbol} kaldır"):
                        session.watchlist.remove_symbol(symbol)
                        _save_watchlist_to_file(session.watchlist.symbols)
                        st.rerun()

        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "🔍 Watchlist'i Tara",
                key="scan_watchlist",
                use_container_width=True,
                type="primary",
            ):
                st.session_state["watchlist_scan_triggered"] = True
                st.session_state["watchlist_symbols"] = session.watchlist.symbols.copy()
        with col2:
            if st.button("📥 CSV Olarak İndir", key="export_watchlist", use_container_width=True):
                # Create CSV content
                df = pd.DataFrame({"symbol": session.watchlist.symbols})
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 İndir",
                    data=csv,
                    file_name=f"watchlist_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    key="download_watchlist",
                )
    else:
        st.info("📋 İzleme listeniz boş. Yukarıdan sembol ekleyerek başlayın.")

        # Quick add suggestions
        st.markdown("**Popüler Semboller:**")
        popular = ["AAPL", "GOOGL", "MSFT", "NVDA", "TSLA", "AMD"]
        cols = st.columns(len(popular))
        for idx, symbol in enumerate(popular):
            with cols[idx]:
                if st.button(symbol, key=f"quick_add_{symbol}"):
                    session.watchlist.add_symbol(symbol)
                    _save_watchlist_to_file(session.watchlist.symbols)
                    st.rerun()


def render_watchlist_sidebar() -> None:
    """
    Render a compact watchlist widget for the sidebar.
    """
    session = get_session()
    initialize_watchlist()

    with st.sidebar.expander("📋 İzleme Listesi", expanded=False):
        if session.watchlist.symbols:
            for symbol in session.watchlist.symbols[:10]:  # Max 10 in sidebar
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(symbol)
                with col2:
                    if st.button("✕", key=f"sb_remove_{symbol}"):
                        session.watchlist.remove_symbol(symbol)
                        _save_watchlist_to_file(session.watchlist.symbols)
                        st.rerun()

            if len(session.watchlist.symbols) > 10:
                st.caption(f"... ve {len(session.watchlist.symbols) - 10} daha")
        else:
            st.caption("Liste boş")


def get_watchlist_symbols() -> List[str]:
    """Get current watchlist symbols."""
    session = get_session()
    initialize_watchlist()
    return session.watchlist.symbols.copy()


def is_watchlist_scan_triggered() -> bool:
    """Check if watchlist scan was triggered."""
    return st.session_state.get("watchlist_scan_triggered", False)


def get_watchlist_scan_symbols() -> List[str]:
    """Get symbols for watchlist scan and clear trigger."""
    symbols = st.session_state.get("watchlist_symbols", [])
    st.session_state["watchlist_scan_triggered"] = False
    st.session_state["watchlist_symbols"] = []
    return symbols


__all__ = [
    "render_watchlist_panel",
    "render_watchlist_sidebar",
    "get_watchlist_symbols",
    "is_watchlist_scan_triggered",
    "get_watchlist_scan_symbols",
    "initialize_watchlist",
]

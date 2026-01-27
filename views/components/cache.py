# -*- coding: utf-8 -*-
"""
FinPilot Cache Utilities
========================

Streamlit caching wrappers for expensive computations.
Provides consistent caching across the application.

Usage:
    from views.components.cache import (
        cached_compute_scores,
        cached_filter_buyable,
        cached_format_dataframe,
    )

    buyable_df = cached_filter_buyable(df)
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Cache TTL settings
CACHE_TTL_SHORT = 60  # 1 minute for dynamic data
CACHE_TTL_MEDIUM = 300  # 5 minutes for computed data
CACHE_TTL_LONG = 3600  # 1 hour for static data


def _dataframe_hash(df: pd.DataFrame) -> str:
    """Generate a hash for a DataFrame for caching purposes."""
    if df is None or df.empty:
        return "empty"
    # Use shape and column names for quick hash
    return hashlib.md5(
        f"{df.shape}_{list(df.columns)}_{df.iloc[0].tolist() if len(df) > 0 else []}".encode()
    ).hexdigest()[:16]


# ============================================
# 📊 DataFrame Processing Cache
# ============================================


@st.cache_data(ttl=CACHE_TTL_MEDIUM, show_spinner=False)
def cached_compute_scores(
    df_hash: str,
    symbols: Tuple[str, ...],
    prices: Tuple[float, ...],
    entry_oks: Tuple[bool, ...],
    risk_rewards: Tuple[float, ...],
    regimes: Tuple[str, ...],
) -> pd.DataFrame:
    """
    Cached computation of recommendation scores.

    Note: Takes tuples instead of DataFrame for hashability.
    """
    # Reconstruct minimal DataFrame
    df = pd.DataFrame(
        {
            "symbol": symbols,
            "price": prices,
            "entry_ok": entry_oks,
            "risk_reward": risk_rewards,
            "regime": regimes,
        }
    )

    # Import here to avoid circular imports
    from scanner import compute_recommendation_score

    df["recommendation_score"] = df.apply(compute_recommendation_score, axis=1)
    return df[["symbol", "recommendation_score"]]


@st.cache_data(ttl=CACHE_TTL_MEDIUM, show_spinner=False)
def cached_filter_buyable(
    df_hash: str, symbols: Tuple[str, ...], entry_oks: Tuple[bool, ...], scores: Tuple[float, ...]
) -> List[str]:
    """
    Cached filtering of buyable symbols.

    Returns list of symbols that are buyable.
    """
    buyable = []
    for symbol, entry_ok, score in zip(symbols, entry_oks, scores):
        if entry_ok:
            buyable.append(symbol)
    return buyable


@st.cache_data(ttl=CACHE_TTL_LONG, show_spinner=False)
def cached_regime_color_map() -> Dict[str, str]:
    """Cached regime to color mapping."""
    return {
        "bull": "#22c55e",
        "trend": "#22c55e",
        "bear": "#ef4444",
        "range": "#eab308",
        "sideways": "#94a3b8",
        "neutral": "#94a3b8",
    }


@st.cache_data(ttl=CACHE_TTL_LONG, show_spinner=False)
def cached_score_color(score: float) -> str:
    """Cached score to color mapping."""
    if score >= 80:
        return "#22c55e"
    elif score >= 60:
        return "#eab308"
    elif score >= 40:
        return "#f97316"
    else:
        return "#ef4444"


# ============================================
# 🎨 HTML Generation Cache
# ============================================


@st.cache_data(ttl=CACHE_TTL_LONG, show_spinner=False)
def cached_badge_html(is_buy: bool, label: str = None, font_size: str = "0.75rem") -> str:
    """Cached badge HTML generation."""
    if label is None:
        label = "AL" if is_buy else "İzle"

    if is_buy:
        style = (
            "background:rgba(34,197,94,0.18); border:1px solid rgba(34,197,94,0.35); color:#4ade80;"
        )
    else:
        style = "background:rgba(148,163,184,0.18); border:1px solid rgba(148,163,184,0.35); color:#cbd5f5;"

    return (
        f'<span style="display:inline-flex; align-items:center; padding:4px 10px; '
        f"border-radius:999px; font-size:{font_size}; font-weight:600; "
        f'letter-spacing:0.04em; {style}">{label}</span>'
    )


@st.cache_data(ttl=CACHE_TTL_LONG, show_spinner=False)
def cached_progress_bar_html(
    value: float, max_value: float = 100, color: str = "#22c55e", height: str = "6px"
) -> str:
    """Cached progress bar HTML generation."""
    pct = min(100, max(0, (value / max_value) * 100))
    return f"""
    <div style="width: 100%; height: {height}; background: #334155; border-radius: 3px; overflow: hidden;">
        <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 3px;"></div>
    </div>
    """


# ============================================
# 📝 Text Processing Cache
# ============================================


@st.cache_data(ttl=CACHE_TTL_LONG, show_spinner=False)
def cached_format_number(value: float, precision: int = 2, prefix: str = "") -> str:
    """Cached number formatting."""
    if value is None:
        return "-"
    return f"{prefix}{value:.{precision}f}"


@st.cache_data(ttl=CACHE_TTL_LONG, show_spinner=False)
def cached_format_currency(value: float, currency: str = "$") -> str:
    """Cached currency formatting."""
    if value is None:
        return "-"
    return f"{currency}{value:,.2f}"


@st.cache_data(ttl=CACHE_TTL_LONG, show_spinner=False)
def cached_format_percentage(value: float, include_sign: bool = True) -> str:
    """Cached percentage formatting."""
    if value is None:
        return "-"
    if include_sign:
        sign = "+" if value >= 0 else ""
        return f"{sign}{value:.1f}%"
    return f"{value:.1f}%"


# ============================================
# 🔧 Utility Functions
# ============================================


def prepare_for_cache(df: pd.DataFrame, columns: List[str]) -> Dict[str, Tuple]:
    """
    Convert DataFrame columns to tuples for cache compatibility.

    Args:
        df: Source DataFrame
        columns: List of column names to extract

    Returns:
        Dictionary with column names as keys and tuples as values
    """
    result = {"hash": _dataframe_hash(df)}
    for col in columns:
        if col in df.columns:
            result[col] = tuple(df[col].tolist())
        else:
            result[col] = tuple()
    return result


def clear_component_cache() -> None:
    """Clear all component caches."""
    cached_compute_scores.clear()
    cached_filter_buyable.clear()
    cached_regime_color_map.clear()
    cached_score_color.clear()
    cached_badge_html.clear()
    cached_progress_bar_html.clear()
    cached_format_number.clear()
    cached_format_currency.clear()
    cached_format_percentage.clear()


__all__ = [
    # Cache TTL constants
    "CACHE_TTL_SHORT",
    "CACHE_TTL_MEDIUM",
    "CACHE_TTL_LONG",
    # DataFrame caching
    "cached_compute_scores",
    "cached_filter_buyable",
    "cached_regime_color_map",
    "cached_score_color",
    # HTML caching
    "cached_badge_html",
    "cached_progress_bar_html",
    # Text formatting
    "cached_format_number",
    "cached_format_currency",
    "cached_format_percentage",
    # Utilities
    "prepare_for_cache",
    "clear_component_cache",
]

# -*- coding: utf-8 -*-
"""
FinPilot Helper Functions
=========================
Yardımcı fonksiyonlar ve genel araçlar.
"""

import math
import re
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

# Regex patterns
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")

# Hint catalogs
REGIME_HINT_CATALOG = {
    "trend": "Trend modu: Fiyat yukarı yönlü momentumda, trend takip stratejileri avantaj sağlar.",
    "bull": "Boğa rejimi: Piyasa yükseliş eğiliminde, long stratejiler öne çıkar.",
    "bear": "Ayı rejimi: Zayıf momentum, risk azaltımı veya hedge tercih edilmeli.",
    "yan": "Yatay/sideways rejim: Net trend yok, range trade veya bekle-gör stratejisi.",
    "side": "Yatay/sideways rejim: Net trend yok, range trade veya bekle-gör stratejisi.",
}

SENTIMENT_HINT_CATALOG = {
    "positive": "Pozitif sentiment: Piyasa hissiyatı destekleyici, haber akışı güçlü.",
    "neg": "Negatif sentiment: Haber ve akış zayıf, risk iştahı düşük.",
    "bull": "Boğa sentiment: Yatırımcılar iyimser, alım iştahı yüksek.",
    "bear": "Ayı sentiment: İyimserlik sınırlı, savunma stratejisi düşünülmeli.",
    "fear": "Korku/Fear modu: Volatilite yüksek, pozisyon boyutları azaltılmalı.",
    "greed": "Greed modu: Risk iştahı yüksek, aşırı ısınma kontrol edilmeli.",
    "neutral": "Nötr sentiment: Net bir eğilim yok, teyit arayın.",
    "mixed": "Karışık sentiment: Göstergeler çelişkili, ek doğrulama gerekli.",
}


def trigger_rerun() -> None:
    """Safely trigger a rerun for Streamlit across versions."""
    rerun_callable = getattr(st, "rerun", None)
    if callable(rerun_callable):
        rerun_callable()
        return

    legacy_rerun = getattr(st, "experimental_rerun", None)
    if callable(legacy_rerun):
        legacy_rerun()


def is_advanced_view() -> bool:
    """Check if the user is in advanced view mode."""
    return st.session_state.get("view_mode", "advanced") == "advanced"


def normalize_narrative(value: Any) -> str:
    """Normalize narrative text by removing HTML artifacts and collapsing whitespace."""
    if value is None:
        return ""
    try:
        if hasattr(pd, "isna") and pd.isna(value):
            return ""
    except Exception:
        pass
    if isinstance(value, float):
        try:
            if math.isnan(value):
                return ""
        except Exception:
            pass
    text = str(value)
    if not text.strip():
        return ""
    text = dedent(text)
    normalized = text.strip()
    lower = normalized.lower()
    if lower in {"nan", "none"}:
        return ""
    normalized = HTML_TAG_RE.sub(" ", normalized)
    normalized = WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def format_decimal(value: Any, precision: int = 2, placeholder: str = "-") -> str:
    """Format numeric values defensively for UI rendering."""
    if value in (None, "", "-"):
        return placeholder
    try:
        if isinstance(value, (int, float)):
            return f"{float(value):.{precision}f}"
        if pd.isna(value):
            return placeholder
        numeric = float(value)
        return f"{numeric:.{precision}f}"
    except Exception:
        return str(value)


def _lookup_hint(value: Any, catalog: dict, default: str) -> str:
    """Lookup a hint from a catalog based on value."""
    if value in (None, ""):
        return default
    key = str(value).lower()
    for token, hint in catalog.items():
        if token in key:
            return hint
    return default


def get_regime_hint(value: Any) -> str:
    """Get a descriptive hint for a regime value."""
    return _lookup_hint(
        value,
        REGIME_HINT_CATALOG,
        "Rejim metriği, trend analizi sonucunu ve piyasa yapısını gösterir.",
    )


def get_sentiment_hint(value: Any) -> str:
    """Get a descriptive hint for a sentiment value."""
    return _lookup_hint(
        value,
        SENTIMENT_HINT_CATALOG,
        "Sentiment metriği, haber ve veri akışından türetilen piyasa hissiyatını özetler.",
    )


def detect_symbol_column(df: pd.DataFrame) -> str | None:
    """Detect the symbol column in a DataFrame."""
    cols = {c.lower(): c for c in df.columns}
    for name in ["symbol", "ticker"]:
        if name in cols:
            return cols[name]
    return None


def extract_symbols_from_df(df: pd.DataFrame) -> list[str]:
    """Extract unique symbols from a DataFrame."""
    cand = detect_symbol_column(df)
    if cand is None:
        return []
    series = df[cand].dropna().astype(str).map(lambda x: x.strip().upper())
    return [s for s in series.unique().tolist() if s]


# Badge style constants (DRY)
BADGE_STYLE_BUY = (
    "background:rgba(34,197,94,0.18); border:1px solid rgba(34,197,94,0.35); color:#4ade80;"
)
BADGE_STYLE_HOLD = (
    "background:rgba(148,163,184,0.18); border:1px solid rgba(148,163,184,0.35); color:#cbd5f5;"
)


def get_badge_style(is_buy: bool) -> str:
    """Return badge style based on buy/hold status."""
    return BADGE_STYLE_BUY if is_buy else BADGE_STYLE_HOLD


def build_badge_html(
    is_buy: bool, font_size: str = "0.75rem", buy_label: str = "AL", hold_label: str = "İzle"
) -> str:
    """Build HTML for a buy/hold badge.

    Args:
        is_buy: True for buy badge, False for hold badge
        font_size: CSS font size (default: 0.75rem)
        buy_label: Label for buy badge (default: AL)
        hold_label: Label for hold badge (default: İzle)

    Returns:
        HTML string for the badge
    """
    label = buy_label if is_buy else hold_label
    style = get_badge_style(is_buy)
    return (
        f'<span style="display:inline-flex; align-items:center; padding:4px 10px; '
        f"border-radius:999px; font-size:{font_size}; font-weight:600; "
        f'letter-spacing:0.04em; {style}">{label}</span>'
    )


def format_timestamp_display(timestamp: Any) -> str:
    """Format a timestamp for display, with safe escaping.

    Args:
        timestamp: Timestamp value (pd.Timestamp, datetime, or string)

    Returns:
        Formatted and HTML-escaped timestamp string
    """
    import datetime
    from html import escape

    if isinstance(timestamp, (pd.Timestamp, datetime.datetime)):
        display = timestamp.strftime("%Y-%m-%d %H:%M")
    else:
        display = str(timestamp) if timestamp not in (None, "", "NaT") else "-"
    return escape(display)


# ============================================
# 📋 CSV Validation
# ============================================


class CSVValidationResult:
    """CSV doğrulama sonucu."""

    def __init__(
        self, is_valid: bool, errors: list[str], warnings: list[str], df: pd.DataFrame | None = None
    ):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings
        self.df = df


def validate_csv_upload(df: pd.DataFrame) -> CSVValidationResult:
    """
    CSV dosyasını tarama için doğrular.

    Args:
        df: Yüklenen DataFrame

    Returns:
        CSVValidationResult with validation details
    """
    errors: list[str] = []
    warnings: list[str] = []

    if df is None or df.empty:
        return CSVValidationResult(False, ["CSV dosyası boş veya okunamadı."], [], None)

    # Required columns (case-insensitive)
    required_columns = {"symbol", "ticker"}
    df_columns_lower = {c.lower(): c for c in df.columns}

    symbol_col = None
    for req in required_columns:
        if req in df_columns_lower:
            symbol_col = df_columns_lower[req]
            break

    if symbol_col is None:
        errors.append(
            "'symbol' veya 'ticker' sütunu bulunamadı. CSV'de en az bir sembol sütunu gerekli."
        )
        return CSVValidationResult(False, errors, warnings, None)

    # Validate symbol format
    symbols = df[symbol_col].dropna().astype(str).str.strip().str.upper()
    invalid_symbols = symbols[~symbols.str.match(r"^[A-Z0-9\.\-]{1,10}$")]

    if len(invalid_symbols) > 0:
        warnings.append(
            f"{len(invalid_symbols)} geçersiz sembol formatı tespit edildi (örn: {invalid_symbols.head(3).tolist()})"
        )

    # Row count validation
    if len(df) > 500:
        warnings.append(f"CSV {len(df)} satır içeriyor. Performans için 500 sembol önerilir.")

    if len(df) < 1:
        errors.append("CSV'de en az 1 sembol gerekli.")
        return CSVValidationResult(False, errors, warnings, None)

    # Optional columns check
    optional_columns = {"price", "volume", "sector", "market_cap"}
    found_optional = [c for c in df.columns if c.lower() in optional_columns]
    if found_optional:
        warnings.append(f"Ek sütunlar bulundu: {found_optional}")

    # Normalize DataFrame
    df_normalized = df.copy()
    df_normalized = df_normalized.rename(columns={symbol_col: "symbol"})
    df_normalized["symbol"] = df_normalized["symbol"].astype(str).str.strip().str.upper()
    df_normalized = df_normalized[df_normalized["symbol"].str.len() > 0]
    df_normalized = df_normalized.drop_duplicates(subset=["symbol"])

    return CSVValidationResult(True, errors, warnings, df_normalized)


# ============================================
# 💀 Loading Skeleton UI
# ============================================


def render_loading_skeleton(num_cards: int = 4, card_type: str = "signal") -> None:
    """
    Yükleme sırasında placeholder skeleton kartları gösterir.

    Args:
        num_cards: Gösterilecek skeleton kart sayısı
        card_type: Kart tipi ("signal", "metric", "table")
    """
    if card_type == "signal":
        cols = st.columns(min(num_cards, 4))
        for i in range(num_cards):
            with cols[i % 4]:
                st.markdown(
                    """
<div style="background: linear-gradient(90deg, #1e293b 0%, #334155 50%, #1e293b 100%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.1);">
    <div style="height: 24px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-bottom: 12px; width: 60%;"></div>
    <div style="height: 16px; background: rgba(255,255,255,0.08); border-radius: 4px; margin-bottom: 8px; width: 40%;"></div>
    <div style="height: 16px; background: rgba(255,255,255,0.08); border-radius: 4px; margin-bottom: 8px; width: 80%;"></div>
    <div style="height: 32px; background: rgba(255,255,255,0.05); border-radius: 4px; width: 100%;"></div>
</div>
<style>
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
</style>
""",
                    unsafe_allow_html=True,
                )

    elif card_type == "metric":
        cols = st.columns(min(num_cards, 4))
        for i in range(num_cards):
            with cols[i % 4]:
                st.markdown(
                    """
<div style="background: rgba(30, 41, 59, 0.5); border-radius: 8px; padding: 1rem; border: 1px solid rgba(255,255,255,0.1);">
    <div style="height: 12px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-bottom: 8px; width: 50%;"></div>
    <div style="height: 28px; background: rgba(255,255,255,0.15); border-radius: 4px; width: 70%;"></div>
</div>
""",
                    unsafe_allow_html=True,
                )

    elif card_type == "table":
        st.markdown(
            """
<div style="background: rgba(30, 41, 59, 0.5); border-radius: 8px; padding: 1rem; border: 1px solid rgba(255,255,255,0.1);">
    <div style="display: flex; gap: 1rem; margin-bottom: 12px;">
        <div style="height: 16px; background: rgba(255,255,255,0.1); border-radius: 4px; flex: 1;"></div>
        <div style="height: 16px; background: rgba(255,255,255,0.1); border-radius: 4px; flex: 1;"></div>
        <div style="height: 16px; background: rgba(255,255,255,0.1); border-radius: 4px; flex: 1;"></div>
        <div style="height: 16px; background: rgba(255,255,255,0.1); border-radius: 4px; flex: 1;"></div>
    </div>
    <div style="display: flex; gap: 1rem; margin-bottom: 8px;">
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
    </div>
    <div style="display: flex; gap: 1rem; margin-bottom: 8px;">
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
    </div>
    <div style="display: flex; gap: 1rem;">
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
        <div style="height: 14px; background: rgba(255,255,255,0.05); border-radius: 4px; flex: 1;"></div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

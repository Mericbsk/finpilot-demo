"""
AI Signals — Single Source of Truth for AI Signal Data & Rendering
==================================================================

Sprint 10: Consolidated from duplicate code in dashboard.py and detail_view.py.
Provides: load_ai_signals, get_drl_predictions, render_ai_insights_panel,
          render_drl_signals_panel, refresh_inference_json.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DRL Integration (optional)
# ---------------------------------------------------------------------------
try:
    from drl.inference import DRLInference, has_trained_model

    DRL_AVAILABLE = True
except ImportError:
    DRL_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_INFERENCE_PATH = os.path.join(os.getcwd(), "data", "inference.json")
_STALE_THRESHOLD_HOURS = 24


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60, show_spinner=False)
def load_ai_signals() -> dict:
    """Load AI signals from inference.json with 60s memory cache."""
    try:
        with open(_INFERENCE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _get_data_age_hours(data: dict) -> float | None:
    """Return age of the oldest timestamp in data (hours), or None."""
    if not data:
        return None
    try:
        timestamps = [v.get("timestamp", "") for v in data.values() if v.get("timestamp")]
        if not timestamps:
            return None
        oldest = min(datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in timestamps)
        delta = datetime.now(UTC) - oldest
        return delta.total_seconds() / 3600
    except Exception:
        return None


def _humanize_timestamp(ts_str: str) -> str:
    """Convert ISO timestamp to 'X gün/saat önce' format."""
    if not ts_str:
        return "Bilinmiyor"
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        delta = now - dt
        days = delta.days
        hours = delta.seconds // 3600
        if days > 30:
            return f"{days} gün önce ⚠️"
        if days > 0:
            return f"{days} gün önce"
        if hours > 0:
            return f"{hours} saat önce"
        return "Az önce"
    except Exception:
        return ts_str[:16] if len(ts_str) >= 16 else ts_str


def is_data_stale(data: dict) -> bool:
    """Return True if inference data is older than _STALE_THRESHOLD_HOURS."""
    age = _get_data_age_hours(data)
    return age is not None and age > _STALE_THRESHOLD_HOURS


# ---------------------------------------------------------------------------
# DRL Predictions
# ---------------------------------------------------------------------------


def get_drl_predictions(symbols: list, max_symbols: int = 10) -> dict:
    """Generate predictions via DRL model (returns {} if unavailable)."""
    if not DRL_AVAILABLE:
        return {}

    try:
        if not has_trained_model():
            logger.info("No trained DRL model found")
            return {}

        inference = DRLInference()
        if not inference.load_model():
            return {}

        results = {}
        predictions = inference.batch_predict(symbols[:max_symbols])

        for pred in predictions:
            results[pred.symbol] = {
                "action": pred.action.name,
                "confidence": pred.confidence,
                "suggested_position": pred.suggested_position,
                "regime": pred.regime,
                "is_actionable": pred.is_actionable,
                "raw_action": pred.raw_action,
            }
        return results

    except Exception as e:
        logger.error("DRL prediction error: %s", e)
        return {}


# ---------------------------------------------------------------------------
# AI Insights Panel (renders on main dashboard)
# ---------------------------------------------------------------------------


def render_ai_insights_panel() -> None:
    """Render clickable AI signal cards on the main dashboard.

    Sprint 10: Unified from dashboard.py + detail_view.py duplicates.
    Includes stale-data guard (>24 h → red warning banner).
    """
    data = load_ai_signals()
    if not data:
        st.markdown(
            """<div class='empty-state' style='padding: 16px 20px;'>
                <span class='empty-icon' style='font-size:2rem;'>🧠</span>
                <h3>FinPilot AI Gözlemleri</h3>
                <p>AI gözlem verileri henüz mevcut değil.
                   Tarama tamamlandığında AI sinyalleri burada görünecek.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    # ── Stale data guard ─────────────────────────────────
    stale = is_data_stale(data)
    if stale:
        age_h = _get_data_age_hours(data)
        age_display = (
            f"{int(age_h)} saat" if age_h and age_h < 48 else f"{int((age_h or 0) / 24)} gün"
        )  # noqa: E501
        st.warning(
            f"⚠️ AI verileri **{age_display}** önce güncellendi. "
            "Güncel sinyaller için yeni bir tarama başlatın.",
            icon="🕒",
        )

    st.markdown("### 🧠 FinPilot AI Gözlemleri (Canlı)")
    st.caption("Bir karta tıklayarak AI Lab'da derinlemesine analiz başlatabilirsiniz.")

    cols = st.columns(len(data)) if len(data) <= 5 else st.columns(4)

    for idx, (symbol, info) in enumerate(data.items()):
        col = cols[idx % len(cols)]

        score = info.get("ai_score", 50)
        signal = info.get("signal", "HOLD")
        confidence = info.get("confidence", 0.0)
        regime = info.get("regime", "UNKNOWN")

        if signal == "BUY":
            color = "var(--color-success)"
            icon = "🟢"
            signal_class = "signal-buy"
        elif signal == "SELL":
            color = "var(--color-error)"
            icon = "🔴"
            signal_class = "signal-sell"
        else:
            color = "var(--text-muted)"
            icon = "⚪"
            signal_class = "signal-hold"

        # Stale → dim card
        opacity = "0.5" if stale else "1.0"

        with col:
            st.markdown(
                f"""
            <div class="ai-insight-card {signal_class}" role="article"
                 aria-label="{symbol} sinyal: {signal}, güven {confidence * 100:.0f}%"
                 style="border: 1px solid var(--border-default); border-radius: var(--radius-md);
                        padding: 10px; background-color: var(--bg-glass); opacity: {opacity};">
                <div style="font-weight: bold; font-size: 1.1em; color: var(--text-primary);">{symbol} {icon}</div>
                <div style="font-size: 0.9em; color: var(--text-secondary);">Fiyat: ${info.get("price", 0)}</div>
                <hr style="margin: 5px 0; border-color: var(--border-subtle);">
                <div style="display: flex; justify-content: space-between;">
                    <span>Sinyal:</span>
                    <span style="color: {color}; font-weight: bold;">{signal}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Güven:</span>
                    <span>%{confidence * 100:.0f}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Skor:</span>
                    <span>{score}/100</span>
                </div>
                <div style="font-size: 0.8em; color: var(--text-muted); margin-top: 5px;">Rejim: {regime}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"🔍 {symbol} Analiz",
                key=f"ai_card_{symbol}",
                use_container_width=True,
            ):
                st.session_state["selected_ai_symbol"] = symbol
                # Sprint 11: set query param so AI Lab tab can detect selection
                st.query_params["ai_symbol"] = symbol
                st.toast(
                    f"🧠 {symbol} seçildi — AI Laboratuvarı sekmesine gidin.",
                    icon="🧠",
                )

    raw_ts = list(data.values())[0].get("timestamp", "")
    st.caption(f"Son Yapay Zeka Analizi: {_humanize_timestamp(raw_ts)}")
    st.markdown("---")


# ---------------------------------------------------------------------------
# DRL Signals Panel
# ---------------------------------------------------------------------------


def render_drl_signals_panel(symbols: list) -> None:
    """Render DRL model buy/sell signals on the dashboard."""
    if not DRL_AVAILABLE:
        st.markdown(
            """<div class='empty-state' style='padding: 16px 20px;'>
                <span class='empty-icon' style='font-size:2rem;'>🤖</span>
                <h3>AI Trading Modeli</h3>
                <p>DRL (Deep Reinforcement Learning) modülü henüz kurulmamış.
                   Kurulduğunda burada AI alım-satım sinyalleri görünecektir.</p>
            </div>""",
            unsafe_allow_html=True,
        )
        return

    try:
        if not has_trained_model():
            return

        drl_preds = get_drl_predictions(symbols, max_symbols=20)
        if not drl_preds:
            return

        st.markdown("### 🤖 AI Trading Sinyalleri (DRL)")

        buy_signals = {
            s: p for s, p in drl_preds.items() if p["action"] == "BUY" and p["is_actionable"]
        }
        sell_signals = {
            s: p for s, p in drl_preds.items() if p["action"] == "SELL" and p["is_actionable"]
        }

        c1, c2, c3 = st.columns(3)
        c1.metric("📊 Analiz Edilen", f"{len(drl_preds)} hisse")
        c2.metric("🟢 Alım Sinyali", f"{len(buy_signals)} hisse")
        c3.metric("🔴 Satım Sinyali", f"{len(sell_signals)} hisse")

        if buy_signals:
            st.markdown("#### 🟢 AI Alım Önerileri")
            for symbol, pred in sorted(buy_signals.items(), key=lambda x: -x[1]["confidence"]):
                conf_pct = pred["confidence"] * 100
                regime = pred.get("regime", "N/A")
                pos_size = pred.get("suggested_position", 0) * 100
                st.markdown(
                    f"""
                <div style="background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3);
                     border-radius: var(--radius-sm); padding: 10px; margin-bottom: 8px; display: flex;
                     justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: var(--color-success); font-size: 1.1em;">{symbol}</strong>
                        <span style="color: var(--text-secondary); margin-left: 10px;">Rejim: {regime}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: var(--color-success); font-weight: bold;">Güven: %{conf_pct:.0f}</span>
                        <span style="color: var(--text-secondary); margin-left: 10px;">Pozisyon: %{pos_size:.0f}</span>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Aktif alım sinyali yok")

        if sell_signals:
            st.markdown("#### ▼ AI Satım Uyarıları")
            for symbol, pred in sorted(sell_signals.items(), key=lambda x: -x[1]["confidence"]):
                conf_pct = pred["confidence"] * 100
                st.markdown(
                    f"""
                <div class='drl-signal-card drl-sell' role='listitem'
                     aria-label='{symbol} satım sinyali, güven yüzde {conf_pct:.0f}'>
                    <div><strong class='signal-sell'>{symbol}</strong></div>
                    <div><span class='signal-sell'>Güven: %{conf_pct:.0f}</span></div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Aktif satış sinyali yok")

        st.markdown("---")

    except Exception as e:
        logger.warning("DRL panel render error: %s", e)


# ---------------------------------------------------------------------------
# Refresh inference.json after scan
# ---------------------------------------------------------------------------


def refresh_inference_json(df: pd.DataFrame) -> None:
    """Update inference.json from scan results, then bust cache."""
    if df is None or df.empty:
        return

    try:
        now = datetime.now(UTC).isoformat()
        top_symbols = df.head(5) if len(df) >= 5 else df

        data: dict[str, Any] = {}
        for _, row in top_symbols.iterrows():
            symbol = row.get("symbol", "")
            if not symbol:
                continue

            score = float(row.get("recommendation_score", 50))
            entry_ok = bool(row.get("entry_ok", False))

            if entry_ok and score >= 70:
                signal = "BUY"
                confidence = min(score / 100, 0.95)
            elif score <= 30:
                signal = "SELL"
                confidence = min((100 - score) / 100, 0.85)
            else:
                signal = "HOLD"
                confidence = 0.5

            data[symbol] = {
                "ai_score": score,
                "signal": signal,
                "confidence": round(confidence, 2),
                "regime": str(row.get("regime", "UNKNOWN")),
                "price": float(row.get("price", 0)),
                "timestamp": now,
            }

        if data:
            os.makedirs(os.path.dirname(_INFERENCE_PATH), exist_ok=True)
            with open(_INFERENCE_PATH, "w") as f:
                json.dump(data, f, indent=2)
            load_ai_signals.clear()
            logger.info("inference.json refreshed with %d symbols", len(data))
    except Exception as e:
        logger.warning("Failed to refresh inference.json: %s", e)

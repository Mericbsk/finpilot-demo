"""
Detail View — DRL Predictions, AI Insights, Top Cards & Detail Cards
=====================================================================

Extracted from dashboard.py (Sprint P7) to reduce file size.
Contains all HTML-heavy rendering for stock details and AI panels.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# DRL Integration
try:
    from drl.inference import DRLInference, has_trained_model

    DRL_AVAILABLE = True
except ImportError:
    DRL_AVAILABLE = False


# ---------------------------------------------------------------------------
# AI Signals (inference.json)
# ---------------------------------------------------------------------------


def load_ai_signals() -> dict:
    """AI Sinyal dosyasını yükler."""
    try:
        path = os.path.join(os.getcwd(), "data", "inference.json")
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# DRL Predictions
# ---------------------------------------------------------------------------


def get_drl_predictions(symbols: list, max_symbols: int = 10) -> dict:
    """DRL modeli ile tahminler üretir."""
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
        logger.error(f"DRL prediction error: {e}")
        return {}


# ---------------------------------------------------------------------------
# DRL Signals Panel
# ---------------------------------------------------------------------------


def render_drl_signals_panel(symbols: list) -> None:
    """Dashboard'da DRL model sinyallerini gösterir."""
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
                     border-radius: 8px; padding: 10px; margin-bottom: 8px; display: flex;
                     justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #22c55e; font-size: 1.1em;">{symbol}</strong>
                        <span style="color: #94a3b8; margin-left: 10px;">Rejim: {regime}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: #22c55e; font-weight: bold;">Güven: %{conf_pct:.0f}</span>
                        <span style="color: #94a3b8; margin-left: 10px;">Pozisyon: %{pos_size:.0f}</span>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Aktif alım sinyali yok")

        if sell_signals:
            st.markdown("#### \u25bc AI Sat\u0131m Uyar\u0131lar\u0131")
            for symbol, pred in sorted(sell_signals.items(), key=lambda x: -x[1]["confidence"]):
                conf_pct = pred["confidence"] * 100
                st.markdown(
                    f"""
                <div class='drl-signal-card drl-sell' role='listitem' aria-label='{symbol} sat\u0131m sinyali, g\u00fcven y\u00fczde {conf_pct:.0f}'>
                    <div><strong class='signal-sell'>{symbol}</strong></div>
                    <div><span class='signal-sell'>G\u00fcven: %{conf_pct:.0f}</span></div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Aktif satış sinyali yok")

        st.markdown("---")

    except Exception as e:
        logger.warning(f"DRL panel render error: {e}")


# ---------------------------------------------------------------------------
# AI Insights Panel
# ---------------------------------------------------------------------------


def render_ai_insights_panel() -> None:
    """Ana dashboard'a AI Pilot sinyallerini ekler."""
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

    st.markdown("### 🧠 FinPilot AI Gözlemleri (Canlı)")

    cols = st.columns(len(data)) if len(data) <= 5 else st.columns(4)

    for idx, (symbol, info) in enumerate(data.items()):
        col = cols[idx % len(cols)]

        score = info.get("ai_score", 50)
        signal = info.get("signal", "HOLD")
        confidence = info.get("confidence", 0.0)
        regime = info.get("regime", "UNKNOWN")

        if signal == "BUY":
            signal_class = "signal-buy"
            signal_label = "AL ▲"
        elif signal == "SELL":
            signal_class = "signal-sell"
            signal_label = "SAT ▼"
        else:
            signal_class = "signal-hold"
            signal_label = "İZLE ●"

        with col:
            st.markdown(
                f"""
            <div role='article' aria-label='{symbol} AI gözlemi, sinyal {signal}'
                 style="border: 1px solid var(--border-default); border-radius: var(--radius-md);
                        padding: 10px; background: var(--bg-glass);">
                <div style="font-weight: bold; font-size: 1.1em; color: var(--text-primary);">{symbol}</div>
                <div style="font-size: 0.9em; color: var(--text-secondary);">Fiyat: ${info.get("price", 0)}</div>
                <hr style="margin: 5px 0; border-color: var(--bg-tertiary);">
                <div style="display: flex; justify-content: space-between;">
                    <span>Sinyal:</span>
                    <span class='{signal_class}'>{signal_label}</span>
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

    st.caption(f"Son Yapay Zeka Analizi: {list(data.values())[0].get('timestamp', '')[:16]}")
    st.markdown("---")


# ---------------------------------------------------------------------------
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

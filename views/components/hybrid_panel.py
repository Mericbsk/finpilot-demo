"""Hybrid Engine Dashboard Panel — Scanner + DRL consensus view.

Sprint 13 — Item #6: Integrates the HybridEngine into the AI Lab tab,
showing side-by-side scanner vs DRL signals and consensus decisions.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# Lazy import flag
_HYBRID_AVAILABLE = False
try:
    from drl.hybrid_engine import HybridEngine, ScannerSignal

    _HYBRID_AVAILABLE = True
except ImportError:
    pass

try:
    from drl.inference import has_trained_model

    _DRL_AVAILABLE = True
except ImportError:
    _DRL_AVAILABLE = False
    has_trained_model = lambda *a, **kw: False  # noqa: E731


def _scanner_action_from_row(row: pd.Series) -> str:
    """Convert a scanner row to BUY/SELL/HOLD string."""
    if row.get("entry_ok", False):
        return "BUY"
    score = row.get("recommendation_score", 0)
    if score < 30:
        return "SELL"
    return "HOLD"


def render_hybrid_panel(df: pd.DataFrame | None) -> None:
    """Render the Hybrid Engine panel inside the AI Lab tab.

    Shows scanner vs DRL comparisons and consensus decisions for
    the top symbols from the latest scan.
    """
    st.markdown("### ⚡ Hybrid Engine — Scanner + DRL Konsensüs")

    if not _HYBRID_AVAILABLE:
        st.info("Hybrid Engine modülü yüklenemedi. (drl/hybrid_engine.py)")
        return

    if not _DRL_AVAILABLE or not has_trained_model():
        st.info("DRL modeli yüklü değil. Önce model eğitimi veya registry population gerekiyor.")
        return

    if df is None or df.empty:
        st.info("Tarama verisi yok — önce bir tarama çalıştırın.")
        return

    # Mode selector
    mode = st.radio(
        "Strateji Modu",
        ["hybrid", "scanner_only", "drl_only"],
        format_func=lambda m: {
            "hybrid": "🔀 Hibrit (Scanner + DRL)",
            "scanner_only": "📊 Sadece Scanner",
            "drl_only": "🤖 Sadece DRL",
        }[m],
        horizontal=True,
        key="hybrid_mode",
    )

    # Get the active model path from registry
    try:
        from drl.model_registry import get_registry

        registry = get_registry("models/")
        active_meta = None
        # Search all PPO models for the active one
        for m in registry.list_models(algorithm="PPO"):
            if m.is_active:
                active_meta = m
                break
        if not active_meta:
            # Fallback: get latest PPO model
            all_ppo = registry.list_models(algorithm="PPO")
            active_meta = all_ppo[0] if all_ppo else None

        if not active_meta or not active_meta.model_path:
            st.warning("Registry'de yüklenebilir model bulunamadı.")
            return

        model_path = active_meta.model_path
    except Exception as e:
        st.warning(f"Model registry hatası: {e}")
        return

    with st.spinner("Hybrid Engine başlatılıyor …"):
        try:
            engine = HybridEngine(
                model_path=model_path,
                strategy_mode=mode,
                drl_weight=0.5,
            )
        except Exception as e:
            st.error(f"Hybrid Engine başlatılamadı: {e}")
            return

    # Process top symbols
    from scanner import compute_recommendation_score

    top_df = df.copy()
    if "recommendation_score" not in top_df.columns:
        top_df["recommendation_score"] = top_df.apply(compute_recommendation_score, axis=1)
    top_df = top_df.sort_values("recommendation_score", ascending=False).head(10)

    rows: list[dict[str, Any]] = []
    agree_count = 0
    total_count = 0

    for _, row in top_df.iterrows():
        symbol = row["symbol"]
        scanner_sig = ScannerSignal(
            symbol=symbol,
            action=_scanner_action_from_row(row),
            score=int(row.get("recommendation_score", 50)),
            confidence=float(row.get("recommendation_score", 50)) / 100.0,
            reason=row.get("regime", ""),
        )

        try:
            hybrid_result = engine.process_signal(scanner_sig, pd.DataFrame())
            drl_action = (
                hybrid_result.drl_prediction.action.name if hybrid_result.drl_prediction else "N/A"
            )
            agree = hybrid_result.agreement
            if agree:
                agree_count += 1
            total_count += 1

            rows.append(
                {
                    "Sembol": symbol,
                    "Scanner": scanner_sig.action,
                    "DRL": drl_action,
                    "Konsensüs": hybrid_result.final_action,
                    "Güven": f"{hybrid_result.final_confidence:.0%}",
                    "Uyum": "✅" if agree else "⚠️",
                    "Pozisyon": f"{hybrid_result.risk_adjusted_size:.0%}",
                }
            )
        except Exception as e:
            logger.warning("Hybrid signal error %s: %s", symbol, e)
            rows.append(
                {
                    "Sembol": symbol,
                    "Scanner": scanner_sig.action,
                    "DRL": "ERR",
                    "Konsensüs": scanner_sig.action,
                    "Güven": "—",
                    "Uyum": "❌",
                    "Pozisyon": "—",
                }
            )

    if rows:
        # Summary metrics
        agree_pct = agree_count / total_count * 100 if total_count else 0
        col1, col2, col3 = st.columns(3)
        col1.metric("Sembol Sayısı", total_count)
        col2.metric("Uyum Oranı", f"{agree_pct:.0f}%")
        col3.metric("Aktif Model", active_meta.version if active_meta else "—")

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Hibrit sinyal üretilemedi.")


__all__ = ["render_hybrid_panel"]

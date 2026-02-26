"""Hybrid Engine Dashboard Panel — Scanner + DRL Ensemble consensus view.

Sprint 17 — Updated to use Ensemble Router (3 regime agents) with
fallback to single-model HybridEngine.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# Lazy import flags
_HYBRID_AVAILABLE = False
try:
    from drl.hybrid_engine import HybridEngine, ScannerSignal

    _HYBRID_AVAILABLE = True
except ImportError:
    pass

_ENSEMBLE_AVAILABLE = False
try:
    from drl.ensemble_router import get_ensemble_router

    _ENSEMBLE_AVAILABLE = True
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


def _render_ensemble_hybrid(df: pd.DataFrame) -> bool:
    """Render hybrid panel using Ensemble Router (3 agents).

    Returns True if rendered successfully, False to signal fallback.
    """
    from scanner import compute_recommendation_score

    router = get_ensemble_router()
    status = router.get_status()

    if not status.get("loaded"):
        st.warning("Ensemble Router yüklenemedi — tekil model moduna düşülüyor.")
        return False

    top_df = df.copy()
    if "recommendation_score" not in top_df.columns:
        top_df["recommendation_score"] = top_df.apply(compute_recommendation_score, axis=1)
    top_df = top_df.sort_values("recommendation_score", ascending=False).head(10)

    symbols = top_df["symbol"].tolist()
    action_map = {0: "SAT", 1: "TUT", 2: "AL"}
    action_icons = {0: "🔴", 1: "⚪", 2: "🟢"}

    try:
        ens_results = router.batch_predict(symbols)
        ens_map = {r.symbol: r for r in ens_results}
    except Exception as e:
        st.error(f"Ensemble tahmin hatası: {e}")
        return True  # Don't fallback, just show error

    rows: list[dict[str, Any]] = []
    agree_count = 0
    total_count = 0

    for _, row in top_df.iterrows():
        symbol = row["symbol"]
        scanner_action = _scanner_action_from_row(row)
        ens = ens_map.get(symbol)

        if ens:
            drl_action_str = action_map.get(ens.final_action, "?")
            drl_icon = action_icons.get(ens.final_action, "?")

            # Agreement: scanner and ensemble agree
            agree = (
                (scanner_action == "BUY" and ens.final_action == 2)
                or (scanner_action == "SELL" and ens.final_action == 0)
                or (scanner_action == "HOLD" and ens.final_action == 1)
            )
            if agree:
                agree_count += 1
            total_count += 1

            # Consensus logic
            if agree:
                consensus = scanner_action
            elif ens.final_confidence > 0.7:
                consensus = drl_action_str
            else:
                consensus = scanner_action

            rows.append(
                {
                    "Sembol": symbol,
                    "Scanner": scanner_action,
                    "Ensemble": f"{drl_icon} {drl_action_str}",
                    "Konsensüs": consensus,
                    "Güven": f"{ens.final_confidence:.0%}",
                    "Uzlaşı": f"{ens.agreement_score:.0%}",
                    "Rejim": ens.dominant_regime,
                    "Uyum": "✅" if agree else "⚠️",
                    "Pozisyon": f"{ens.suggested_position:+.2f}",
                }
            )
        else:
            rows.append(
                {
                    "Sembol": symbol,
                    "Scanner": scanner_action,
                    "Ensemble": "N/A",
                    "Konsensüs": scanner_action,
                    "Güven": "—",
                    "Uzlaşı": "—",
                    "Rejim": "—",
                    "Uyum": "❌",
                    "Pozisyon": "—",
                }
            )

    if rows:
        agree_pct = agree_count / total_count * 100 if total_count else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sembol Sayısı", total_count)
        c2.metric("Uyum Oranı", f"{agree_pct:.0f}%")
        c3.metric("Ajan Sayısı", status.get("n_agents", 0))
        c4.metric("Rejim", status.get("current_regime", "N/A"))

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.warning("Hibrit sinyal üretilemedi.")

    return True


def render_hybrid_panel(df: pd.DataFrame | None) -> None:
    """Render the Hybrid Engine panel inside the AI Lab tab.

    Uses Ensemble Router (3 regime agents) with fallback to single model.
    """
    st.markdown("### ⚡ Hybrid Engine — Scanner + Ensemble Konsensüs")

    if df is None or df.empty:
        st.info("Tarama verisi yok — önce bir tarama çalıştırın.")
        return

    # Try ensemble first
    if _ENSEMBLE_AVAILABLE and _render_ensemble_hybrid(df):
        return  # ensemble succeeded

    # Fallback to single model HybridEngine
    if not _HYBRID_AVAILABLE:
        st.info("Hybrid Engine modülü yüklenemedi. (drl/hybrid_engine.py)")
        return

    if not _DRL_AVAILABLE or not has_trained_model():
        st.info("DRL modeli yüklü değil. Önce model eğitimi gerekiyor.")
        return

    st.caption("⚠️ Ensemble Router kullanılamıyor — tekil model modu aktif.")

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
        for m in registry.list_models(algorithm="PPO"):
            if m.is_active:
                active_meta = m
                break
        if not active_meta:
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

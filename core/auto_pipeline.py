"""FinPilot Auto-Pipeline — DEPRECATED (2026-06-12).

This module's 7-phase workflow has been merged into ``core.pipeline.run_cycle``
with ``stages={"social", "bull_bear", "backtest", "synthesize"}``.

``run_auto_pipeline`` is kept as a thin shim so that any remaining call sites
continue to work until they are updated to call ``run_cycle`` directly.
"""

from __future__ import annotations

import logging
import warnings
from typing import Any

logger = logging.getLogger(__name__)


def run_auto_pipeline(
    symbols: list[str],
    kelly_fraction: float = 0.5,
    top_n: int = 5,  # noqa: ARG001 — kept for call-site compatibility
    backtest_top_n: int = 3,  # noqa: ARG001 — kept for call-site compatibility
) -> dict[str, Any]:
    """Delegate to ``core.pipeline.run_cycle`` with all stages enabled.

    .. deprecated:: 2026-06-12
        Use ``core.pipeline.run_cycle(..., stages={"social","bull_bear","backtest","synthesize"})``
        directly.  This shim exists only for backward compatibility.
    """
    warnings.warn(
        "run_auto_pipeline is deprecated; use core.pipeline.run_cycle with stages=… instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from core.pipeline import run_cycle

    state = run_cycle(
        symbols=symbols,
        task="full",
        kelly_fraction=kelly_fraction,
        stages={"social", "bull_bear", "backtest", "synthesize"},
    )
    # Back-fill synthesized_picks for call sites that read state["synthesized_picks"]
    if "synthesized_picks" not in state:
        state["synthesized_picks"] = _synthesize(state)
    return state


# ---------------------------------------------------------------------------
# Synthesizer
# ---------------------------------------------------------------------------


def _synthesize(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Combine scan, analysis, and backtest signals into a composite confidence score.

    Formula (weighted sum, clamped 0-100):
        composite = scan_score * 0.40 + llm_confidence * 0.35 + backtest_win_rate * 0.25
    """
    picks: list[dict[str, Any]] = []

    for sym in state["top_symbols"]:
        scan = state["scan_results"].get(sym, {})
        analysis = state["analysis_results"].get(sym, {})
        backtest = state["backtest_results"].get(sym, {})

        # Scan score: normalize raw 0-5 → 0-100
        raw_score = max(
            float(scan.get("finpilot_score", 0)),
            float(scan.get("composite_score", 0)),
            float(scan.get("filter_score", 0)),
        )
        scan_score = raw_score if raw_score > 5 else (raw_score / 4.0) * 100

        # LLM confidence: use latency as inverse proxy; if report exists → 70+ base
        if analysis:
            latency_ms = float(analysis.get("latency_ms", 3000))
            # 3s = 70 confidence, 1s = 90 confidence (faster = more confident provider)
            llm_confidence = max(50.0, min(95.0, 90.0 - (latency_ms / 1000) * 10))
        else:
            llm_confidence = 0.0

        # Backtest win rate (0-100)
        if backtest:
            win_rate = float(backtest.get("win_rate", 0))
            bt_confidence = min(100.0, win_rate)
        else:
            bt_confidence = 0.0

        # Weighted composite
        weights_used = _W_SCAN
        composite = scan_score * _W_SCAN
        if analysis:
            composite += llm_confidence * _W_ANALYSIS
            weights_used += _W_ANALYSIS
        if backtest:
            composite += bt_confidence * _W_BACKTEST
            weights_used += _W_BACKTEST

        # Rescale to fill 100 when some components missing
        if weights_used > 0:
            composite = min(100.0, composite / weights_used)

        signal = (
            "BUY"
            if composite >= 70 and scan.get("entry_ok")
            else "BUY"
            if composite >= 80
            else "HOLD"
            if composite >= 50
            else "CAUTION"
        )

        picks.append(
            {
                "symbol": sym,
                "composite_confidence": round(composite, 1),
                "scan_score": round(scan_score, 1),
                "llm_confidence": round(llm_confidence, 1),
                "backtest_win_rate": round(bt_confidence, 1),
                "signal": signal,
                "entry_ok": bool(scan.get("entry_ok")),
                "price": scan.get("price"),
                "stop_loss": scan.get("stop_loss"),
                "take_profit": scan.get("take_profit"),
                "risk_reward": scan.get("risk_reward"),
                "news_count": len(state["research_results"].get(sym, [])),
                "has_llm_report": bool(analysis),
            }
        )

    picks.sort(key=lambda p: p["composite_confidence"], reverse=True)
    return picks

"""FinPilot Auto-Pipeline — single-call unified analysis workflow.

Runs all analysis phases automatically without requiring the user to select
a task type.  All phases are best-effort; a failure in any phase appends to
``errors`` but does not abort subsequent phases.

Phases
------
1. Scan          — ScannerAgent (mandatory; aborts if fails)
2. Research      — ResearchAgent parallel per top-5 symbols
3. Analysis      — AnalysisAgent parallel per top-5 symbols
4. Risk          — RiskAgent per top-5 symbols
5. Backtest      — BacktestAgent top-3 symbols
6. Synthesize    — Compute composite_confidence (0-100) per symbol
7. Alert         — AlertAgent for confirmed high-confidence signals

Usage::

    from core.auto_pipeline import run_auto_pipeline

    state = run_auto_pipeline(["NVDA", "AAPL", "TSLA", ...])
    top = state["synthesized_picks"]  # list of {symbol, composite_confidence, ...}
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

logger = logging.getLogger(__name__)

# Weights for composite_confidence synthesis
_W_SCAN = 0.40
_W_ANALYSIS = 0.35
_W_BACKTEST = 0.25

# Confidence threshold above which Alert fires
_ALERT_THRESHOLD = 70.0


def run_auto_pipeline(
    symbols: list[str],
    kelly_fraction: float = 0.5,
    top_n: int = 5,
    backtest_top_n: int = 3,
) -> dict[str, Any]:
    """Execute all analysis phases and return a synthesized result.

    Returns a state dict::

        {
            "task":                "auto",
            "symbols":             list[str],
            "scan_results":        dict[symbol, ...],
            "top_symbols":         list[str],          # top_n by scan score
            "research_results":    dict[symbol, list],
            "analysis_results":    dict[symbol, {...}],
            "risk_results":        dict[symbol, {...}],
            "backtest_results":    dict[symbol, {...}],
            "synthesized_picks":   list[dict],         # sorted by composite_confidence desc
            "alerts_sent":         list[str],
            "errors":              list[str],
        }
    """
    from agents.base import AgentContext
    from agents.scanner_agent import ScannerAgent

    state: dict[str, Any] = {
        "task": "auto",
        "symbols": symbols,
        "scan_results": {},
        "top_symbols": [],
        "research_results": {},
        "analysis_results": {},
        "risk_results": {},
        "backtest_results": {},
        "synthesized_picks": [],
        "alerts_sent": [],
        "errors": [],
    }

    # ── Phase 1: Scan ────────────────────────────────────────────────────────
    try:
        ctx = AgentContext(symbols=symbols)
        result = ScannerAgent().run(ctx, kelly_fraction=kelly_fraction)
        if result.success:
            scan = result.data or {}
            ranked = sorted(
                scan.items(),
                key=lambda kv: kv[1].get("finpilot_score", kv[1].get("composite_score", 0)),
                reverse=True,
            )
            state["scan_results"] = scan
            state["top_symbols"] = [sym for sym, _ in ranked[:top_n]]
            logger.info("auto_pipeline: scan — %d symbols, top=%s", len(scan), state["top_symbols"])
        else:
            state["errors"].append(f"scan: {result.error}")
            logger.error("auto_pipeline: scan failed — aborting: %s", result.error)
            return state
    except Exception as exc:
        state["errors"].append(f"scan: {exc}")
        logger.exception("auto_pipeline: scan exception")
        return state

    top = state["top_symbols"]
    if not top:
        return state

    # ── Phase 2 + 3: Research & Analysis (parallel per symbol) ──────────────
    def _research_one(sym: str) -> tuple[str, list]:
        try:
            from agents.research_agent import ResearchAgent

            ctx = AgentContext(symbols=[sym])
            r = ResearchAgent().run(ctx)
            return sym, r.data.get(sym, []) if r.success else []
        except Exception as exc:
            logger.warning("auto_pipeline: research %s failed: %s", sym, exc)
            return sym, []

    def _analyze_one(sym: str) -> tuple[str, dict | None]:
        try:
            from agents.analysis_agent import AnalysisAgent

            ctx = AgentContext(
                symbols=[sym],
                scan_results={sym: state["scan_results"].get(sym, {})},
            )
            r = AnalysisAgent().run(ctx)
            if r.success:
                return sym, r.data.get(sym, r.data)
            state["errors"].append(f"analyze/{sym}: {r.error}")
            return sym, None
        except Exception as exc:
            logger.warning("auto_pipeline: analysis %s failed: %s", sym, exc)
            return sym, None

    with ThreadPoolExecutor(max_workers=8, thread_name_prefix="auto") as pool:
        research_futures = {pool.submit(_research_one, sym): sym for sym in top}
        analysis_futures = {pool.submit(_analyze_one, sym): sym for sym in top}

        for fut in as_completed(research_futures):
            sym, items = fut.result()
            state["research_results"][sym] = items

        for fut in as_completed(analysis_futures):
            sym, data = fut.result()
            if data is not None:
                state["analysis_results"][sym] = data

    logger.info(
        "auto_pipeline: research=%d analysis=%d symbols",
        len(state["research_results"]),
        len(state["analysis_results"]),
    )

    # ── Phase 4: Risk ────────────────────────────────────────────────────────
    try:
        from agents.risk_agent import RiskAgent

        ctx = AgentContext(symbols=top, scan_results=state["scan_results"])
        r = RiskAgent().run(ctx)
        if r.success:
            state["risk_results"] = r.data or {}
            logger.info("auto_pipeline: risk — %d symbols", len(state["risk_results"]))
        else:
            state["errors"].append(f"risk: {r.error}")
    except Exception as exc:
        state["errors"].append(f"risk: {exc}")
        logger.exception("auto_pipeline: risk exception")

    # ── Phase 5: Backtest (top-N by scan score) ──────────────────────────────
    backtest_symbols = top[:backtest_top_n]
    try:
        from agents.backtest_agent import BacktestAgent

        ctx = AgentContext(symbols=backtest_symbols, scan_results=state["scan_results"])
        r = BacktestAgent().run(ctx, strategy="momentum", initial_capital=10_000)
        if r.success:
            state["backtest_results"] = r.data or {}
            logger.info("auto_pipeline: backtest — %d symbols", len(state["backtest_results"]))
        else:
            state["errors"].append(f"backtest: {r.error}")
    except Exception as exc:
        state["errors"].append(f"backtest: {exc}")
        logger.exception("auto_pipeline: backtest exception")

    # ── Phase 6: Synthesize ──────────────────────────────────────────────────
    state["synthesized_picks"] = _synthesize(state)
    logger.info(
        "auto_pipeline: synthesized %d picks",
        len(state["synthesized_picks"]),
    )

    # ── Phase 7: Alert (composite_confidence >= threshold) ───────────────────
    high_confidence = [
        p["symbol"]
        for p in state["synthesized_picks"]
        if p.get("composite_confidence", 0) >= _ALERT_THRESHOLD
    ]
    if high_confidence:
        try:
            from agents.alert_agent import AlertAgent

            alert_scan = {
                sym: state["scan_results"][sym]
                for sym in high_confidence
                if sym in state["scan_results"]
            }
            ctx = AgentContext(symbols=high_confidence, scan_results=alert_scan)
            r = AlertAgent().run(ctx)
            if r.success:
                state["alerts_sent"] = r.data or []
                logger.info("auto_pipeline: alerts sent for %s", high_confidence)
            else:
                state["errors"].append(f"alert: {r.error}")
        except Exception as exc:
            state["errors"].append(f"alert: {exc}")
            logger.exception("auto_pipeline: alert exception")

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

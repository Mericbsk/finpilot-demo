"""FinPilot pipeline — LangGraph-free sequential CEO workflow.

Provides ``run_cycle(symbols, task, kelly_fraction)`` as a single entry point
that replaces ``get_graph().invoke({...})`` without LangGraph StateGraph overhead.

Tasks
-----
``"scan"``    — scan only (fast path, used by scheduler main cycle)
``"analyze"`` — scan → analysis on top 5 symbols
``"risk"``    — scan → risk assessment
``"full"``    — scan → analyze → risk → alert

Usage::

    from core.pipeline import run_cycle

    state = run_cycle(["AAPL", "NVDA"], task="scan")
    scan_results = state["scan_results"]  # {symbol: {...}}
    top_symbols  = state["top_symbols"]   # ["NVDA", "AAPL", ...]
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def run_cycle(
    symbols: list[str],
    task: str = "full",
    kelly_fraction: float = 0.5,
) -> dict[str, Any]:
    """Run the CEO agent pipeline without LangGraph.

    Returns a state dict compatible with the legacy LangGraph graph output::

        {
            "task":             str,
            "symbols":          list[str],
            "scan_results":     dict[str, Any],
            "top_symbols":      list[str],
            "analysis_results": dict[str, Any],
            "risk_results":     dict[str, Any],
            "alerts_sent":      list[str],
            "errors":           list[str],
        }

    On scan failure the function returns early with an ``errors`` entry.
    All subsequent steps are best-effort: a failure appends to ``errors``
    but does NOT abort remaining steps (except scan, which is mandatory).
    """
    from agents.base import AgentContext
    from agents.scanner_agent import ScannerAgent

    state: dict[str, Any] = {
        "task": task,
        "symbols": symbols,
        "scan_results": {},
        "top_symbols": [],
        "analysis_results": {},
        "risk_results": {},
        "alerts_sent": [],
        "errors": [],
    }

    # ── Step 1: Scan ────────────────────────────────────────────────────────
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
            state["top_symbols"] = [sym for sym, _ in ranked[:5]]
            logger.info(
                "pipeline: scan — %d symbols, top=%s",
                len(scan),
                state["top_symbols"],
            )
        else:
            state["errors"].append(f"scan: {result.error}")
            logger.error("pipeline: scan failed: %s", result.error)
            return state  # downstream steps are meaningless without scan data
    except Exception as exc:
        state["errors"].append(f"scan: {exc}")
        logger.exception("pipeline: scan exception")
        return state

    if task == "scan":
        return state

    # ── Step 2: Analysis (task in ["analyze", "full"]) ──────────────────────
    if task in ("analyze", "full"):
        try:
            from agents.analysis_agent import AnalysisAgent

            for sym in state["top_symbols"]:
                ctx = AgentContext(
                    symbols=[sym],
                    scan_results={sym: state["scan_results"].get(sym, {})},
                )
                r = AnalysisAgent().run(ctx)
                if r.success:
                    state["analysis_results"][sym] = r.data.get(sym, r.data)
                else:
                    state["errors"].append(f"analyze/{sym}: {r.error}")
            logger.info(
                "pipeline: analysis — %d symbols",
                len(state["analysis_results"]),
            )
        except Exception as exc:
            state["errors"].append(f"analyze: {exc}")
            logger.exception("pipeline: analysis exception")

    if task == "analyze":
        return state

    # ── Step 3: Risk ─────────────────────────────────────────────────────────
    try:
        from agents.risk_agent import RiskAgent

        ctx = AgentContext(
            symbols=state["top_symbols"] or symbols,
            scan_results=state["scan_results"],
        )
        r = RiskAgent().run(ctx)
        if r.success:
            state["risk_results"] = r.data or {}
            logger.info("pipeline: risk — %d symbols", len(state["risk_results"]))
        else:
            state["errors"].append(f"risk: {r.error}")
            logger.error("pipeline: risk failed: %s", r.error)
    except Exception as exc:
        state["errors"].append(f"risk: {exc}")
        logger.exception("pipeline: risk exception")

    if task == "risk":
        return state

    # ── Step 4: Alert (full only) ─────────────────────────────────────────────
    try:
        from agents.alert_agent import AlertAgent

        ctx = AgentContext(
            symbols=state["top_symbols"] or symbols,
            scan_results=state["scan_results"],
        )
        r = AlertAgent().run(ctx)
        if r.success:
            state["alerts_sent"] = r.data or []
            logger.info("pipeline: alerts — %s", state["alerts_sent"])
        else:
            state["errors"].append(f"alert: {r.error}")
            logger.error("pipeline: alert failed: %s", r.error)
    except Exception as exc:
        state["errors"].append(f"alert: {exc}")
        logger.exception("pipeline: alert exception")

    return state

"""CEO Agent — LangGraph StateGraph orchestrator.

Coordinates the four Tier-1 specialist agents:

    scan  →  [analyze]  →  risk  →  alert  →  END
                ↑ only when task == "full"

State machine tasks
-------------------
    "scan"    : Scanner only  (fast, ~10-30s per symbol batch)
    "analyze" : Scanner → Analysis for each symbol
    "risk"    : Scanner → Risk assessment
    "full"    : Scanner → Analysis (top 5) → Risk → Alert  (complete workflow)

Usage::

    from agents.ceo import get_graph

    result = get_graph().invoke({
        "task": "full",
        "symbols": ["AAPL", "NVDA", "KGEI"],
        "kelly_fraction": 0.5,
        ...
    })
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared state type
# ---------------------------------------------------------------------------


class FinPilotState(TypedDict, total=False):
    """State flowing through every node in the LangGraph pipeline.

    All keys are optional (``total=False``) so nodes only need to return
    the keys they update — LangGraph merges them automatically.
    """

    task: str
    symbols: list[str]
    kelly_fraction: float
    scan_results: dict[str, Any]
    analysis_results: dict[str, Any]
    risk_results: dict[str, Any]
    alerts_sent: list[str]
    errors: list[str]
    top_symbols: list[str]


# ---------------------------------------------------------------------------
# Node functions  (each returns a partial FinPilotState dict)
# ---------------------------------------------------------------------------


def _node_scan(state: FinPilotState) -> dict:
    """Run ScannerAgent on all requested symbols."""
    from agents.base import AgentContext
    from agents.scanner_agent import ScannerAgent

    ctx = AgentContext(symbols=state.get("symbols", []))
    result = ScannerAgent().run(ctx, kelly_fraction=state.get("kelly_fraction", 0.5))

    if result.success:
        scan = result.data or {}
        # CEO selects top 5 symbols by finpilot_score for deep analysis
        ranked = sorted(
            scan.items(),
            key=lambda kv: kv[1].get("finpilot_score", kv[1].get("composite_score", 0)),
            reverse=True,
        )
        top = [sym for sym, _ in ranked[:5]]
        logger.info("CEO: scan complete — %d symbols, top=%s", len(scan), top)
        return {"scan_results": scan, "top_symbols": top}

    err = f"scan: {result.error}"
    logger.error("CEO: %s", err)
    return {"errors": list(state.get("errors", [])) + [err], "scan_results": {}, "top_symbols": []}


def _node_analyze(state: FinPilotState) -> dict:
    """Run AnalysisAgent on top_symbols (deep LLM analysis)."""
    from agents.analysis_agent import AnalysisAgent
    from agents.base import AgentContext

    symbols = state.get("top_symbols", [])
    scan = state.get("scan_results", {})
    errors = list(state.get("errors", []))
    analysis: dict = {}

    for sym in symbols:
        ctx = AgentContext(symbols=[sym], scan_results={sym: scan.get(sym, {})})
        result = AnalysisAgent().run(ctx)
        if result.success:
            analysis[sym] = result.data.get(sym, result.data)
        else:
            errors.append(f"analyze/{sym}: {result.error}")

    logger.info("CEO: analysis complete — %d symbols", len(analysis))
    return {"analysis_results": analysis, "errors": errors}


def _node_risk(state: FinPilotState) -> dict:
    """Run RiskAgent on top_symbols."""
    from agents.base import AgentContext
    from agents.risk_agent import RiskAgent

    ctx = AgentContext(
        symbols=state.get("top_symbols", []) or state.get("symbols", []),
        scan_results=state.get("scan_results", {}),
    )
    result = RiskAgent().run(ctx)

    if result.success:
        logger.info("CEO: risk complete — %d symbols", len(result.data or {}))
        return {"risk_results": result.data or {}}

    err = f"risk: {result.error}"
    logger.error("CEO: %s", err)
    return {"errors": list(state.get("errors", [])) + [err], "risk_results": {}}


def _node_alert(state: FinPilotState) -> dict:
    """Run AlertAgent for entry-ok BUY signals."""
    from agents.alert_agent import AlertAgent
    from agents.base import AgentContext

    symbols = state.get("top_symbols", []) or state.get("symbols", [])
    ctx = AgentContext(symbols=symbols, scan_results=state.get("scan_results", {}))
    result = AlertAgent().run(ctx)

    if result.success:
        sent = result.data or []
        logger.info("CEO: alerts sent — %s", sent)
        return {"alerts_sent": sent}

    err = f"alert: {result.error}"
    logger.error("CEO: %s", err)
    return {"errors": list(state.get("errors", [])) + [err], "alerts_sent": []}


# ---------------------------------------------------------------------------
# Conditional routing
# ---------------------------------------------------------------------------


def _route_after_scan(state: FinPilotState) -> str:
    """After scan, branch based on task type."""
    task = state.get("task", "scan")
    if task == "scan":
        return "__end__"
    if task in ("full", "analyze"):
        return "analyze"
    return "risk"


def _route_after_risk(state: FinPilotState) -> str:
    """After risk: send alerts only for 'full' task."""
    task = state.get("task", "scan")
    if task == "full":
        return "alert"
    return "__end__"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_graph() -> Any:
    """Build and compile the FinPilot LangGraph StateGraph.

    Graph topology:
        scan ──[full/analyze]──► analyze ──► risk ──[full]──► alert ──► END
             ──[scan/risk]────────────────► risk ──[scan/risk]────────► END
    """
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise ImportError(
            "langgraph is required for the agent system. " "Install with: pip install langgraph"
        ) from exc

    g: StateGraph = StateGraph(FinPilotState)

    g.add_node("scan", _node_scan)
    g.add_node("analyze", _node_analyze)
    g.add_node("risk", _node_risk)
    g.add_node("alert", _node_alert)

    g.set_entry_point("scan")

    g.add_conditional_edges(
        "scan",
        _route_after_scan,
        {"analyze": "analyze", "risk": "risk", "__end__": END},
    )
    g.add_edge("analyze", "risk")

    g.add_conditional_edges(
        "risk",
        _route_after_risk,
        {"alert": "alert", "__end__": END},
    )
    g.add_edge("alert", END)

    return g.compile()


# ---------------------------------------------------------------------------
# Singleton graph instance
# ---------------------------------------------------------------------------

_graph: Any = None


def get_graph() -> Any:
    """Return a compiled LangGraph instance (lazy singleton)."""
    global _graph  # noqa: PLW0603
    if _graph is None:
        _graph = build_graph()
        logger.info("CEO: LangGraph workflow compiled successfully")
    return _graph

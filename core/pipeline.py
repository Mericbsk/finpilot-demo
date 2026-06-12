"""FinPilot pipeline — LangGraph-free sequential CEO workflow.

Provides ``run_cycle(symbols, task, kelly_fraction, stages)`` as a single entry point
that replaces ``get_graph().invoke({...})`` without LangGraph StateGraph overhead.

Tasks
-----
``"scan"``    — scan only (fast path, used by scheduler main cycle)
``"analyze"`` — scan → analysis on top 5 symbols
``"risk"``    — scan → risk assessment
``"full"``    — scan → analyze → risk → alert

Optional stages (set[str])
--------------------------
``"social"``     — SocialIntelligenceAgent (Reddit/HN/Polymarket sentiment)
``"bull_bear"``  — BullResearcherAgent + BearResearcherAgent in parallel (top-N only)
``"backtest"``   — BacktestAgent + composite_confidence synthesis (from auto_pipeline)
``"synthesize"`` — composite_confidence weighting (used together with "backtest")

Pass ``stages=None`` (default) to preserve original behaviour — nothing extra runs.

Usage::

    from core.pipeline import run_cycle

    # Fast scan (original)
    state = run_cycle(["AAPL", "NVDA"], task="scan")

    # Full cycle with social + debate
    state = run_cycle(["AAPL", "NVDA"], task="full",
                      stages={"social", "bull_bear"})
    state["social_results"]   # {symbol: SocialData}
    state["bull_cases"]        # {symbol: {arguments, strength_score, ...}}
    state["bear_cases"]        # {symbol: {arguments, strength_score, ...}}
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any

logger = logging.getLogger(__name__)

# ENV gate for social sentiment (mirrors ceo.py _node_social behaviour)
_SOCIAL_ENABLED = os.getenv("SOCIAL_SENTIMENT_ENABLED", "true").lower() in ("1", "true", "yes")


def _emit(cycle_id: str, symbols: list[str], agent: str, to_state: str,
          from_state: str | None = None, payload: dict | None = None,
          success: bool = True, error: str | None = None) -> None:
    """Fire-and-forget wrapper around signal_events.emit_event."""
    try:
        from core.signal_events import emit_event
        for sym in symbols:
            emit_event(
                cycle_id, sym, agent, to_state,
                from_state=from_state,
                payload=payload,
                success=success,
                error=error,
            )
    except Exception as exc:  # noqa: BLE001
        logger.debug("pipeline: _emit failed (ignored): %s", exc)


def run_cycle(
    symbols: list[str],
    task: str = "full",
    kelly_fraction: float = 0.5,
    stages: set[str] | None = None,
) -> dict[str, Any]:
    """Run the CEO agent pipeline without LangGraph.

    Parameters
    ----------
    symbols:        Ticker list to process.
    task:           ``"scan"`` | ``"analyze"`` | ``"risk"`` | ``"full"``
    kelly_fraction: Kelly criterion fraction passed to scanner.
    stages:         Optional set of extra pipeline stages to activate.
                    Supported values: ``"social"``, ``"bull_bear"``,
                    ``"backtest"``, ``"synthesize"``.
                    ``None`` (default) keeps original behaviour.

    Returns a state dict compatible with the legacy LangGraph graph output::

        {
            "task":             str,
            "symbols":          list[str],
            "scan_results":     dict[str, Any],
            "top_symbols":      list[str],
            "analysis_results": dict[str, Any],
            "research_results": dict[str, Any],
            "risk_results":     dict[str, Any],
            "alerts_sent":      list[str],
            "social_results":   dict[str, Any],   # populated when "social" in stages
            "bull_cases":       dict[str, Any],   # populated when "bull_bear" in stages
            "bear_cases":       dict[str, Any],   # populated when "bull_bear" in stages
            "composite_confidence": float | None, # populated when "synthesize" in stages
            "errors":           list[str],
        }

    On scan failure the function returns early with an ``errors`` entry.
    All subsequent steps are best-effort: a failure appends to ``errors``
    but does NOT abort remaining steps (except scan, which is mandatory).
    """
    from agents.base import AgentContext
    from agents.scanner_agent import ScannerAgent

    _stages: set[str] = set(stages) if stages else set()
    _cycle_id = f"cycle-{uuid.uuid4().hex[:12]}"

    state: dict[str, Any] = {
        "task": task,
        "symbols": symbols,
        "cycle_id": _cycle_id,
        "scan_results": {},
        "top_symbols": [],
        "analysis_results": {},
        "research_results": {},
        "risk_results": {},
        "alerts_sent": [],
        "social_results": {},
        "bull_cases": {},
        "bear_cases": {},
        "composite_confidence": None,
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
            _emit(_cycle_id, symbols, "scanner", "scan_done",
                  from_state="init",
                  payload={"n_symbols": len(scan), "top": state["top_symbols"]})
        else:
            state["errors"].append(f"scan: {result.error}")
            logger.error("pipeline: scan failed: %s", result.error)
            _emit(_cycle_id, symbols, "scanner", "scan_failed",
                  from_state="init", success=False, error=str(result.error))
            return state  # downstream steps are meaningless without scan data
    except Exception as exc:
        state["errors"].append(f"scan: {exc}")
        logger.exception("pipeline: scan exception")
        _emit(_cycle_id, symbols, "scanner", "scan_error",
              from_state="init", success=False, error=str(exc))
        return state

    if task == "scan":
        return state

    # ── Step 1b: Social Intelligence (optional — "social" in stages) ────────
    if "social" in _stages and _SOCIAL_ENABLED:
        try:
            from agents.social_intelligence_agent import SocialIntelligenceAgent

            top_for_social = state["top_symbols"] or symbols[:5]
            s_ctx = AgentContext(symbols=top_for_social)
            s_result = SocialIntelligenceAgent().run(s_ctx)
            if s_result.success:
                state["social_results"] = s_result.data or {}
                logger.info(
                    "pipeline: social — %d symbols enriched", len(state["social_results"])
                )
                _emit(_cycle_id, top_for_social, "social_intel", "social_done",
                      from_state="scan_done",
                      payload={"n": len(state["social_results"])})
            else:
                state["errors"].append(f"social: {s_result.error}")
                logger.warning("pipeline: social failed (non-fatal): %s", s_result.error)
                _emit(_cycle_id, top_for_social, "social_intel", "social_failed",
                      from_state="scan_done", success=False, error=str(s_result.error))
        except Exception as exc:
            state["errors"].append(f"social: {exc}")
            logger.warning("pipeline: social exception (non-fatal): %s", exc)

    # ── Step 1c: Bull/Bear Debate (optional — "bull_bear" in stages) ─────────
    if "bull_bear" in _stages:
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            from agents.bear_researcher import BearResearcherAgent
            from agents.bull_researcher import BullResearcherAgent

            top_for_debate = state["top_symbols"] or symbols[:5]
            debate_ctx = AgentContext(
                symbols=top_for_debate,
                scan_results=state["scan_results"],
            )
            # Merge social sentiment into scan results so researchers see it
            if state["social_results"]:
                for sym in top_for_debate:
                    soc = state["social_results"].get(sym, {})
                    if soc and sym in state["scan_results"]:
                        state["scan_results"][sym]["sentiment_score"] = soc.get(
                            "sentiment_score", 0.5
                        )

            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="debate") as pool:
                bull_fut = pool.submit(
                    BullResearcherAgent().run,
                    debate_ctx,
                    research_data=state["research_results"],
                )
                bear_fut = pool.submit(
                    BearResearcherAgent().run,
                    debate_ctx,
                    research_data=state["research_results"],
                )
                bull_result = bull_fut.result()
                bear_result = bear_fut.result()

            if bull_result.success:
                state["bull_cases"] = bull_result.data or {}
                logger.info("pipeline: bull_research — %d symbols", len(state["bull_cases"]))
                _emit(_cycle_id, top_for_debate, "bull_researcher", "bull_done",
                      from_state="scan_done",
                      payload={"n": len(state["bull_cases"])})
            else:
                state["errors"].append(f"bull_research: {bull_result.error}")
                _emit(_cycle_id, top_for_debate, "bull_researcher", "bull_failed",
                      from_state="scan_done", success=False, error=str(bull_result.error))

            if bear_result.success:
                state["bear_cases"] = bear_result.data or {}
                logger.info("pipeline: bear_research — %d symbols", len(state["bear_cases"]))
                _emit(_cycle_id, top_for_debate, "bear_researcher", "bear_done",
                      from_state="scan_done",
                      payload={"n": len(state["bear_cases"])})
            else:
                state["errors"].append(f"bear_research: {bear_result.error}")
                _emit(_cycle_id, top_for_debate, "bear_researcher", "bear_failed",
                      from_state="scan_done", success=False, error=str(bear_result.error))
        except Exception as exc:
            state["errors"].append(f"bull_bear: {exc}")
            logger.warning("pipeline: bull/bear exception (non-fatal): %s", exc)

    # ── Step 2: Analysis (task in ["analyze", "full"]) ──────────────────────
    if task in ("analyze", "full"):
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            from agents.analysis_agent import AnalysisAgent

            def _analyze_sym(sym: str) -> tuple[str, Any]:
                ctx = AgentContext(
                    symbols=[sym],
                    scan_results={sym: state["scan_results"].get(sym, {})},
                )
                r = AnalysisAgent().run(ctx)
                if r.success:
                    return sym, r.data.get(sym, r.data)
                state["errors"].append(f"analyze/{sym}: {r.error}")
                return sym, None

            with ThreadPoolExecutor(max_workers=5, thread_name_prefix="analysis") as pool:
                futures = {pool.submit(_analyze_sym, sym): sym for sym in state["top_symbols"]}
                for fut in as_completed(futures):
                    sym, result = fut.result()
                    if result is not None:
                        state["analysis_results"][sym] = result

            logger.info(
                "pipeline: analysis — %d symbols (parallel)",
                len(state["analysis_results"]),
            )
        except Exception as exc:
            state["errors"].append(f"analyze: {exc}")
            logger.exception("pipeline: analysis exception")

    if task == "analyze":
        return state

    # ── Step 2b: Research (full only — parallel with top symbols) ────────────
    if task == "full":
        try:
            from agents.research_agent import ResearchAgent

            ctx = AgentContext(symbols=state["top_symbols"] or symbols)
            r = ResearchAgent().run(ctx)
            if r.success:
                state["research_results"] = r.data or {}
                logger.info("pipeline: research — %d symbols", len(state["research_results"]))
            else:
                state["errors"].append(f"research: {r.error}")
                logger.warning("pipeline: research failed (non-fatal): %s", r.error)
        except Exception as exc:
            state["errors"].append(f"research: {exc}")
            logger.exception("pipeline: research exception (non-fatal)")

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

    # ── Step 5: Backtest + Synthesis (optional — "backtest"/"synthesize" in stages) ─
    if "backtest" in _stages:
        try:
            from agents.backtest_agent import BacktestAgent

            regime_hint = "trend"
            bt_ctx = AgentContext(
                symbols=state["top_symbols"] or symbols,
                scan_results=state["scan_results"],
                metadata={"strategy_hint": regime_hint},
            )
            bt_result = BacktestAgent().run(bt_ctx, strategy=regime_hint, initial_capital=10_000)
            if bt_result.success:
                state["backtest_results"] = bt_result.data or {}
                logger.info("pipeline: backtest — %d symbols", len(state["backtest_results"]))
            else:
                state["errors"].append(f"backtest: {bt_result.error}")
                logger.warning("pipeline: backtest failed (non-fatal): %s", bt_result.error)
        except Exception as exc:
            state["errors"].append(f"backtest: {exc}")
            logger.warning("pipeline: backtest exception (non-fatal): %s", exc)

    if "synthesize" in _stages:
        try:
            # composite_confidence: weighted blend of scan + analysis + backtest
            # Weights mirror auto_pipeline.py: scan=40%, analysis=35%, backtest=25%
            scan_scores = [
                float(v.get("finpilot_score", v.get("composite_score", 0)) or 0)
                for v in state["scan_results"].values()
            ]
            scan_avg = (sum(scan_scores) / len(scan_scores)) if scan_scores else 0.0

            analysis_scores = [
                float((v or {}).get("finpilot_score", 0) or 0)
                for v in state["analysis_results"].values()
            ]
            analysis_avg = (sum(analysis_scores) / len(analysis_scores)) if analysis_scores else 0.0

            bt_data = state.get("backtest_results", {}) or {}
            bt_scores = [
                float((v or {}).get("win_rate", 0) or 0) * 100
                for v in bt_data.values()
                if isinstance(v, dict)
            ]
            bt_avg = (sum(bt_scores) / len(bt_scores)) if bt_scores else 0.0

            composite = scan_avg * 0.40 + analysis_avg * 0.35 + bt_avg * 0.25
            state["composite_confidence"] = round(composite, 2)
            logger.info("pipeline: composite_confidence=%.2f", composite)
        except Exception as exc:
            state["errors"].append(f"synthesize: {exc}")
            logger.warning("pipeline: synthesize exception (non-fatal): %s", exc)

    return state

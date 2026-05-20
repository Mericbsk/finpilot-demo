"""Agent orchestration endpoint.

POST /api/v1/agent/run
    Run the full FinPilot multi-agent LangGraph workflow.

GET  /api/v1/agent/status
    Health check — confirms langgraph and all agents are importable.

Tasks
-----
    scan    : ScannerAgent only  (fast, suitable for quick screening)
    analyze : ScannerAgent → AnalysisAgent per symbol
    risk    : ScannerAgent → RiskAgent
    full    : ScannerAgent → AnalysisAgent (top 5) → RiskAgent → AlertAgent
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from api.middleware.auth import require_auth
from auth.tokens import TokenPayload

router = APIRouter(tags=["agent"])

# Event logging — silently no-ops if Redis is unavailable
try:
    from core.agent_events import get_recent_events as _get_events
    from core.agent_events import log_event
except Exception:  # pragma: no cover

    def log_event(*a, **kw):
        pass  # type: ignore

    def _get_events(limit=50):
        return []  # type: ignore


logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="agent")
_AGENT_TIMEOUT_SECONDS = 600  # 10 minutes — full workflow can be slow


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class AgentRunRequest(BaseModel):
    task: str = Field(
        "scan",
        description=(
            "Workflow task: 'scan' | 'analyze' | 'risk' | 'full' | "
            "'research' | 'backtest' | 'report' | "
            "'market_intel' | 'optimize' | 'monitor' | 'combo' | 'advisory'"
        ),
        pattern=r"^(scan|analyze|risk|full|research|backtest|report|market_intel|optimize|monitor|combo|advisory)$",
    )
    question: str | None = Field(None, description="Danışman sorusu (task='advisory' için)")
    advisory_key: str | None = Field(None, description="Danışman anahtar adı (cto|cpo|cmo|...)")
    symbols: list[str] = Field(default=[], max_length=100)

    @model_validator(mode="after")
    def check_symbols_for_task(self) -> AgentRunRequest:
        if self.task not in ("advisory",) and len(self.symbols) == 0:
            raise ValueError("symbols must have at least 1 item for this task")
        return self

    kelly_fraction: float = Field(0.5, ge=0.0, le=1.0)


class AgentRunResponse(BaseModel):
    task: str
    symbols_requested: int
    scan_results: dict[str, Any] = {}
    analysis_results: dict[str, Any] = {}
    risk_results: dict[str, Any] = {}
    research_results: dict[str, Any] = {}
    backtest_results: dict[str, Any] = {}
    market_intel: dict[str, Any] = {}
    optimizer_results: dict[str, Any] = {}
    monitor_results: dict[str, Any] = {}
    combo_results: dict[str, Any] = {}
    advisory_result: dict[str, Any] = {}
    report: str = ""
    alerts_sent: list[str] = []
    top_symbols: list[str] = []
    errors: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/agent/run", response_model=AgentRunResponse)
async def run_agent(req: AgentRunRequest):
    """Execute the multi-agent FinPilot workflow via LangGraph.

    Task routing:
    - **scan**    : Scanner → END
    - **analyze** : Scanner → Analysis → END
    - **risk**    : Scanner → Risk → END
    - **full**    : Scanner → Analysis (top 5) → Risk → Alert → END

    Returns merged state from all executed agents.
    """
    # Tier-2 standalone tasks (bypass LangGraph)
    if req.task in (
        "research",
        "backtest",
        "report",
        "market_intel",
        "optimize",
        "monitor",
        "combo",
        "advisory",
    ):
        from agents.base import AgentContext

        ctx = AgentContext(symbols=req.symbols)
        errors: list[str] = []

        if req.task == "research":
            import time as _time

            from agents.research_agent import ResearchAgent

            _t0 = _time.perf_counter()
            result = ResearchAgent().run(ctx)
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "research failed")
            log_event(
                "Quant Research",
                "research",
                "ok" if result.success else "error",
                _dur,
                f"{len(result.data or {})} sembol haberi",
                req.symbols,
                "strategy",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                research_results=result.data or {},
                errors=errors,
            )

        if req.task == "backtest":
            import time as _time

            from agents.backtest_agent import BacktestAgent

            _t0 = _time.perf_counter()
            result = BacktestAgent().run(ctx, strategy="momentum", initial_capital=10_000)
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "backtest failed")
            log_event(
                "Combination Testing",
                "backtest",
                "ok" if result.success else "error",
                _dur,
                f"{len(result.data or {})} sembol backtest",
                req.symbols,
                "strategy",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                backtest_results=result.data or {},
                errors=errors,
            )

        if req.task == "report":
            # report needs scan first
            import time as _time

            from agents.report_agent import ReportAgent
            from agents.scanner_agent import ScannerAgent

            _t0 = _time.perf_counter()
            scan_result = ScannerAgent().run(ctx, kelly_fraction=req.kelly_fraction)
            scan_data = scan_result.data or {}
            log_event(
                "CEO",
                "scan",
                "ok" if scan_result.success else "error",
                (_time.perf_counter() - _t0) * 1000,
                f"{len(scan_data)} sinyal tarandı",
                req.symbols,
                "management",
            )
            report_ctx = AgentContext(
                symbols=req.symbols,
                scan_results=scan_data,
            )
            _t0 = _time.perf_counter()
            result = ReportAgent().run(report_ctx)
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "report failed")
            rd = result.data or {}
            log_event(
                "Documentation",
                "report",
                "ok" if result.success else "error",
                _dur,
                f"{len(rd.get('report',''))} karakter rapor",
                req.symbols,
                "ops",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                scan_results=scan_data,
                report=rd.get("report", ""),
                errors=errors,
            )

        if req.task == "market_intel":
            import time as _time

            from agents.market_intelligence import MarketIntelligenceAgent

            _t0 = _time.perf_counter()
            result = MarketIntelligenceAgent().run(ctx, lookback_days=30, use_llm=True)
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "market_intel failed")
            rd = result.data or {}
            log_event(
                "Market Intelligence",
                "regime_detection",
                "ok" if result.success else "error",
                _dur,
                rd.get("market_summary", "")[:120],
                req.symbols,
                "strategy",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                market_intel=rd,
                errors=errors,
            )

        if req.task == "optimize":
            import time as _time

            from agents.strategy_optimizer import StrategyOptimizerAgent

            _t0 = _time.perf_counter()
            result = StrategyOptimizerAgent().run(ctx, strategy="momentum", method="grid")
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "optimize failed")
            rd = result.data or {}
            log_event(
                "Strategy Optimizer",
                "grid_optimize",
                "ok" if result.success else "error",
                _dur,
                f"{len(rd)} sembol optimize edildi",
                req.symbols,
                "strategy",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                optimizer_results=rd,
                errors=errors,
            )

        if req.task == "monitor":
            import time as _time

            from agents.performance_monitor import PerformanceMonitorAgent

            _t0 = _time.perf_counter()
            result = PerformanceMonitorAgent().run(ctx, warn_drawdown_pct=10, stop_drawdown_pct=20)
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "monitor failed")
            rd = result.data or {}
            log_event(
                "Performance Monitor",
                "drawdown_check",
                "ok" if result.success else "error",
                _dur,
                rd.get("summary", "")[:120],
                req.symbols,
                "quality",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                monitor_results=rd,
                errors=errors,
            )

        if req.task == "combo":
            import time as _time

            from agents.combo_testing import ComboTestingAgent

            _t0 = _time.perf_counter()
            result = ComboTestingAgent().run(ctx, strategies=["momentum", "trend"])
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "combo failed")
            rd = result.data or {}
            log_event(
                "Combination Testing",
                "combo_matrix",
                "ok" if result.success else "error",
                _dur,
                rd.get("summary", "")[:120],
                req.symbols,
                "strategy",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                combo_results=rd,
                errors=errors,
            )

        if req.task == "advisory":
            import time as _time

            from agents.advisory import advisory_agent_for

            key = req.advisory_key or "cto"
            question = req.question or "FinPilot'u nasıl geliştirebiliriz?"
            _t0 = _time.perf_counter()
            try:
                agent = advisory_agent_for(key)
                result = agent.run(ctx, question=question)
            except ValueError as exc:
                return AgentRunResponse(
                    task=req.task,
                    symbols_requested=len(req.symbols),
                    errors=[str(exc)],
                )
            _dur = (_time.perf_counter() - _t0) * 1000
            if not result.success:
                errors.append(result.error or "advisory failed")
            rd = result.data or {}
            log_event(
                rd.get("role", key),
                "advisory",
                "ok" if result.success else "error",
                _dur,
                question[:80],
                req.symbols,
                "management",
            )
            return AgentRunResponse(
                task=req.task,
                symbols_requested=len(req.symbols),
                advisory_result=rd,
                errors=errors,
            )

    try:
        from agents.ceo import get_graph
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"Agent system unavailable: {exc}") from exc

    initial_state: dict[str, Any] = {
        "task": req.task,
        "symbols": req.symbols,
        "kelly_fraction": req.kelly_fraction,
        "scan_results": {},
        "analysis_results": {},
        "risk_results": {},
        "alerts_sent": [],
        "errors": [],
        "top_symbols": [],
    }

    import time as _time

    _t0 = _time.perf_counter()
    loop = asyncio.get_running_loop()
    try:
        final_state: dict[str, Any] = await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: get_graph().invoke(initial_state)),
            timeout=_AGENT_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        log_event(
            "CEO",
            req.task,
            "error",
            _AGENT_TIMEOUT_SECONDS * 1000,
            "Timeout",
            req.symbols,
            "management",
        )
        raise HTTPException(
            status_code=504,
            detail=f"Agent workflow timed out after {_AGENT_TIMEOUT_SECONDS}s",
        ) from None
    except Exception as exc:
        logger.exception("Agent workflow error: %s", exc)
        log_event(
            "CEO",
            req.task,
            "error",
            (_time.perf_counter() - _t0) * 1000,
            str(exc)[:120],
            req.symbols,
            "management",
        )
        raise HTTPException(
            status_code=500, detail=f"Agent error: {type(exc).__name__}: {exc}"
        ) from exc

    _dur = (_time.perf_counter() - _t0) * 1000
    _scan_cnt = len(final_state.get("scan_results", {}))
    _alerts = final_state.get("alerts_sent", [])
    log_event(
        "CEO",
        req.task,
        "ok",
        _dur,
        f"{_scan_cnt} sinyal, {len(_alerts)} alert, task={req.task}",
        req.symbols,
        "management",
    )

    # Persist CEO results to shared state so Scheduler pipeline can consume them
    try:
        from core.agent_state import save_agent_result as _save

        if final_state.get("scan_results"):
            _save("scan", req.symbols, final_state["scan_results"])
        if final_state.get("analysis_results"):
            _save("analyze", req.symbols, final_state["analysis_results"])
    except Exception:
        pass  # shared state is best-effort

    return AgentRunResponse(
        task=final_state.get("task", req.task),
        symbols_requested=len(req.symbols),
        scan_results=final_state.get("scan_results", {}),
        analysis_results=final_state.get("analysis_results", {}),
        risk_results=final_state.get("risk_results", {}),
        research_results=final_state.get("research_results", {}),
        backtest_results=final_state.get("backtest_results", {}),
        report=final_state.get("report", ""),
        alerts_sent=final_state.get("alerts_sent", []),
        top_symbols=final_state.get("top_symbols", []),
        errors=final_state.get("errors", []),
    )


@router.get("/agent/status")
def agent_status():
    """Return agent system health — importability of all core components."""
    checks: dict[str, str] = {}

    # langgraph
    try:
        import langgraph  # noqa: F401

        checks["langgraph"] = "ok"
    except ImportError:
        checks["langgraph"] = "missing — pip install langgraph"

    # agent modules
    for module in (
        "agents.base",
        "agents.ceo",
        "agents.scanner_agent",
        "agents.analysis_agent",
        "agents.risk_agent",
        "agents.alert_agent",
        "agents.research_agent",
        "agents.backtest_agent",
        "agents.report_agent",
        "agents.market_intelligence",
        "agents.strategy_optimizer",
        "agents.performance_monitor",
        "agents.combo_testing",
        "agents.advisory",
        "core.scheduler",
    ):
        try:
            __import__(module)
            checks[module] = "ok"
        except Exception as exc:
            checks[module] = f"error: {exc}"

    healthy = all(v == "ok" for v in checks.values())
    return {"healthy": healthy, "checks": checks}


@router.get("/agent/registry")
def agent_registry():
    """Return the full 23-agent registry with layer groupings and status counts."""
    try:
        from agents.registry import registry_as_dict

        return registry_as_dict()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agent/events")
def agent_events(limit: int = 50):
    """Return recent agent-run events from the Redis activity stream."""
    events = _get_events(limit=min(limit, 200))
    return {"events": events, "count": len(events)}


@router.get("/agent/scheduler")
def agent_scheduler_status():
    """Return current scheduler state (running, cycle count, last run)."""
    try:
        from core.scheduler import scheduler_status

        return scheduler_status()
    except Exception as exc:
        return {"running": False, "error": str(exc)}


@router.post("/agent/scheduler/start")
def agent_scheduler_start(
    symbols: list[str],
    interval_minutes: int = 60,
    _auth: Annotated[TokenPayload, Depends(require_auth)] = ...,
):
    """Start the background scheduler with the given symbols and interval."""
    try:
        from core.scheduler import start_scheduler

        started = start_scheduler(symbols=symbols, interval_minutes=interval_minutes)
        return {"started": started, "symbols": symbols, "interval_minutes": interval_minutes}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/agent/scheduler/stop")
def agent_scheduler_stop(
    _auth: Annotated[TokenPayload, Depends(require_auth)] = ...,
):
    """Stop the background scheduler."""
    try:
        from core.scheduler import stop_scheduler

        stopped = stop_scheduler()
        return {"stopped": stopped}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agent/kpis")
def agent_kpis():
    """Return current KPI summary (win rate, profit factor, signal counts, recent cycle scores)."""
    try:
        from core.kpi_tracker import get_cycle_scores, get_kpis, get_recent_signals

        return {
            "kpis": get_kpis(),
            "recent_signals": get_recent_signals(limit=10),
            "cycle_scores": get_cycle_scores(n=10),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agent/self-eval")
def agent_self_eval():
    """Return the most recent self-evaluation score and recommendations."""
    try:
        from core.kpi_tracker import get_cycle_scores

        scores = get_cycle_scores(n=1)
        if not scores:
            return {"score": None, "message": "Henüz cycle çalıştırılmadı"}
        return scores[0]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agent/eval/latest")
def agent_eval_latest(symbols: list[str] = Query(default=["THYAO.IS", "KCHOL.IS"])):
    """Return the latest autonomous eval harness report saved in shared state."""
    try:
        from core.agent_state import get_agent_result
        from core.scheduler import scheduler_status

        report = get_agent_result("eval", symbols)
        status = scheduler_status()
        if report is None:
            return {
                "available": False,
                "eval_last_run": status.get("eval_last_run"),
                "message": "Henüz eval çalıştırılmadı",
            }
        return {"available": True, "eval_last_run": status.get("eval_last_run"), "report": report}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/agent/feedback")
def agent_emit_feedback(
    from_agent: str,
    to_agent: str,
    feedback_type: str,
    data: dict[str, Any] | None = None,
    _auth: Annotated[TokenPayload, Depends(require_auth)] = ...,
):
    """Emit a feedback message from one agent to another."""
    try:
        from agents.feedback import emit_feedback

        emit_feedback(
            from_agent=from_agent,
            to_agent=to_agent,
            feedback_type=feedback_type,
            data=data or {},
        )
        return {"ok": True, "from": from_agent, "to": to_agent, "feedback_type": feedback_type}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agent/feedback/{agent_name}")
def agent_get_feedback(agent_name: str, limit: int = 10, peek: bool = False):
    """Return pending feedback messages for the given agent (consumed unless peek=True)."""
    try:
        from agents.feedback import get_feedback, peek_feedback

        messages = peek_feedback(agent_name, limit) if peek else get_feedback(agent_name, limit)
        return {"agent": agent_name, "messages": messages, "count": len(messages)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/agent/cycle")
async def run_agent_cycle(
    symbols: list[str],
    run_optimizer: bool = False,
    _auth: Annotated[TokenPayload, Depends(require_auth)] = ...,
):
    """Run one full agent cycle (market_intel → research → backtest → monitor) synchronously."""
    loop = asyncio.get_running_loop()
    try:
        from core.scheduler import run_cycle_once

        result = await asyncio.wait_for(
            loop.run_in_executor(
                _executor, lambda: run_cycle_once(symbols=symbols, run_optimizer=run_optimizer)
            ),
            timeout=_AGENT_TIMEOUT_SECONDS,
        )
        return result
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Cycle timed out") from None
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

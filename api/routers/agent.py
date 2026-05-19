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
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["agent"])
logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="agent")
_AGENT_TIMEOUT_SECONDS = 600  # 10 minutes — full workflow can be slow


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class AgentRunRequest(BaseModel):
    task: str = Field(
        "scan",
        description="Workflow task: 'scan' | 'analyze' | 'risk' | 'full'",
        pattern="^(scan|analyze|risk|full)$",
    )
    symbols: list[str] = Field(..., min_length=1, max_length=100)
    kelly_fraction: float = Field(0.5, ge=0.0, le=1.0)


class AgentRunResponse(BaseModel):
    task: str
    symbols_requested: int
    scan_results: dict[str, Any] = {}
    analysis_results: dict[str, Any] = {}
    risk_results: dict[str, Any] = {}
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

    loop = asyncio.get_running_loop()
    try:
        final_state: dict[str, Any] = await asyncio.wait_for(
            loop.run_in_executor(_executor, lambda: get_graph().invoke(initial_state)),
            timeout=_AGENT_TIMEOUT_SECONDS,
        )
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Agent workflow timed out after {_AGENT_TIMEOUT_SECONDS}s",
        ) from None
    except Exception as exc:
        logger.exception("Agent workflow error: %s", exc)
        raise HTTPException(
            status_code=500, detail=f"Agent error: {type(exc).__name__}: {exc}"
        ) from exc

    return AgentRunResponse(
        task=final_state.get("task", req.task),
        symbols_requested=len(req.symbols),
        scan_results=final_state.get("scan_results", {}),
        analysis_results=final_state.get("analysis_results", {}),
        risk_results=final_state.get("risk_results", {}),
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
    ):
        try:
            __import__(module)
            checks[module] = "ok"
        except Exception as exc:
            checks[module] = f"error: {exc}"

    healthy = all(v == "ok" for v in checks.values())
    return {"healthy": healthy, "checks": checks}

"""Paper execution gateway operations."""

from __future__ import annotations

import os
from typing import Any

from auth.database import get_database
from execution.gateway import ExecutionGateway
from execution.models import ExecutionMode
from execution.reconciliation import ReconciliationWorker
from execution.repository import ExecutionRepository
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.middleware.auth import require_auth

router = APIRouter(tags=["execution"], dependencies=[Depends(require_auth)])


class ScannerSignal(BaseModel):
    """Scanner contract accepted by the gateway; unknown research fields are retained."""

    model_config = ConfigDict(extra="allow")

    symbol: str = Field(..., min_length=1, max_length=10)
    environment: str = Field("paper", pattern=r"^(paper|live)$")
    timestamp: str
    price: float = Field(..., gt=0)
    position_size: float = Field(..., gt=0)
    selection_eligible: bool = False
    execution_feasible: bool = False
    direction: bool | str = True
    stop_loss: float | None = Field(None, gt=0)
    take_profit: float | None = Field(None, gt=0)
    position_cap_reject_reason: str | None = None
    scanner_run_id: str | None = None
    strategy_id: str | None = None
    strategy_version: str | None = None


class KillSwitchRequest(BaseModel):
    enabled: bool
    reason: str = Field("operator", max_length=500)


def _repository() -> ExecutionRepository:
    return ExecutionRepository(get_database())


def _broker_or_none():
    mode = ExecutionMode(os.getenv("FINPILOT_EXECUTION_MODE", "dry_run"))
    if mode != ExecutionMode.PAPER_EXECUTION:
        return None, mode
    try:
        from broker import AlpacaBroker
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Alpaca broker is unavailable") from exc
    broker = AlpacaBroker()
    if not broker.is_available:
        raise HTTPException(status_code=503, detail="Paper Alpaca credentials are not configured")
    return broker, mode


@router.post("/execution/signals")
def submit_signal(signal: ScannerSignal) -> dict[str, Any]:
    broker, mode = _broker_or_none()
    gateway = ExecutionGateway(_repository(), broker=broker, mode=mode)
    return gateway.submit_signal(signal.model_dump())


@router.get("/execution/status")
def execution_status() -> dict[str, Any]:
    repository = _repository()
    controls = repository.kill_switch()
    open_intents = repository.list_open_intents()
    return {
        "mode": os.getenv("FINPILOT_EXECUTION_MODE", "dry_run"),
        "kill_switch": controls,
        "open_intents": len(open_intents),
        "intents": open_intents,
    }


@router.post("/execution/kill-switch")
def set_kill_switch(request: KillSwitchRequest) -> dict[str, Any]:
    repository = _repository()
    repository.set_kill_switch(request.enabled, request.reason)
    repository.append_event(
        "risk.kill_switch_enabled" if request.enabled else "risk.kill_switch_disabled",
        "paper-execution",
        request.model_dump(),
    )
    return repository.kill_switch()


@router.post("/execution/reconcile")
def reconcile() -> dict[str, Any]:
    broker, mode = _broker_or_none()
    if mode != ExecutionMode.PAPER_EXECUTION or broker is None:
        raise HTTPException(status_code=409, detail="Reconciliation requires paper_execution mode")
    return ReconciliationWorker(_repository(), broker).run_once()

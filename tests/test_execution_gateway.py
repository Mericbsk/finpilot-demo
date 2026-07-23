"""Focused safety tests for the paper execution gateway."""

from __future__ import annotations

from unittest.mock import Mock

from auth.database import Database
from execution.gateway import ExecutionGateway
from execution.models import ExecutionMode
from execution.repository import ExecutionRepository

SIGNAL = {
    "scanner_run_id": "scan-001",
    "symbol": "AAPL",
    "timestamp": "2026-07-23T14:30:00Z",
    "selection_eligible": True,
    "execution_feasible": True,
    "direction": True,
    "price": 100.0,
    "stop_loss": 95.0,
    "take_profit": 110.0,
    "position_size": 10,
    "position_cap_reject_reason": None,
    "composite_score": 80,
}


def _gateway(tmp_path, broker=None, mode=ExecutionMode.DRY_RUN):
    db = Database(str(tmp_path / "execution.db"))
    return ExecutionGateway(ExecutionRepository(db), broker=broker, mode=mode)


def test_dry_run_is_idempotent_and_does_not_call_broker(tmp_path):
    broker = Mock()
    gateway = _gateway(tmp_path, broker=broker)

    first = gateway.submit_signal(SIGNAL)
    second = gateway.submit_signal(SIGNAL)

    assert first["intent_id"] == second["intent_id"]
    assert first["status"] == "created"
    broker.place_buy_order.assert_not_called()


def test_kill_switch_blocks_paper_submission(tmp_path):
    broker = Mock()
    gateway = _gateway(tmp_path, broker=broker, mode=ExecutionMode.PAPER_EXECUTION)
    gateway.repository.set_kill_switch(True, "manual test")

    result = gateway.submit_signal(SIGNAL)

    assert result["status"] == "risk_rejected"
    assert "kill_switch" in result["rejection_reason"]
    broker.place_buy_order.assert_not_called()


def test_invalid_scanner_contract_is_persisted_as_rejection(tmp_path):
    broker = Mock()
    gateway = _gateway(tmp_path, broker=broker, mode=ExecutionMode.PAPER_EXECUTION)
    invalid = {**SIGNAL, "execution_feasible": False}

    result = gateway.submit_signal(invalid)

    assert result["status"] == "risk_rejected"
    assert "execution_not_feasible" in result["rejection_reason"]
    broker.place_buy_order.assert_not_called()


def test_live_environment_is_rejected_and_never_submitted(tmp_path):
    broker = Mock()
    gateway = _gateway(tmp_path, broker=broker, mode=ExecutionMode.PAPER_EXECUTION)

    result = gateway.submit_signal({**SIGNAL, "environment": "live"})

    assert result["status"] == "risk_rejected"
    assert "environment_must_be_paper" in result["rejection_reason"]
    broker.place_buy_order.assert_not_called()


def test_paper_submission_records_order(tmp_path):
    broker = Mock()
    broker.place_buy_order.return_value = {
        "order_id": "alpaca-001",
        "status": "accepted",
        "symbol": "AAPL",
    }
    gateway = _gateway(tmp_path, broker=broker, mode=ExecutionMode.PAPER_EXECUTION)

    result = gateway.submit_signal(SIGNAL)

    assert result["status"] == "submitted"
    assert result["alpaca_order_id"] == "alpaca-001"
    broker.place_buy_order.assert_called_once()

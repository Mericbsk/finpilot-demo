"""Focused reconciliation tests."""

from __future__ import annotations

from unittest.mock import Mock

from auth.database import Database
from execution.gateway import ExecutionGateway
from execution.models import ExecutionMode
from execution.reconciliation import ReconciliationWorker
from execution.repository import ExecutionRepository

from tests.test_execution_gateway import SIGNAL


def test_reconciliation_updates_filled_order(tmp_path):
    db = Database(str(tmp_path / "execution.db"))
    repository = ExecutionRepository(db)
    broker = Mock()
    broker.place_buy_order.return_value = {"order_id": "alpaca-001", "status": "accepted"}
    gateway = ExecutionGateway(repository, broker=broker, mode=ExecutionMode.PAPER_EXECUTION)
    intent = gateway.submit_signal(SIGNAL)

    broker.get_orders.return_value = [
        {
            "order_id": intent["alpaca_order_id"],
            "status": "filled",
            "filled_qty": 10,
            "filled_avg_price": 100.25,
        }
    ]
    result = ReconciliationWorker(repository, broker).run_once()

    stored = repository.get_intent(intent["intent_id"])
    assert result["updated"] == 1
    assert stored["status"] == "filled"
    assert stored["filled_qty"] == 10
    assert stored["filled_price"] == 100.25


def test_reconciliation_marks_missing_order_unknown(tmp_path):
    db = Database(str(tmp_path / "execution.db"))
    repository = ExecutionRepository(db)
    broker = Mock()
    broker.place_buy_order.return_value = {"order_id": "alpaca-002", "status": "accepted"}
    gateway = ExecutionGateway(repository, broker=broker, mode=ExecutionMode.PAPER_EXECUTION)
    intent = gateway.submit_signal({**SIGNAL, "symbol": "MSFT"})
    broker.get_orders.return_value = []

    result = ReconciliationWorker(repository, broker).run_once()

    assert result["unknown"] == 1
    assert repository.get_intent(intent["intent_id"])["status"] == "unknown"

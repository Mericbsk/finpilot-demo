"""REST reconciliation for paper orders and local execution intents."""

from __future__ import annotations

from typing import Any, Protocol

from execution.models import IntentStatus
from execution.repository import ExecutionRepository


class ReconciliationBroker(Protocol):
    def get_orders(self, status: str = "all") -> list[dict[str, Any]]: ...


class ReconciliationWorker:
    """Make local intent state converge to the broker's observed order state."""

    STATUS_MAP = {
        "new": IntentStatus.SUBMITTED.value,
        "accepted": IntentStatus.ACCEPTED.value,
        "pending_new": IntentStatus.SUBMITTED.value,
        "partially_filled": IntentStatus.PARTIALLY_FILLED.value,
        "filled": IntentStatus.FILLED.value,
        "canceled": IntentStatus.CANCELED.value,
        "expired": IntentStatus.EXPIRED.value,
        "rejected": IntentStatus.REJECTED.value,
    }

    def __init__(self, repository: ExecutionRepository, broker: ReconciliationBroker):
        self.repository = repository
        self.broker = broker

    def run_once(self) -> dict[str, int]:
        """Reconcile all open local intents against Alpaca's closed/open snapshot."""
        broker_orders = self.broker.get_orders(status="all")
        by_order_id = {str(order.get("order_id")): order for order in broker_orders}
        counters = {"checked": 0, "updated": 0, "unknown": 0}

        for intent in self.repository.list_open_intents():
            counters["checked"] += 1
            order_id = intent.get("alpaca_order_id")
            if not order_id or str(order_id) not in by_order_id:
                self.repository.update_intent(
                    intent["intent_id"],
                    status=IntentStatus.UNKNOWN.value,
                    last_error="order_not_found_in_broker_snapshot",
                )
                self.repository.append_event(
                    "reconciliation.order_missing",
                    intent["intent_id"],
                    {"alpaca_order_id": order_id},
                    intent["signal_id"],
                )
                counters["unknown"] += 1
                continue

            order = by_order_id[str(order_id)]
            status = self.STATUS_MAP.get(str(order.get("status", "")).lower())
            if not status:
                continue
            changed = self.repository.update_intent(
                intent["intent_id"],
                status=status,
                filled_qty=order.get("filled_qty"),
                filled_price=order.get("filled_avg_price"),
                last_error=None,
            )
            if changed:
                self.repository.append_event(
                    "reconciliation.order_updated",
                    intent["intent_id"],
                    order,
                    intent["signal_id"],
                )
                counters["updated"] += 1

        self.repository.append_event("reconciliation.completed", "paper-execution", counters)
        return counters

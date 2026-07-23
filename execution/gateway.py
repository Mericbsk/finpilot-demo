"""Safety-first scanner-to-paper-order gateway."""

from __future__ import annotations

import hashlib
import os
from typing import Any, Protocol

from execution.models import ExecutionMode, IntentStatus
from execution.repository import ExecutionRepository


class BrokerProtocol(Protocol):
    def place_buy_order(self, **kwargs: Any) -> dict[str, Any]: ...


class ExecutionRejected(ValueError):
    """Raised when a signal cannot pass the execution contract."""


class ExecutionGateway:
    """Convert scanner contracts into durable, idempotent paper intents."""

    def __init__(
        self,
        repository: ExecutionRepository,
        broker: BrokerProtocol | None = None,
        mode: ExecutionMode | str | None = None,
    ):
        self.repository = repository
        self.broker = broker
        self.mode = ExecutionMode(mode or os.getenv("FINPILOT_EXECUTION_MODE", "dry_run"))
        if self.mode == ExecutionMode.PAPER_EXECUTION and broker is None:
            raise ValueError("paper_execution requires an Alpaca broker")

    @staticmethod
    def _signal_id(signal: dict[str, Any]) -> str:
        raw = "|".join(
            str(signal.get(key, ""))
            for key in (
                "environment",
                "scanner_run_id",
                "symbol",
                "timestamp",
                "strategy_id",
                "strategy_version",
            )
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _validate(self, signal: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        if signal.get("environment", "paper") != "paper":
            reasons.append("environment_must_be_paper")
        if not signal.get("selection_eligible"):
            reasons.append("selection_not_eligible")
        if not signal.get("execution_feasible"):
            reasons.append("execution_not_feasible")
        if signal.get("position_cap_reject_reason"):
            reasons.append(str(signal["position_cap_reject_reason"]))
        if (
            str(signal.get("direction", "BUY")).upper() not in {"BUY", "LONG", "TRUE"}
            and signal.get("direction") is not True
        ):
            reasons.append("only_long_buy_supported")
        try:
            if float(signal.get("price", 0)) <= 0:
                reasons.append("invalid_entry_price")
            if float(signal.get("position_size", 0)) <= 0:
                reasons.append("invalid_position_size")
        except (TypeError, ValueError):
            reasons.append("invalid_numeric_signal_fields")
        return reasons

    def submit_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        """Create or reuse an intent, then optionally submit it to paper Alpaca."""
        symbol = str(signal.get("symbol", "")).upper().strip()
        if not symbol:
            raise ExecutionRejected("missing_symbol")
        signal = {**signal, "symbol": symbol}
        if "environment" not in signal:
            signal["environment"] = "paper"
        signal_id = self._signal_id(signal)
        key = f"paper:{signal_id}:entry:v1"
        existing = self.repository.get_by_idempotency_key(key)
        if existing:
            return existing

        reasons = self._validate(signal)
        intent = {
            "intent_id": signal_id,
            "signal_id": signal_id,
            "scanner_run_id": signal.get("scanner_run_id"),
            "idempotency_key": key,
            "environment": "paper",
            "symbol": symbol,
            "side": "buy",
            "qty": float(signal.get("position_size", 0) or 0),
            "order_type": "limit" if signal.get("price") else "market",
            "limit_price": float(signal["price"]) if signal.get("price") else None,
            "stop_price": signal.get("stop_loss"),
            "take_profit": signal.get("take_profit"),
            "strategy_id": signal.get("strategy_id", signal.get("ranking_method", "scanner")),
            "strategy_version": signal.get("strategy_version", "scanner-contract-v1"),
            "status": IntentStatus.RISK_REJECTED.value if reasons else IntentStatus.CREATED.value,
            "rejection_reason": ",".join(reasons) if reasons else None,
            "payload": signal,
        }
        stored = self.repository.create_intent(intent)
        self.repository.append_event(
            "risk.rejected" if reasons else "order.intent_created",
            signal_id,
            {"reasons": reasons, "mode": self.mode.value},
            signal_id,
        )
        if reasons or self.mode in {ExecutionMode.DRY_RUN, ExecutionMode.PAPER_SHADOW}:
            return stored

        controls = self.repository.kill_switch()
        if controls.get("enabled"):
            self.repository.update_intent(
                signal_id,
                status=IntentStatus.RISK_REJECTED.value,
                rejection_reason=f"kill_switch:{controls.get('reason', '')}",
            )
            self.repository.append_event("risk.kill_switch_blocked", signal_id, controls, signal_id)
            return self.repository.get_intent(signal_id) or stored

        self.repository.update_intent(signal_id, status=IntentStatus.RISK_APPROVED.value)
        self.repository.append_event(
            "risk.approved", signal_id, {"mode": self.mode.value}, signal_id
        )
        try:
            result = self.broker.place_buy_order(
                symbol=symbol,
                qty=int(float(signal["position_size"])),
                limit_price=signal.get("price"),
                stop_loss=signal.get("stop_loss"),
                take_profit=signal.get("take_profit"),
                time_in_force="day",
                client_order_id=f"finpilot-paper-{signal_id[:24]}-entry",
            )
        except Exception as exc:
            self.repository.update_intent(
                signal_id,
                status=IntentStatus.UNKNOWN.value,
                last_error=str(exc)[:500],
            )
            self.repository.append_event(
                "order.submit_unknown", signal_id, {"error": str(exc)}, signal_id
            )
            return self.repository.get_intent(signal_id) or stored

        self.repository.update_intent(
            signal_id,
            status=IntentStatus.SUBMITTED.value,
            alpaca_order_id=result.get("order_id"),
        )
        self.repository.append_event("order.submitted", signal_id, result, signal_id)
        return self.repository.get_intent(signal_id) or stored

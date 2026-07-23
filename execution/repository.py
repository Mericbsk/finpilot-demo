"""SQLite persistence for execution intents, events, and safety controls."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from auth.database import Database


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ExecutionRepository:
    """Durable, idempotent repository for the execution gateway."""

    def __init__(self, db: Database):
        self.db = db
        self.db.initialize()

    def create_intent(self, intent: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO execution_intents
                (intent_id, signal_id, scanner_run_id, idempotency_key, environment,
                 symbol, side, qty, order_type, limit_price, stop_price, take_profit,
                 strategy_id, strategy_version, status, rejection_reason, payload,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intent["intent_id"],
                    intent["signal_id"],
                    intent.get("scanner_run_id"),
                    intent["idempotency_key"],
                    intent["environment"],
                    intent["symbol"],
                    intent["side"],
                    intent["qty"],
                    intent["order_type"],
                    intent.get("limit_price"),
                    intent.get("stop_price"),
                    intent.get("take_profit"),
                    intent.get("strategy_id"),
                    intent.get("strategy_version"),
                    intent["status"],
                    intent.get("rejection_reason"),
                    json.dumps(intent.get("payload", {}), default=str),
                    now,
                    now,
                ),
            )
            row = conn.execute(
                "SELECT * FROM execution_intents WHERE idempotency_key = ?",
                (intent["idempotency_key"],),
            ).fetchone()
        return dict(row)

    def get_by_idempotency_key(self, key: str) -> dict[str, Any] | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM execution_intents WHERE idempotency_key = ?", (key,)
            ).fetchone()
        return dict(row) if row else None

    def get_intent(self, intent_id: str) -> dict[str, Any] | None:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM execution_intents WHERE intent_id = ?", (intent_id,)
            ).fetchone()
        return dict(row) if row else None

    def update_intent(self, intent_id: str, **values: Any) -> bool:
        statements = {
            "status": "UPDATE execution_intents SET status = ? WHERE intent_id = ?",
            "alpaca_order_id": "UPDATE execution_intents SET alpaca_order_id = ? WHERE intent_id = ?",
            "client_order_id": "UPDATE execution_intents SET client_order_id = ? WHERE intent_id = ?",
            "filled_qty": "UPDATE execution_intents SET filled_qty = ? WHERE intent_id = ?",
            "filled_price": "UPDATE execution_intents SET filled_price = ? WHERE intent_id = ?",
            "rejection_reason": "UPDATE execution_intents SET rejection_reason = ? WHERE intent_id = ?",
            "updated_at": "UPDATE execution_intents SET updated_at = ? WHERE intent_id = ?",
            "last_error": "UPDATE execution_intents SET last_error = ? WHERE intent_id = ?",
        }
        updates = {key: value for key, value in values.items() if key in statements}
        if not updates:
            return False
        updates["updated_at"] = _now()
        with self.db.connection() as conn:
            changed = False
            for key, value in updates.items():
                cursor = conn.execute(statements[key], (value, intent_id))
                changed = changed or cursor.rowcount > 0
        return changed

    def append_event(
        self,
        event_type: str,
        entity_id: str,
        payload: dict[str, Any] | None = None,
        signal_id: str | None = None,
    ) -> int:
        with self.db.connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO execution_events
                (event_type, entity_id, signal_id, payload, occurred_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_type, entity_id, signal_id, json.dumps(payload or {}, default=str), _now()),
            )
            return int(cursor.lastrowid)

    def set_kill_switch(self, enabled: bool, reason: str = "") -> None:
        with self.db.connection() as conn:
            conn.execute(
                """
                INSERT INTO execution_controls (control_key, enabled, reason, updated_at)
                VALUES ('kill_switch', ?, ?, ?)
                ON CONFLICT(control_key) DO UPDATE SET
                    enabled = excluded.enabled,
                    reason = excluded.reason,
                    updated_at = excluded.updated_at
                """,
                (int(enabled), reason, _now()),
            )

    def kill_switch(self) -> dict[str, Any]:
        with self.db.connection() as conn:
            row = conn.execute(
                "SELECT * FROM execution_controls WHERE control_key = 'kill_switch'"
            ).fetchone()
        return dict(row) if row else {"control_key": "kill_switch", "enabled": 0, "reason": ""}

    def list_open_intents(self, limit: int = 500) -> list[dict[str, Any]]:
        with self.db.connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM execution_intents
                WHERE status IN ('created', 'risk_approved', 'submitted', 'accepted',
                                 'partially_filled', 'unknown')
                ORDER BY created_at ASC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

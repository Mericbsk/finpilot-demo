"""Faz 3 (Kontrollü Otonomi): append-only audit log of autonomous decisions.

Records every promote/rollback/threshold-change/approval as a JSONL line so
operators can later trace what the system did and why.

Storage: JSONL file at logs/autonomy_audit.jsonl plus an in-memory ring (last
200 entries) for cheap API reads. Redis mirroring is best-effort.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOG_PATH = Path(os.getenv("FINPILOT_AUDIT_LOG", "logs/autonomy_audit.jsonl"))
_RING_SIZE = 200
_ring: deque[dict[str, Any]] = deque(maxlen=_RING_SIZE)
_lock = threading.Lock()


def record(
    actor: str,
    action: str,
    decision: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append an audit entry.

    Args:
        actor: who/what initiated (e.g. 'scheduler', 'calibration_gate', 'user:admin').
        action: what was attempted (e.g. 'calibration.refit', 'pending.approve').
        decision: outcome label (e.g. 'promoted', 'rejected', 'queued').
        payload: free-form JSON-safe context.
    """
    entry = {
        "ts": time.time(),
        "actor": actor,
        "action": action,
        "decision": decision,
        "payload": payload or {},
    }
    with _lock:
        _ring.append(entry)
        try:
            _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with _LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as exc:
            logger.debug("audit_log: disk write failed: %s", exc)
    logger.info("AUDIT %s/%s -> %s", actor, action, decision)
    return entry


def recent(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_ring)
    return items[-limit:][::-1]


def reset_for_tests() -> None:
    with _lock:
        _ring.clear()

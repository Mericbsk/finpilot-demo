"""Faz 3 (Kontrollü Otonomi): pending-actions queue.

Risky autonomous decisions (calibration promote with large delta, threshold
change, retraining promote) get enqueued here instead of being applied
directly. An operator (or automated approver) calls approve(id) / reject(id)
to flush them. Audit log records every transition.

Storage: in-memory dict keyed by uuid, optionally mirrored to redis.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any, Callable

from core import audit_log

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_pending: dict[str, dict[str, Any]] = {}
# Registered apply-fn per action kind. Plug-in on import where needed.
_appliers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}


def register_applier(
    kind: str, fn: Callable[[dict[str, Any]], dict[str, Any]]
) -> None:
    """Wire a callback that knows how to apply an approved action of `kind`."""
    _appliers[kind] = fn


def enqueue(
    kind: str,
    payload: dict[str, Any],
    *,
    requested_by: str = "scheduler",
    reason: str = "",
) -> dict[str, Any]:
    """Queue a new pending action and return its envelope."""
    pid = uuid.uuid4().hex[:12]
    entry = {
        "id": pid,
        "kind": kind,
        "payload": payload,
        "requested_by": requested_by,
        "reason": reason,
        "status": "pending",
        "created_at": time.time(),
        "decided_at": None,
        "decided_by": None,
        "result": None,
    }
    with _lock:
        _pending[pid] = entry
    audit_log.record(
        actor=requested_by,
        action=f"pending.enqueue:{kind}",
        decision="queued",
        payload={"id": pid, "reason": reason, "data": payload},
    )
    return entry


def list_pending(include_decided: bool = False) -> list[dict[str, Any]]:
    with _lock:
        items = list(_pending.values())
    if not include_decided:
        items = [e for e in items if e["status"] == "pending"]
    return sorted(items, key=lambda e: e["created_at"], reverse=True)


def get(pid: str) -> dict[str, Any] | None:
    with _lock:
        return _pending.get(pid)


def approve(pid: str, *, decided_by: str = "user") -> dict[str, Any]:
    with _lock:
        entry = _pending.get(pid)
        if entry is None:
            raise KeyError(f"unknown pending action: {pid}")
        if entry["status"] != "pending":
            raise ValueError(f"action {pid} already {entry['status']}")
        entry["status"] = "approved"
        entry["decided_at"] = time.time()
        entry["decided_by"] = decided_by

    applier = _appliers.get(entry["kind"])
    result: dict[str, Any]
    if applier is None:
        result = {"applied": False, "reason": f"no applier for {entry['kind']}"}
    else:
        try:
            result = applier(entry["payload"]) or {"applied": True}
        except Exception as exc:
            result = {"applied": False, "error": str(exc)}
            logger.exception("pending_actions: applier failed for %s", pid)

    with _lock:
        entry["result"] = result

    audit_log.record(
        actor=f"user:{decided_by}",
        action=f"pending.approve:{entry['kind']}",
        decision="applied" if result.get("applied") else "apply_failed",
        payload={"id": pid, "result": result},
    )
    return entry


def reject(
    pid: str, *, decided_by: str = "user", reason: str = ""
) -> dict[str, Any]:
    with _lock:
        entry = _pending.get(pid)
        if entry is None:
            raise KeyError(f"unknown pending action: {pid}")
        if entry["status"] != "pending":
            raise ValueError(f"action {pid} already {entry['status']}")
        entry["status"] = "rejected"
        entry["decided_at"] = time.time()
        entry["decided_by"] = decided_by
        entry["result"] = {"applied": False, "reason": reason or "rejected"}
    audit_log.record(
        actor=f"user:{decided_by}",
        action=f"pending.reject:{entry['kind']}",
        decision="rejected",
        payload={"id": pid, "reason": reason},
    )
    return entry


def reset_for_tests() -> None:
    with _lock:
        _pending.clear()

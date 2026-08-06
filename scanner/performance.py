"""Optional observation-only scanner stage timing."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

_LOCK = threading.Lock()
_EVENTS: list[dict[str, Any]] = []


def enabled() -> bool:
    """Return whether stage timing was explicitly enabled for this process."""
    return os.getenv("FINPILOT_SCAN_STAGE_TIMING", "0") == "1"


def reset() -> None:
    """Clear the current scan's in-memory stage events."""
    with _LOCK:
        _EVENTS.clear()


def record(
    stage: str,
    elapsed_s: float,
    *,
    count: int | None = None,
    timeframe: str | None = None,
    path: str | None = None,
    outcome: str | None = None,
) -> None:
    """Record one stage event when opt-in timing is enabled."""
    if not enabled():
        return
    event: dict[str, Any] = {"stage": stage, "elapsed_s": round(elapsed_s, 6)}
    for key, value in (
        ("count", count),
        ("timeframe", timeframe),
        ("path", path),
        ("outcome", outcome),
    ):
        if value is not None:
            event[key] = value
    with _LOCK:
        _EVENTS.append(event)


@contextmanager
def timer(
    stage: str,
    *,
    count: int | None = None,
    timeframe: str | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Measure a block without changing its return value or exceptions."""
    if not enabled():
        yield
        return
    started = time.perf_counter()
    outcome = "ok"
    try:
        yield
    except Exception:
        outcome = "error"
        raise
    finally:
        record(
            stage,
            time.perf_counter() - started,
            count=count,
            timeframe=timeframe,
            path=path,
            outcome=outcome,
        )


def snapshot() -> list[dict[str, Any]]:
    """Return a copy of the current scan's stage events."""
    with _LOCK:
        return [dict(event) for event in _EVENTS]

"""GET /api/v1/history — Signal history from the database + inference cache."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(tags=["history"])

_INFERENCE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "inference.json"


def _load_inference() -> dict:
    """Load inference cache JSON (fallback)."""
    if _INFERENCE_PATH.exists():
        return json.loads(_INFERENCE_PATH.read_text())
    return {}


@router.get("/history/signals")
def get_signal_history(days: int = Query(14, ge=1, le=90)):
    """Return recent signals from the DB. Falls back to inference cache if DB is empty."""
    from auth.database import Database, SignalRepository

    db = Database()
    repo = SignalRepository(db)
    signals = repo.get_recent(limit=days * 20)

    if signals:
        return {"source": "database", "count": len(signals), "signals": signals}

    # Fallback: return inference cache as "latest" signals
    cache = _load_inference()
    flat: list[dict] = []
    for sym, data in cache.items():
        flat.append({"symbol": sym, **data})
    return {"source": "inference_cache", "count": len(flat), "signals": flat}


@router.get("/history/stats")
def get_signal_stats():
    """Aggregate signal statistics."""
    from auth.database import Database, SignalRepository

    db = Database()
    repo = SignalRepository(db)
    return repo.get_stats()


@router.get("/history/inference")
def get_inference_cache():
    """Return the latest DRL inference results."""
    return _load_inference()

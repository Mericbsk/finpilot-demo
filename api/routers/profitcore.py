"""ProfitCore metrics endpoint — serves data/profitcore_audit.json verbatim."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["profitcore"])

_AUDIT_PATH = Path(__file__).resolve().parents[2] / "data" / "profitcore_audit.json"


@router.get("/profitcore/metrics")
def profitcore_metrics() -> dict:
    """Return the latest profitcore audit metrics."""
    if not _AUDIT_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="profitcore_audit.json missing — run scripts/profitcore_audit.py",
        )
    try:
        return json.loads(_AUDIT_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"audit read failed: {exc}") from exc

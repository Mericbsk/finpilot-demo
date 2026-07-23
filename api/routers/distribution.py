"""Public, validated distribution snapshot endpoints."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from distribution.scan_contract import expected_universe
from distribution.schema import demo_view, validate_snapshot
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["distribution"])


@router.get("/distribution/snapshot")
def distribution_snapshot():
    """Return today's validated public snapshot for web consumers."""
    dist_dir = Path(os.getenv("FINPILOT_DIST_DIR", "data/distribution"))
    path = dist_dir / "snapshot_en_latest.json"
    if not path.exists():
        path = dist_dir / "snapshot_latest.json"
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=503, detail=f"snapshot unavailable: {exc}") from exc

    problems = validate_snapshot(snapshot)
    if problems:
        raise HTTPException(
            status_code=503,
            detail={"error": "snapshot invalid", "problems": problems},
        )

    today = datetime.now(tz=ZoneInfo("Europe/Vienna")).date().isoformat()
    if snapshot.get("date") != today or int(snapshot.get("universe") or 0) < expected_universe():
        raise HTTPException(
            status_code=409,
            detail={
                "error": "snapshot stale_or_incomplete",
                "snapshot_date": snapshot.get("date"),
                "snapshot_universe": snapshot.get("universe"),
                "expected_date": today,
                "expected_universe": expected_universe(),
            },
        )
    return demo_view(snapshot, max_candidates=len(snapshot.get("candidates", [])))

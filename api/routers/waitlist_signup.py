"""POST /api/v1/waitlist — Public email waitlist sign-up."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(tags=["waitlist"])
logger = logging.getLogger(__name__)

_WAITLIST_PATH = Path("data") / "waitlist_signups.json"
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_MAX_SIGNUPS = 10_000


class WaitlistRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=254)
    source: str = Field("landing", max_length=50)


def _load() -> list[dict]:
    if _WAITLIST_PATH.exists():
        try:
            return json.loads(_WAITLIST_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save(entries: list[dict]) -> None:
    _WAITLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    _WAITLIST_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


@router.post("/waitlist", status_code=201)
def join_waitlist(body: WaitlistRequest):
    """Add an email to the waitlist. Idempotent — re-joining returns 200."""
    email = body.email.strip().lower()

    if not _EMAIL_RE.match(email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address.",
        )

    entries = _load()

    # Idempotency — already in list
    existing = next((e for e in entries if e.get("email") == email), None)
    if existing:
        position = next(
            (i + 1 for i, e in enumerate(entries) if e.get("email") == email), len(entries)
        )
        return {"status": "already_registered", "position": position}

    if len(entries) >= _MAX_SIGNUPS:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Waitlist is full.",
        )

    entries.append(
        {
            "email": email,
            "source": body.source,
            "signed_up_at": datetime.now(UTC).isoformat(),
        }
    )
    _save(entries)

    logger.info("Waitlist signup: email=<redacted> source=%s total=%d", body.source, len(entries))
    return {"status": "ok", "position": len(entries)}


@router.get("/waitlist/count")
def waitlist_count():
    """Return public waitlist count (no auth required)."""
    return {"count": len(_load())}

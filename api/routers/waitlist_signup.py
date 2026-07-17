"""POST /api/v1/waitlist — Public email waitlist sign-up."""

from __future__ import annotations

import json
import logging
import os
import re
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
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
    utm: str = Field("", max_length=200)


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


def _notify_waitlist_signup(email: str, source: str) -> None:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    if not smtp_host or not smtp_password:
        logger.warning("Waitlist email notification skipped: SMTP is not configured")
        return

    smtp_user = os.getenv("SMTP_USER", "finpilot@finpilot.at").strip()
    notify_to = os.getenv("WAITLIST_NOTIFY_TO", "finpilot@finpilot.at").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    message = EmailMessage()
    message["Subject"] = "New FinPilot waitlist signup"
    message["From"] = smtp_user
    message["To"] = notify_to
    message.set_content(
        f"A new visitor joined the FinPilot waitlist.\n\nEmail: {email}\nSource: {source}\n"
    )

    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)


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

    # Dual-write to the distribution SQLite store (canonical going forward;
    # JSON file kept for backwards compatibility with existing tooling).
    try:
        from distribution.store import add_waitlist

        add_waitlist(email, source=body.source, utm=body.utm)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("waitlist sqlite dual-write failed: %s", exc)

    try:
        _notify_waitlist_signup(email, body.source)
    except Exception as exc:  # pragma: no cover - notification must not break signup
        logger.warning("waitlist email notification failed: %s", exc)

    logger.info("Waitlist signup: email=<redacted> source=%s total=%d", body.source, len(entries))
    return {"status": "ok", "position": len(entries)}


@router.get("/waitlist/count")
def waitlist_count():
    """Return public waitlist count (no auth required)."""
    return {"count": len(_load())}

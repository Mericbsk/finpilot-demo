"""Public demo feedback endpoints (Demo Spec §7 — 3-question form + micro polls).

Part of the small 'public API' profile (feedback, waitlist, stripe webhook)
that is safe to expose on the internet.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["demo-feedback"])
logger = logging.getLogger(__name__)


class DemoFeedbackRequest(BaseModel):
    session_id: str = Field("", max_length=64)
    q1: str = Field("", max_length=2000, description="Kendi cümlenle: bu ürün ne işe yarıyor?")
    q2: str = Field("", max_length=2000, description="En yararlı / en kafa karıştıran")
    q3: str = Field("", max_length=10, description="yes | maybe | no")
    q3_why: str = Field("", max_length=1000)
    micro: str = Field("", max_length=1000, description="JSON: mikro anket cevapları")
    source: str = Field("demo", max_length=50)


@router.post("/demo/feedback", status_code=201)
def submit_demo_feedback(body: DemoFeedbackRequest):
    from distribution.store import add_demo_feedback

    if not (body.q1 or body.q2 or body.q3 or body.micro):
        return {"status": "ignored", "reason": "empty"}
    fid = add_demo_feedback(body.model_dump())
    logger.info("demo feedback saved id=%s q3=%s source=%s", fid, body.q3, body.source)

    # Best-effort Telegram admin ping (never breaks the request) — so new
    # feedback is noticed immediately instead of sitting unseen in the DB.
    # notify_admin() returns False (no raise) when the bot is unconfigured.
    try:
        from distribution.telegram_client import notify_admin

        pay = {"yes": "✅ öder", "maybe": "🤔 belki", "no": "❌ ödemez"}.get(
            body.q3.strip().lower(), body.q3 or "-"
        )
        snippet = (body.q1 or body.q2 or "").strip().replace("\n", " ")[:180]
        notify_admin(
            f"📝 Yeni demo yorumu (#{fid})\nÖdeme niyeti: {pay}\nKaynak: {body.source}\n"
            f"“{snippet}”"
        )
    except Exception as exc:  # pragma: no cover - notification must not break feedback
        logger.warning("demo feedback admin notify failed: %s", exc)

    return {"status": "ok", "id": fid}


@router.get("/demo/feedback/stats")
def demo_feedback_stats():
    """Minimal aggregate for the Friday ritual (no raw text exposure)."""
    from distribution.store import ensure_tables, get_conn

    ensure_tables()
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM demo_feedback").fetchone()[0]
        by_pay = dict(
            conn.execute(
                "SELECT COALESCE(NULLIF(q3_would_pay,''),'-') , COUNT(*)"
                " FROM demo_feedback GROUP BY 1"
            ).fetchall()
        )
    return {"total": total, "would_pay": by_pay}

"""Stripe webhook -> premium Telegram channel automation.

Flow (Funnel doc §7 / Telegram doc §8):
  checkout.session.completed -> single-use premium invite link
      -> DM'd to the user's Telegram (if tg id supplied via payment-link
         custom field) otherwise the admin is notified to deliver manually.
  customer.subscription.deleted / charge.refunded -> kick from premium channel.

Signature verification implemented with stdlib HMAC per Stripe docs —
no stripe SDK dependency for this single endpoint.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(tags=["billing"])
logger = logging.getLogger(__name__)

_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
_TOLERANCE_SECONDS = 300


def _verify_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """Stripe-Signature: t=...,v1=... — HMAC-SHA256 over '{t}.{payload}'."""
    try:
        parts = dict(p.split("=", 1) for p in sig_header.split(","))
        ts = int(parts["t"])
        v1 = parts.get("v1", "")
    except Exception:
        return False
    if abs(time.time() - ts) > _TOLERANCE_SECONDS:
        return False
    signed = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, v1)


def _extract_tg_user_id(session: dict) -> str:
    """Payment Link custom field 'telegram' (kullanıcıdan istenir) veya metadata."""
    for f in session.get("custom_fields") or []:
        if str(f.get("key", "")).lower().startswith("telegram"):
            val = (f.get("text") or {}).get("value") or ""
            return str(val).strip().lstrip("@")
    return str((session.get("metadata") or {}).get("telegram_id") or "").strip()


@router.post("/billing/stripe-webhook")
async def stripe_webhook(
    request: Request, stripe_signature: str = Header("", alias="Stripe-Signature")
):
    from distribution.store import log_premium_event
    from distribution.telegram_client import (
        create_one_time_invite,
        kick_user,
        notify_admin,
        send_message,
    )

    payload = await request.body()
    if not _WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="webhook secret not configured")
    if not _verify_signature(payload, stripe_signature, _WEBHOOK_SECRET):
        raise HTTPException(status_code=400, detail="invalid signature")

    event = json.loads(payload.decode())
    etype = event.get("type", "")
    obj = (event.get("data") or {}).get("object") or {}
    customer = str(obj.get("customer") or "")
    email = str((obj.get("customer_details") or {}).get("email") or obj.get("customer_email") or "")

    if etype == "checkout.session.completed":
        tg_id = _extract_tg_user_id(obj)
        log_premium_event("checkout_completed", customer, email, tg_id, detail=etype)
        try:
            invite = create_one_time_invite(premium=True)
        except Exception as exc:
            logger.error("invite creation failed: %s", exc)
            notify_admin(f"❌ Premium davet linki üretilemedi ({email}): {exc}")
            return {"status": "invite_failed"}

        welcome = (
            "💠 FinPilot Premium'a hoş geldin!\n\n"
            f"Özel kanal davetin (tek kullanımlık): {invite}\n\n"
            "Nasıl okumalı: Grade = kalibre derecelendirme; risk notu her adayın yanında; "
            "izleme güncellemeleri önceki adayların seyrini gösterir.\n"
            "Dürüst beklenti: kötü haftalar olacak ve hepsini karnede göreceksin — "
            "bu ürün kesinlik değil, disiplinli araştırma sunar.\n"
            "İstediğin an tek mesajla iptal + 14 gün koşulsuz iade.\n\n"
            "Bu içerik araştırma ve eğitim amaçlıdır; yatırım tavsiyesi değildir."
        )
        delivered = False
        if tg_id and tg_id.isdigit():
            delivered = send_message(tg_id, welcome)
        if delivered:
            log_premium_event("invite_sent", customer, email, tg_id)
        else:
            notify_admin(
                f"💠 Yeni premium ödeme: {email or customer}. "
                f"Telegram ID {'yok' if not tg_id else tg_id + ' (DM başarısız)'} — daveti elle ilet:\n{invite}"
            )
            log_premium_event("invite_manual", customer, email, tg_id, detail=invite)
        return {"status": "ok", "delivered": delivered}

    if etype in ("customer.subscription.deleted", "charge.refunded"):
        log_premium_event("cancelled" if "subscription" in etype else "refund", customer, email)
        # tg id'yi geçmiş eventlerden bul
        from distribution.store import ensure_tables, get_conn

        ensure_tables()
        with get_conn() as conn:
            row = conn.execute(
                "SELECT tg_user_id FROM premium_events WHERE stripe_customer=?"
                " AND tg_user_id != '' ORDER BY id DESC LIMIT 1",
                (customer,),
            ).fetchone()
        tg_id = row[0] if row else ""
        if tg_id and tg_id.isdigit():
            if kick_user(tg_id, premium=True):
                log_premium_event("kicked", customer, email, tg_id)
        else:
            notify_admin(f"ℹ️ Premium iptal/iade: {email or customer} — kanaldan elle çıkar.")
        return {"status": "ok"}

    return {"status": "ignored", "type": etype}

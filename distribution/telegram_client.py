"""Minimal Telegram Bot API client for the distribution layer (stdlib only).

Channel broadcasting + admin DM. Retry x3 with backoff; every send is
recorded in tg_delivery_log.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

from distribution.store import log_delivery

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")  # @finpilot_brief or -100...
PREMIUM_CHANNEL_ID = os.getenv("TELEGRAM_PREMIUM_CHANNEL_ID", "")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "") or os.getenv("TELEGRAM_CHAT_ID", "")

_RETRIES = 3
_BACKOFF = 2.0


def _api(method: str, payload: dict) -> dict:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    last_err: Exception | None = None
    for attempt in range(1, _RETRIES + 1):
        try:
            # nosec B310 - url is built from a hardcoded https://api.telegram.org
            # prefix above, never from user input.
            with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
                out = json.loads(resp.read().decode())
                if not out.get("ok"):
                    raise RuntimeError(f"telegram error: {out}")
                return out
        except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
            last_err = exc
            if attempt < _RETRIES:
                time.sleep(_BACKOFF * attempt)
    raise RuntimeError(f"telegram send failed after {_RETRIES} attempts: {last_err}")


def send_message(chat_id: str, text: str, queue_id: int | None = None) -> bool:
    """Markdown message with delivery logging. Returns success flag."""
    try:
        _api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            },
        )
        log_delivery(queue_id, str(chat_id), True)
        return True
    except Exception as exc:
        logger.error("telegram send to %s failed: %s", chat_id, exc)
        log_delivery(queue_id, str(chat_id), False, str(exc))
        return False


def send_to_channel(text: str, queue_id: int | None = None, premium: bool = False) -> bool:
    chat = PREMIUM_CHANNEL_ID if premium else CHANNEL_ID
    if not chat:
        logger.warning("channel id not configured (premium=%s)", premium)
        return False
    return send_message(chat, text, queue_id=queue_id)


def notify_admin(text: str) -> bool:
    if not ADMIN_ID:
        logger.warning("TELEGRAM_ADMIN_ID not configured")
        return False
    return send_message(ADMIN_ID, text)


def create_one_time_invite(premium: bool = True) -> str:
    """Single-use invite link for the (premium) channel."""
    chat = PREMIUM_CHANNEL_ID if premium else CHANNEL_ID
    out = _api("createChatInviteLink", {"chat_id": chat, "member_limit": 1})
    return str(out["result"]["invite_link"])


def kick_user(user_id: str, premium: bool = True) -> bool:
    """Remove a user from the (premium) channel: ban + immediate unban."""
    chat = PREMIUM_CHANNEL_ID if premium else CHANNEL_ID
    try:
        _api("banChatMember", {"chat_id": chat, "user_id": int(user_id)})
        _api("unbanChatMember", {"chat_id": chat, "user_id": int(user_id)})
        return True
    except Exception as exc:
        logger.error("kick_user %s failed: %s", user_id, exc)
        return False

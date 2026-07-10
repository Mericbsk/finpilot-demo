"""M7 yardımcısı — Telegram kanal/kullanıcı ID keşfi (SENİN makinede çalıştır).

Kullanım (PowerShell, repo kökünde):
    python scripts/tg_discover.py

Önce şunları yap (yoksa liste boş gelir):
  1. Public kanala 1 test mesajı at.
  2. Private kanala 1 test mesajı at.
  3. Botuna DM'den /start yaz.
  4. telegram_bot_runner ÇALIŞMIYOR olsun (updates'i o tüketir).

Çıktı token içermez — bana olduğu gibi yapıştırabilirsin.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _token() -> str:
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        m = re.match(r"TELEGRAM_BOT_TOKEN=(.+)", line.strip())
        if m:
            return m.group(1).strip()
    return ""


def main() -> int:
    token = _token()
    if not token:
        print("HATA: .env içinde TELEGRAM_BOT_TOKEN yok.")
        return 1

    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=100"
    with urllib.request.urlopen(url, timeout=20) as r:  # nosec B310 - kendi bot API'miz  # noqa: S310
        data = json.loads(r.read().decode())

    if not data.get("ok"):
        print("HATA: Telegram API 'ok' dönmedi:", data.get("description"))
        return 1

    chats: dict[int, tuple[str, str]] = {}
    for u in data.get("result", []):
        for key in ("message", "channel_post", "my_chat_member", "edited_message"):
            obj = u.get(key)
            if not obj:
                continue
            c = obj.get("chat", {})
            if c.get("id"):
                chats[c["id"]] = (
                    str(c.get("type")),
                    str(c.get("title") or c.get("username") or c.get("first_name") or ""),
                )
            frm = obj.get("from", {})
            if frm.get("id") and not frm.get("is_bot"):
                chats[frm["id"]] = (
                    "user",
                    str(frm.get("username") or frm.get("first_name") or ""),
                )

    if not chats:
        print("Liste boş — kanallara birer mesaj at + bota /start yaz, sonra tekrar çalıştır.")
        return 0

    print("── Görülen sohbetler (token İÇERMEZ, güvenle paylaş) ──")
    for cid, (typ, name) in sorted(chats.items()):
        print(f"  {typ:8} | id={cid:<16} | {name}")
    print()
    print("Eşleştirme rehberi:")
    print("  channel + public adı olan  → TELEGRAM_CHANNEL_ID (@kullaniciadi da olur)")
    print("  channel + private olan     → TELEGRAM_PREMIUM_CHANNEL_ID (-100... sayısı)")
    print("  user (sen)                 → TELEGRAM_ADMIN_ID")
    return 0


if __name__ == "__main__":
    sys.exit(main())

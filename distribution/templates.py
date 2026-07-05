"""Message templates for the daily/weekly briefs (str.format based, no jinja).

All renderers return Telegram-Markdown text that MUST still pass
``lint.assert_publishable`` before entering the broadcast queue.
"""

from __future__ import annotations

import os
from typing import Any

from distribution.lint import DISCLAIMER_TR
from distribution.schema import free_view

SITE_URL = os.getenv("FINPILOT_SITE_URL", "https://www.finpilot.at")
DEMO_URL = f"{SITE_URL}/demo?utm_source=telegram&utm_medium=brief"
KARNE_URL = f"{SITE_URL}/demo?utm_source=telegram&utm_medium=brief#karne"

_GRADE_EMOJI = {"A": "🟢", "B": "🔵", "C": "⚪"}

MAX_FREE_LEN = 1200
MAX_PREMIUM_LEN = 2600


def _candidate_line(c: dict[str, Any], with_risk: bool = False) -> str:
    badges = " ".join(f"#{b}" for b in c.get("badges", []))
    emoji = _GRADE_EMOJI.get(c.get("grade", ""), "⚪")
    line = (
        f"{emoji} *{c['ticker']}* — Grade {c['grade']} · "
        f"geçmişte bu profildekilerin {c['prob_band']}'i 5 günde ≥%5 hareket etti\n"
        f"{c['rationale']}\n{badges}"
    )
    if with_risk and c.get("risk_note"):
        line += f"\n⚠️ {c['risk_note']}"
    return line


def _karne_line(snap: dict[str, Any]) -> str:
    karne = snap.get("karne") or {}
    totals = karne.get("toplam_aday_bugun") or {}
    shown = len(free_view(snap).get("candidates", []))
    total = sum(int(v) for v in totals.values()) if totals else None
    if total:
        detail = ", ".join(f"{k}: {v}" for k, v in totals.items())
        return (
            f"🎯 Bugün sistem toplam *{total} aday* işaretledi ({detail}). "
            f"Yukarıda {shown} tanesini görüyorsun. Tam karne: {KARNE_URL}"
        )
    return f"🎯 Sistemin açık karnesi: {KARNE_URL}"


def render_daily_free(snap: dict[str, Any], concept_line: str = "") -> str:
    view = free_view(snap)
    cands = view.get("candidates", [])
    lines = [f"📊 *FinPilot Daily Brief — {snap['date']}*"]
    lines.append(f"_Bu sabah {snap.get('universe', 0)} hisse tarandı._\n")
    if cands:
        lines += [_candidate_line(c) for c in cands]
    else:
        lines.append("Bugün eşiği geçen aday yok — bazı günler en iyi aday 'bekle'dir.")
    lines.append("")
    lines.append(_karne_line(snap))
    if concept_line:
        lines.append(f"📚 Günün kavramı: {concept_line}")
    lines.append(f"🔍 Dünün brifini web'de incele: {DEMO_URL}")
    lines.append(f"\n_{DISCLAIMER_TR}_")
    return "\n".join(lines)


def render_daily_premium(snap: dict[str, Any], watch_updates: list[str] | None = None) -> str:
    cands = snap.get("candidates", [])
    lines = [f"💠 *FinPilot Premium Brief — {snap['date']}*"]
    lines.append(f"_Tam liste: {len(cands)} aday · {snap.get('universe', 0)} hisse tarandı._\n")
    for c in cands:
        lines.append(_candidate_line(c, with_risk=True))
        lines.append("")
    if watch_updates:
        lines.append("👁 *İzleme güncellemeleri*")
        lines += [f"• {u}" for u in watch_updates[:6]]
        lines.append("")
    lines.append(_karne_line(snap))
    lines.append(f"\n_{DISCLAIMER_TR}_")
    return "\n".join(lines)


def render_weekly(karne_summary: str, lesson: str, date_range: str) -> str:
    return (
        f"🗓 *FinPilot Haftalık Özet — {date_range}*\n\n"
        f"📊 *Karne:*\n{karne_summary}\n\n"
        f"📚 *Haftanın dersi:*\n{lesson}\n\n"
        f"Tam karne ve metodoloji: {KARNE_URL}\n\n"
        f"_{DISCLAIMER_TR}_"
    )


def render_holiday(date_str: str, reason: str) -> str:
    return (
        f"🇺🇸 *{date_str}* — ABD piyasaları bugün kapalı ({reason}). "
        f"Brif yarın normal saatinde.\n\n_{DISCLAIMER_TR}_"
    )


def render_correction(date_str: str, wrong: str, correct: str) -> str:
    return (
        f"✏️ *Düzeltme — {date_str} brifi:* {wrong} bilgisi hatalıydı; doğrusu: {correct}. "
        f"Şeffaflık karnenin parçasıdır.\n\n_{DISCLAIMER_TR}_"
    )

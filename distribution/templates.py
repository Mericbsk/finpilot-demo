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
_BADGE_LABELS = {
    "squeeze": "Short baskısı",
    "catalyst": "Şirket katalizörü",
    "rvol": "Göreli hacim",
    "gap": "Açılış gap'i",
    "momentum": "Kısa vadeli momentum",
    "volume": "Hacim artışı",
    "contraction": "Sıkışma çözülmesi",
    "regime": "Destekleyici piyasa",
    "early_tier": "Aşamalı teyit",
}


def _esc(t: str) -> str:
    """HTML parse modu icin kacis (Telegram: &, <, > yeter)."""
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


MAX_FREE_LEN = 1200
MAX_PREMIUM_LEN = 2600


def _candidate_line(c: dict[str, Any], with_risk: bool = False) -> str:
    badge_labels = [
        _BADGE_LABELS.get(str(b), str(b).replace("_", " ")) for b in c.get("badges", [])
    ]
    badges = " · ".join(_esc(label) for label in badge_labels)
    emoji = _GRADE_EMOJI.get(c.get("grade", ""), "⚪")
    band = c.get("prob_band", "—")
    if band and band != "—":
        stat = f"geçmişte bu profildekilerin {_esc(band)}'i 5 günde ≥%5 hareket etti"
    else:
        stat = "olasılık bandı için veri birikiyor (yeni faktör seti)"
    line = (
        f"{emoji} <b>{_esc(c['ticker'])}</b> — Grade {_esc(c['grade'])} · {stat}\n"
        f"<b>Öne çıkaran nedenler:</b> {_esc(c['rationale'])}\n"
        f"🔎 <i>Sinyal bileşenleri:</i> {badges or 'çoklu faktör değerlendirmesi'}"
    )
    if with_risk and c.get("risk_note"):
        line += f"\n⚠️ {_esc(c['risk_note'])}"
    return line


def _karne_line(snap: dict[str, Any], shown: int | None = None) -> str:
    karne = snap.get("karne") or {}
    totals = karne.get("toplam_aday_bugun") or {}
    if shown is None:
        shown = len(free_view(snap).get("candidates", []))
    total = sum(int(v) for v in totals.values()) if totals else None
    if total:
        detail = ", ".join(f"{k}: {v}" for k, v in totals.items())
        return (
            f"🎯 Bugün sistem toplam <b>{total} aday</b> işaretledi ({_esc(detail)}). "
            f"Yukarıda {shown} tanesini görüyorsun. Tam karne: {KARNE_URL}"
        )
    return f"🎯 Sistemin açık karnesi: {KARNE_URL}"


def render_daily_free(snap: dict[str, Any], concept_line: str = "", context_line: str = "") -> str:
    view = free_view(snap)
    cands = view.get("candidates", [])
    lines = [f"📊 <b>FinPilot Daily Brief — {_esc(snap['date'])}</b>"]
    lines.append(f"<i>Bu sabah {snap.get('universe', 0)} hisse tarandı.</i>")
    if context_line:
        lines.append(f"<i>{_esc(context_line)}</i>")
    lines.append("")
    if cands:
        lines += [_candidate_line(c) for c in cands]
    else:
        lines.append("Bugün eşiği geçen aday yok — bazı günler en iyi aday 'bekle'dir.")
    lines.append("")
    lines.append(_karne_line(snap))
    if concept_line:
        lines.append(f"📚 Günün kavramı: {concept_line}")
    lines.append(f"🔍 Dünün brifini web'de incele: {DEMO_URL}")
    lines.append(f"\n<i>{DISCLAIMER_TR}</i>")
    return "\n".join(lines)


def render_daily_premium(
    snap: dict[str, Any],
    watch_updates: list[str] | None = None,
    context_line: str = "",
) -> str:
    cands = snap.get("candidates", [])
    lines = [f"💠 <b>FinPilot Premium Brief — {_esc(snap['date'])}</b>"]
    lines.append(f"<i>Tam liste: {len(cands)} aday · {snap.get('universe', 0)} hisse tarandı.</i>")
    if context_line:
        lines.append(f"<i>{_esc(context_line)}</i>")
    lines.append("")
    for c in cands:
        lines.append(_candidate_line(c, with_risk=True))
        lines.append("")
    if watch_updates:
        lines.append("👁 <b>İzleme güncellemeleri</b>")
        lines += [f"• {u}" for u in watch_updates[:6]]
        lines.append("")
    lines.append(_karne_line(snap, shown=len(cands)))
    lines.append(f"\n<i>{DISCLAIMER_TR}</i>")
    return "\n".join(lines)


def render_weekly(karne_summary: str, lesson: str, date_range: str) -> str:
    return (
        f"🗓 <b>FinPilot Haftalık Özet — {_esc(date_range)}</b>\n\n"
        f"📊 <b>Karne:</b>\n{_esc(karne_summary)}\n\n"
        f"📚 <b>Haftanın dersi:</b>\n{_esc(lesson)}\n\n"
        f"Tam karne ve metodoloji: {KARNE_URL}\n\n"
        f"_{DISCLAIMER_TR}_"
    )


def render_holiday(date_str: str, reason: str) -> str:
    return (
        f"🇺🇸 <b>{_esc(date_str)}</b> — ABD piyasaları bugün kapalı ({_esc(reason)}). "
        f"Brif yarın normal saatinde.\n\n_{DISCLAIMER_TR}_"
    )


def render_correction(date_str: str, wrong: str, correct: str) -> str:
    return (
        f"✏️ <b>Düzeltme — {_esc(date_str)} brifi:</b> {_esc(wrong)} bilgisi hatalıydı; doğrusu: {_esc(correct)}. "
        f"Şeffaflık karnenin parçasıdır.\n\n_{DISCLAIMER_TR}_"
    )

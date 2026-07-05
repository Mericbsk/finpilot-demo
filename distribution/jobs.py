"""Scheduler-facing job functions for the distribution layer.

Wire-up (core/scheduler.py, env-gated FINPILOT_ENABLE_DISTRIBUTION=1):
  07:50 Europe/Vienna  job_draft     — build snapshot, render briefs, lint,
                                       queue, DM admin for approval
  08:30 Europe/Vienna  job_publish   — send APPROVED drafts to channel(s),
                                       push snapshot to web
  Sun 10:00            job_weekly    — weekly summary draft -> queue
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import urllib.request
from datetime import UTC, datetime

UTC = UTC
from pathlib import Path

from distribution import broadcast, templates
from distribution.concepts import concept_of_the_day
from distribution.market_calendar import holiday_name, is_trading_day
from distribution.snapshot_builder import build_snapshot, load_scan_export, save_snapshot
from distribution.telegram_client import notify_admin, send_to_channel

logger = logging.getLogger(__name__)

WEB_PUBLIC_SNAPSHOT = Path(os.getenv("FINPILOT_WEB_SNAPSHOT", "web/public/demo_snapshot.json"))
API_BASE = os.getenv("FINPILOT_LOCAL_API", "http://localhost:8000/api/v1")


def distribution_enabled() -> bool:
    return os.getenv("FINPILOT_ENABLE_DISTRIBUTION", "0") == "1"


def _fetch_karne() -> dict | None:
    """Best-effort karne from the local API (watchlist performance).

    Response shape (api/routers/watchlist.py): by_conviction / by_tier are
    LISTS of {group, count, tp_count, stop_count, open_count, tp_rate, avg_pnl}
    where tp_rate is 0-100. We map A/B/C groups to {n, hit_rate (0-1)}.
    """
    try:
        # nosec B310 - API_BASE is an ops-controlled env var (default localhost),
        # never user input; scheme is always http(s).
        with urllib.request.urlopen(f"{API_BASE}/watchlist/performance?days=5", timeout=20) as r:  # nosec B310
            data = json.loads(r.read().decode())
        by_grade: dict[str, dict] = {}
        for key in ("by_conviction", "by_tier"):
            for row in data.get(key) or []:
                grp = str(row.get("group", "")).upper()
                if grp in ("A", "B", "C") and isinstance(row, dict):
                    by_grade[grp] = {
                        "n": int(row.get("count") or 0),
                        "hit_rate": round(float(row.get("tp_rate") or 0.0) / 100.0, 3),
                        "avg_pnl": row.get("avg_pnl"),
                    }
            if by_grade:
                break
        if not by_grade:
            return None
        return {"by_grade": by_grade, "window": f"last {data.get('days', 5)}d eval", "raw": True}
    except Exception as exc:
        logger.warning("karne fetch failed: %s", exc)
        return None


def job_draft() -> dict:
    """07:50 — build snapshot + queue free/premium drafts + notify admin."""
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}

    today = datetime.now(tz=UTC).date()
    if not is_trading_day(today):
        reason = holiday_name(today) or "weekend"
        if reason != "weekend":  # holiday note only for real holidays
            text = templates.render_holiday(today.isoformat(), reason)
            qid = broadcast.queue_draft("holiday", today.isoformat(), text)
            notify_admin(f"🇺🇸 Tatil notu kuyruğa alındı (#{qid}). ONAYLA {qid} / RED {qid}")
        return {"skipped": f"not a trading day ({reason})"}

    broadcast.expire_stale()

    try:
        rows, universe, date_str = load_scan_export()
    except FileNotFoundError:
        notify_admin(
            "⚠️ Bugün için scan export bulunamadı — brif taslağı üretilemedi. Önce bir tarama çalıştır."
        )
        return {"error": "scan export missing"}

    if date_str != today.isoformat():
        notify_admin(
            f"⚠️ Scan export bayat ({date_str}). Bugünkü brif üretilmedi — yeni tarama gerekli."
        )
        return {"error": f"stale export {date_str}"}

    karne = _fetch_karne()
    snap = build_snapshot(rows, universe=universe, karne=karne, date_str=date_str)
    save_snapshot(snap)

    concept = concept_of_the_day(today)
    free_text = templates.render_daily_free(snap, concept_line=concept)
    qid_free = broadcast.queue_draft("daily_free", date_str, free_text)

    result = {"snapshot": True, "free_queue_id": qid_free, "warnings": snap.get("warnings", [])}

    if os.getenv("FINPILOT_ENABLE_PREMIUM_BRIEF", "0") == "1":
        prem_text = templates.render_daily_premium(snap)
        result["premium_queue_id"] = broadcast.queue_draft("daily_premium", date_str, prem_text)

    warn = ("\n⚠️ " + "; ".join(snap["warnings"])) if snap.get("warnings") else ""
    notify_admin(
        f"📝 *{date_str} brif taslağı hazır.*{warn}\n\n"
        f"— ÜCRETSİZ (#{qid_free}) —\n{free_text[:1500]}\n\n"
        f"Yayınlamak için: `ONAYLA {qid_free}`  ·  Reddetmek için: `RED {qid_free}`"
    )
    return result


def job_publish() -> dict:
    """08:30 — send approved drafts; push snapshot to the web demo."""
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}

    sent, failed = [], []
    for item in broadcast.get_approved_unsent():
        premium = item["kind"] == "daily_premium"
        ok = send_to_channel(item["text"], queue_id=item["id"], premium=premium)
        if ok:
            broadcast.mark_sent(item["id"])
            sent.append(item["id"])
        else:
            broadcast.mark_sent(item["id"], error="send failed")
            failed.append(item["id"])

    pending = broadcast.get_pending()
    if pending:
        notify_admin(
            f"⏰ Yayın saati geçti, onaysız {len(pending)} taslak var (yayınlanmadı): "
            + ", ".join(f"#{p['id']}" for p in pending)
        )

    pushed = _push_snapshot_to_web()
    if failed:
        notify_admin(f"❌ Gönderim hatası: {failed} — tg_delivery_log'a bak.")
    return {
        "sent": sent,
        "failed": failed,
        "web_pushed": pushed,
        "pending_unapproved": len(pending),
    }


def _push_snapshot_to_web() -> bool:
    """Copy the FREE view of the latest snapshot to web/public for the demo."""
    from distribution.schema import demo_view
    from distribution.snapshot_builder import EXPORT_DIR

    src = EXPORT_DIR / "snapshot_latest.json"
    if not src.exists():
        return False
    try:
        snap = json.loads(src.read_text(encoding="utf-8"))
        # Public file: yesterday's top-3 (premium fields stripped) + full karne.
        public = demo_view(snap, max_candidates=3)
        WEB_PUBLIC_SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        WEB_PUBLIC_SNAPSHOT.write_text(
            json.dumps(public, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        # Optional: external publish hook (e.g. copy into the Vercel repo /
        # rclone to R2). Configured by ops, not by code. shell=False + shlex
        # split avoids shell-injection risk even though the value is
        # operator-controlled (defense in depth).
        hook = os.getenv("FINPILOT_WEB_PUBLISH_CMD", "")
        if hook:
            import shlex
            import subprocess

            subprocess.run(shlex.split(hook), timeout=120, check=False)
        return True
    except Exception as exc:
        logger.error("web snapshot push failed: %s", exc)
        return False


def job_weekly() -> dict:
    """Sunday — weekly summary draft into the queue."""
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}
    today = datetime.now(tz=UTC).date()
    karne = _fetch_karne()
    if karne and karne.get("by_grade"):
        lines = []
        for g, stats in sorted(karne["by_grade"].items()):
            n = stats.get("n") or stats.get("count") or "?"
            hit = stats.get("hit_rate") or stats.get("success_rate") or stats.get("hit5") or "?"
            lines.append(f"Grade {g}: n={n}, isabet={hit}")
        karne_summary = "\n".join(lines)
    else:
        karne_summary = "Bu hafta karne verisi derlenemedi; gelecek hafta tam tablo."

    lesson = concept_of_the_day(today)
    text = templates.render_weekly(karne_summary, lesson, date_range=f"{today.isoformat()} haftası")
    qid = broadcast.queue_draft("weekly", today.isoformat(), text)
    notify_admin(
        f"🗓 Haftalık özet taslağı hazır (#{qid}).\n\n{text[:1200]}\n\n`ONAYLA {qid}` / `RED {qid}`"
    )
    return {"weekly_queue_id": qid}


def push_snapshot_manual(snapshot_path: str | Path) -> bool:
    """CLI helper: publish an arbitrary snapshot file to web/public."""
    p = Path(snapshot_path)
    from distribution.snapshot_builder import EXPORT_DIR

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(p, EXPORT_DIR / "snapshot_latest.json")
    return _push_snapshot_to_web()

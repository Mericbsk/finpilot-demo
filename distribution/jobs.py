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
    except (json.JSONDecodeError, ValueError) as exc:
        notify_admin(f"⚠️ Scan export bozuk okundu ({exc}) — yeni tarama gerekli.")
        return {"error": "scan export corrupt"}

    if date_str != today.isoformat():
        notify_admin(
            f"⚠️ Scan export bayat ({date_str}). Bugünkü brif üretilmedi — yeni tarama gerekli."
        )
        return {"error": f"stale export {date_str}"}

    karne = _fetch_karne()
    snap = build_snapshot(rows, universe=universe, karne=karne, date_str=date_str)
    save_snapshot(snap)

    # English snapshot for the web Ledger (landing + /demo) — the Telegram
    # brief above stays Turkish for its existing audience; this is a
    # separate, additive artefact so the web/Telegram pipelines can't
    # interfere with each other.
    try:
        from distribution.snapshot_builder import EXPORT_DIR

        snap_en = build_snapshot(rows, universe=universe, karne=karne, date_str=date_str, lang="en")
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        (EXPORT_DIR / "snapshot_en_latest.json").write_text(
            json.dumps(snap_en, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    except Exception as exc:
        logger.warning("english web snapshot build failed: %s", exc)

    concept = concept_of_the_day(today)
    from distribution.market_context import build_context_line

    ctx_line = build_context_line("tr")
    free_text = templates.render_daily_free(snap, concept_line=concept, context_line=ctx_line)
    qid_free = broadcast.queue_draft("daily_free", date_str, free_text)

    result = {"snapshot": True, "free_queue_id": qid_free, "warnings": snap.get("warnings", [])}

    if os.getenv("FINPILOT_ENABLE_PREMIUM_BRIEF", "0") == "1":
        prem_text = templates.render_daily_premium(snap, context_line=ctx_line)
        result["premium_queue_id"] = broadcast.queue_draft("daily_premium", date_str, prem_text)

    warn = ("\n⚠️ " + "; ".join(snap["warnings"])) if snap.get("warnings") else ""
    notify_admin(
        f"📝 <b>{date_str} brif taslağı hazır.</b>{warn}\n\n"
        f"— ÜCRETSİZ (#{qid_free}) —\n{free_text[:1500]}\n\n"
        f"Yayınlamak için: ONAYLA {qid_free}  ·  Reddetmek için: RED {qid_free}"
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

    # Prefer the English snapshot (web Ledger's language) when present;
    # fall back to the Turkish one so publishing never silently breaks.
    src = EXPORT_DIR / "snapshot_en_latest.json"
    if not src.exists():
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
        f"🗓 Haftalık özet taslağı hazır (#{qid}).\n\n{text[:1200]}\n\nONAYLA {qid} / RED {qid}"
    )
    return {"weekly_queue_id": qid}


def push_snapshot_manual(snapshot_path: str | Path) -> bool:
    """CLI helper: publish an arbitrary snapshot file to web/public."""
    p = Path(snapshot_path)
    from distribution.snapshot_builder import EXPORT_DIR

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(p, EXPORT_DIR / "snapshot_latest.json")
    return _push_snapshot_to_web()


# ── Startup catch-up (Meriç'in "PC'yi sabah elle açarım" kararının gereği) ────
# APScheduler kaçan cron'ları geriye dönük çalıştırmaz. PC 07:15'ten sonra
# açılırsa zincir kopmasın diye scheduler başlarken bu fonksiyon çağrılır:
# "bugün ne eksikse tamamla". Kural: 08:15'ten önce aç, gerisi otomatik.

CATCHUP_WINDOW_START = (6, 30)  # Vienna
CATCHUP_WINDOW_END = (11, 0)


def _vienna_now():
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(tz=ZoneInfo("Europe/Vienna"))
    except Exception:  # pragma: no cover
        return datetime.now(tz=UTC)


def job_startup_catchup() -> dict:
    """Scheduler açılışında bugünün eksik adımlarını tamamla (idempotent).

    Sıra: (1) taze scan export yoksa sabah taramasını tetikle [E5 gelince],
    (2) taslak üretilmemişse job_draft, (3) saat 08:30'u geçtiyse ve onaylı
    bekleyen varsa job_publish. Her adım kendi korumalarını zaten taşır
    (bayat veri reddi, onaysız-yayın-yok, lint).
    """
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}

    now_v = _vienna_now()
    today = now_v.date()
    result: dict = {"time": now_v.strftime("%H:%M")}

    if not is_trading_day(today):
        return {**result, "skipped": "not a trading day"}

    hm = (now_v.hour, now_v.minute)
    if hm < CATCHUP_WINDOW_START or hm > CATCHUP_WINDOW_END:
        return {**result, "skipped": "outside catch-up window"}

    # (1) Scan export bugünün mü? Değilse sabah taramasını tetikle (E5 hook'u).
    export_fresh = False
    try:
        _rows, _uni, date_str = load_scan_export()
        export_fresh = date_str == today.isoformat()
    except FileNotFoundError:
        pass
    if not export_fresh:
        result["scan"] = _trigger_morning_scan()
        try:
            _rows, _uni, date_str = load_scan_export()
            export_fresh = date_str == today.isoformat()
        except FileNotFoundError:
            export_fresh = False

    # (2) Bugünün taslağı kuyrukta/karar görmüş mü? Yoksa üret.
    from distribution.store import ensure_tables, get_conn

    ensure_tables()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM broadcast_queue WHERE brief_date=? AND kind LIKE 'daily%'",
            (today.isoformat(),),
        ).fetchone()
    if row[0] == 0 and export_fresh:
        result["draft"] = job_draft()

    # (3) Yayın saati geçtiyse onaylıları gönder + web push (idempotent).
    if hm >= (8, 30):
        result["publish"] = job_publish()

    if result.get("draft") or result.get("publish") or result.get("scan"):
        notify_admin(
            f"🔄 Catch-up ({result['time']}): "
            + ", ".join(k for k in ("scan", "draft", "publish") if k in result)
            + " tamamlandı."
        )
    return result


def _trigger_morning_scan() -> dict:
    """E5 sabah taraması — localhost API'ye mevcut /scan yolu üzerinden.

    v1: sembol listesi data/distribution/universe.txt (satır başına sembol)
    veya env FINPILOT_SCAN_SYMBOLS (virgüllü). Liste yoksa tarama atlanır ve
    admin bilgilendirilir (asla sessiz kalmaz).
    """
    symbols = _load_universe()
    if not symbols:
        notify_admin(
            "⚠️ Sabah taraması: sembol listesi yok (data/distribution/universe.txt) — tarama atlandı."
        )
        return {"skipped": "no universe"}

    batch = 200
    done, failed = 0, 0
    for i in range(0, len(symbols), batch):
        chunk = symbols[i : i + batch]
        try:
            req = urllib.request.Request(
                f"{API_BASE}/scan",
                data=json.dumps({"symbols": chunk}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=660) as r:  # nosec B310 - kendi API_BASE'imiz
                r.read()
            done += len(chunk)
        except Exception as exc:
            failed += len(chunk)
            logger.warning("morning scan batch failed (%d-%d): %s", i, i + batch, exc)
    if failed:
        notify_admin(f"⚠️ Sabah taraması: {done} OK, {failed} sembol başarısız batch'lerde kaldı.")
    return {"scanned": done, "failed": failed}


def _load_universe() -> list[str]:
    """Sembol evreni. Öncelik: env override > universe.txt > stock_presets.json.

    Kanonik kaynak web/public/stock_presets.json'dur (dashboard'ın 1812'lik
    preset seti) — ayrı bir liste tutmak drift üretir; buradan türetilir.
    """
    env_syms = os.getenv("FINPILOT_SCAN_SYMBOLS", "")
    if env_syms.strip():
        return [x.strip().upper() for x in env_syms.split(",") if x.strip()]

    from distribution.snapshot_builder import EXPORT_DIR

    p = EXPORT_DIR / "universe.txt"
    if p.exists():
        return [
            line.strip().upper()
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]

    presets = Path(os.getenv("FINPILOT_PRESETS_JSON", "web/public/stock_presets.json"))
    if presets.exists():
        try:
            data = json.loads(presets.read_text(encoding="utf-8"))
            symbols: set[str] = set()

            def _walk(x) -> None:
                if isinstance(x, list):
                    for item in x:
                        if isinstance(item, str):
                            symbols.add(item.strip().upper())
                        else:
                            _walk(item)
                elif isinstance(x, dict):
                    for v in x.values():
                        _walk(v)

            _walk(data)
            return sorted(sym for sym in symbols if sym and sym.isascii())
        except Exception as exc:
            logger.warning("stock_presets.json okunamadı: %s", exc)
    return []


def _export_is_fresh() -> bool:
    """Scan export bugünün tarihini mi taşıyor?"""
    try:
        _rows, _uni, date_str = load_scan_export()
        return date_str == _vienna_now().date().isoformat()
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return False


def job_morning_scan() -> dict:
    """E5 — 07:15 Vienna: işlem günüyse ve export taze değilse taramayı çalıştır."""
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}
    today = _vienna_now().date()
    if not is_trading_day(today):
        return {"skipped": "not a trading day"}
    if _export_is_fresh():
        return {"skipped": "export already fresh"}
    result = _trigger_morning_scan()
    if result.get("scanned"):
        logger.info("morning scan done: %s", result)
    return result


def job_scan_sentinel() -> dict:
    """E5 bekçisi — 07:40 Vienna: export hâlâ taze değilse ACİL DM.

    07:50 draft job'u zaten bayat veriyi reddeder; bu bekçi Meriç'e brifin
    riske girdiğini yayın saatinden ÖNCE haber verir.
    """
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}
    today = _vienna_now().date()
    if not is_trading_day(today):
        return {"skipped": "not a trading day"}
    if _export_is_fresh():
        return {"ok": True}
    notify_admin(
        "🚨 07:40 bekçisi: bugünün taraması hâlâ tamamlanmadı — 07:50 brif taslağı "
        "üretilemeyecek. PC/API ayakta mı kontrol et; tarama bitince catch-up "
        "zinciri taslağı kendiliğinden üretir."
    )
    return {"alerted": True}

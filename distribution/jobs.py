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
from distribution.scan_contract import expected_universe
from distribution.schema import validate_snapshot
from distribution.snapshot_builder import (
    build_snapshot,
    load_scan_export,
    load_scan_export_record,
    save_snapshot,
    validate_scan_export,
    write_snapshot,
)
from distribution.telegram_client import notify_admin, send_to_channel

logger = logging.getLogger(__name__)

WEB_PUBLIC_SNAPSHOT = Path(os.getenv("FINPILOT_WEB_SNAPSHOT", "web/public/demo_snapshot.json"))
API_BASE = os.getenv("FINPILOT_LOCAL_API", "http://localhost:8000/api/v1")


def distribution_enabled() -> bool:
    return os.getenv("FINPILOT_ENABLE_DISTRIBUTION", "0") == "1"


def distribution_status() -> dict:
    """Return lightweight operational state for the daily distribution chain."""
    from distribution.snapshot_builder import EXPORT_DIR
    from distribution.store import ensure_tables, get_conn

    status: dict = {
        "enabled": distribution_enabled(),
        "snapshot_date": None,
        "snapshot_universe": None,
        "queue": {"pending": 0, "approved": 0, "sent": 0},
        "last_sent": None,
    }
    snapshot_path = EXPORT_DIR / "snapshot_latest.json"
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        status["snapshot_date"] = snapshot.get("date")
        status["snapshot_universe"] = snapshot.get("universe")
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        status["snapshot_error"] = "snapshot_latest unavailable or invalid"

    try:
        ensure_tables()
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) FROM broadcast_queue GROUP BY status"
            ).fetchall()
            for state, count in rows:
                if state in status["queue"]:
                    status["queue"][state] = int(count)
            row = conn.execute(
                "SELECT id, kind, brief_date, sent_at FROM broadcast_queue "
                "WHERE status='sent' ORDER BY sent_at DESC LIMIT 1"
            ).fetchone()
        if row:
            status["last_sent"] = {
                "queue_id": row[0],
                "kind": row[1],
                "brief_date": row[2],
                "sent_at": row[3],
            }
    except Exception as exc:  # pragma: no cover - health endpoint boundary
        status["queue_error"] = str(exc)
    return status


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
        by_grade = _resolve_karne_by_grade(data)
        if not by_grade:
            return _fetch_karne_db_fallback("api returned no closed outcomes")
        return {"by_grade": by_grade, "window": f"last {data.get('days', 5)}d eval", "raw": True}
    except Exception as exc:
        return _fetch_karne_db_fallback(f"api unreachable: {exc}")


def _fetch_karne_db_fallback(reason: str) -> dict | None:
    """Direct-from-DB karne so manual morning publishes work with the API down."""
    logger.warning("karne API path failed (%s) — falling back to DB", reason)
    try:
        from distribution.karne import compute_karne_db

        return compute_karne_db()
    except Exception as exc:
        logger.warning("karne db fallback failed: %s", exc)
        return None


def _resolve_karne_by_grade(data: dict) -> dict[str, dict]:
    """Resolve honest grade scorecards from closed watchlist outcomes.

    The watchlist report includes open signals in ``count`` and ``tp_rate``.
    A scorecard must use only decided outcomes so an open position cannot be
    counted as a failed observation.
    """
    for key in ("by_conviction", "by_tier"):
        rows = data.get(key) or []
        by_grade: dict[str, dict] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            grade = str(row.get("group", "")).upper()
            if grade not in ("A", "B", "C"):
                continue
            tp = max(0, int(row.get("tp_count") or 0))
            stop = max(0, int(row.get("stop_count") or 0))
            closed = tp + stop
            if closed == 0:
                continue
            by_grade[grade] = {
                "n": closed,
                "hit_rate": round(tp / closed, 3),
                "avg_pnl": row.get("avg_pnl"),
            }
        if by_grade:
            return by_grade
    return {}


def job_draft() -> dict:
    """07:50 — build snapshot + queue free/premium drafts + notify admin."""
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}

    today = _vienna_now().date()
    if not is_trading_day(today):
        reason = holiday_name(today) or "weekend"
        if reason != "weekend":  # holiday note only for real holidays
            text = templates.render_holiday(today.isoformat(), reason)
            qid = broadcast.queue_draft("holiday", today.isoformat(), text)
            notify_admin(f"🇺🇸 Tatil notu kuyruğa alındı (#{qid}). ONAYLA {qid} / RED {qid}")
        return {"skipped": f"not a trading day ({reason})"}

    broadcast.expire_stale()

    try:
        export = load_scan_export_record()
        rows = export.get("results", [])
        universe = int(export.get("universe") or len(rows))
        date_str = str(export.get("date") or "")
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

    export_problems = validate_scan_export(export)
    if export_problems:
        reason = "; ".join(export_problems)
        notify_admin(f"⚠️ Scan export tamamlanmamış ({reason}) — bugünkü brif üretilmedi.")
        return {"error": "incomplete export", "problems": export_problems}

    # P0.3 — manual latency: time between scan finish (export.generated_at) and
    # this draft build. The 55-min "gap" in the 2026-07-24 audit was human
    # approval wait, not compute — make it explicit so it is never a mystery.
    import time as _time
    from datetime import datetime as _dt

    _gen_at = str(export.get("generated_at") or "")
    try:
        _scan_fin = _dt.fromisoformat(_gen_at.replace("Z", "+00:00"))
        _lat_min = (_dt.now(tz=_scan_fin.tzinfo) - _scan_fin).total_seconds() / 60.0
        logger.info(
            "pipeline timing: scan→draft manual latency = %.1f min (export %s)", _lat_min, _gen_at
        )
    except Exception:  # noqa: BLE001
        pass

    karne = _fetch_karne()
    scan_id = export.get("scan_id")
    _t_snap = _time.perf_counter()
    snap = build_snapshot(rows, universe=universe, karne=karne, date_str=date_str, scan_id=scan_id)
    save_snapshot(snap)
    logger.info("pipeline timing: snapshot build+save = %.2fs", _time.perf_counter() - _t_snap)

    # English snapshot for the web Ledger (landing + /demo) — the Telegram
    # brief above stays Turkish for its existing audience; this is a
    # separate, additive artefact so the web/Telegram pipelines can't
    # interfere with each other.
    from distribution.snapshot_builder import EXPORT_DIR

    snap_en = build_snapshot(
        rows,
        universe=universe,
        karne=karne,
        date_str=date_str,
        lang="en",
        scan_id=scan_id,
    )
    tr_tickers = [candidate["ticker"] for candidate in snap.get("candidates", [])]
    en_tickers = [candidate["ticker"] for candidate in snap_en.get("candidates", [])]
    if tr_tickers != en_tickers or snap_en["snapshot_id"] != snap["snapshot_id"]:
        raise ValueError("Turkish and English snapshots do not share identity")
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_snapshot(EXPORT_DIR / "snapshot_en_latest.json", snap_en)

    concept = concept_of_the_day(today)
    from distribution.market_context import build_context_line

    ctx_line = build_context_line("tr")
    free_text = templates.render_daily_free(snap, concept_line=concept, context_line=ctx_line)
    queue_metadata = {
        "snapshot_id": snap["snapshot_id"],
        "snapshot_date": snap["date"],
        "snapshot_universe": snap["universe"],
        "candidate_hash": snap["candidate_hash"],
        "scan_id": snap.get("scan_id"),
    }
    qid_free = broadcast.queue_draft("daily_free", date_str, free_text, **queue_metadata)

    result = {"snapshot": True, "free_queue_id": qid_free, "warnings": snap.get("warnings", [])}

    if os.getenv("FINPILOT_ENABLE_PREMIUM_BRIEF", "0") == "1":
        prem_text = templates.render_daily_premium(snap, context_line=ctx_line)
        result["premium_queue_id"] = broadcast.queue_draft(
            "daily_premium", date_str, prem_text, **queue_metadata
        )

    warn = ("\n⚠️ " + "; ".join(snap["warnings"])) if snap.get("warnings") else ""
    # Admin preview only (not the published text): strip HTML tags before
    # truncating. A raw character-index slice of HTML can cut a tag in half
    # (e.g. "<b>GOO" with no closing "</b>"), which Telegram's HTML parse_mode
    # rejects outright with "400 Bad Request: can't parse entities" — this
    # silently dropped the admin ONAYLA/RED prompt once free_text grew past
    # 1500 chars. Stripping tags first makes the preview length-safe
    # regardless of where the cut lands.
    import re as _re

    _preview_plain = _re.sub(r"<[^>]+>", "", free_text)[:1500]
    notify_admin(
        f"📝 <b>{date_str} brif taslağı hazır.</b>{warn}\n\n"
        f"— ÜCRETSİZ (#{qid_free}) —\n{_preview_plain}\n\n"
        f"Yayınlamak için: ONAYLA {qid_free}  ·  Reddetmek için: RED {qid_free}"
    )
    return result


def job_publish() -> dict:
    """08:30 — send approved drafts; push snapshot to the web demo."""
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}

    sent, failed, blocked = [], [], []
    current_snapshot = _load_current_snapshot()
    for item in broadcast.get_approved_unsent():
        problems = _queue_snapshot_problems(item, current_snapshot)
        if problems:
            error = "snapshot mismatch: " + "; ".join(problems)
            broadcast.mark_sent(item["id"], error=error)
            blocked.append(item["id"])
            continue
        premium = item["kind"] == "daily_premium"
        ok = send_to_channel(
            item["text"],
            queue_id=item["id"],
            premium=premium,
            snapshot_id=item.get("snapshot_id"),
        )
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

    # Web publication is coupled to an approved, successfully delivered
    # edition. Never expose a newly generated snapshot merely because the
    # scheduled publisher ran while approval was still pending.
    pushed = False
    if sent and not failed and not blocked:
        import time as _time

        _t_web = _time.perf_counter()
        pushed = _push_snapshot_to_web(current_snapshot)
        logger.info(
            "pipeline timing: web snapshot push = %.2fs (ok=%s)",
            _time.perf_counter() - _t_web,
            pushed,
        )
    elif pending:
        logger.info("web snapshot held: %d draft(s) still await approval", len(pending))
    if failed:
        notify_admin(f"❌ Gönderim hatası: {failed} — tg_delivery_log'a bak.")
    return {
        "sent": sent,
        "failed": failed,
        "blocked": blocked,
        "web_pushed": pushed,
        "pending_unapproved": len(pending),
    }


def _load_current_snapshot() -> dict | None:
    from distribution.snapshot_builder import EXPORT_DIR, read_json_object

    for path in (EXPORT_DIR / "snapshot_en_latest.json", EXPORT_DIR / "snapshot_latest.json"):
        try:
            snapshot = read_json_object(path)
        except (FileNotFoundError, OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
            continue
        if not validate_snapshot(snapshot):
            return snapshot
    return None


def _queue_snapshot_problems(item: dict, snapshot: dict | None) -> list[str]:
    if snapshot is None:
        return ["current snapshot unavailable"]
    today = _vienna_now().date().isoformat()
    problems: list[str] = []
    if item.get("snapshot_id") != snapshot.get("snapshot_id"):
        problems.append("snapshot_id differs")
    if item.get("snapshot_date") != today or snapshot.get("date") != today:
        problems.append("snapshot date is stale")
    if int(item.get("snapshot_universe") or 0) < expected_universe():
        problems.append("queue universe is incomplete")
    if int(snapshot.get("universe") or 0) < expected_universe():
        problems.append("current universe is incomplete")
    if item.get("candidate_hash") != snapshot.get("candidate_hash"):
        problems.append("candidate_hash differs")
    return problems


def _push_snapshot_to_web(snapshot: dict | None = None) -> bool:
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
        if snapshot and snap.get("snapshot_id") != snapshot.get("snapshot_id"):
            logger.error("web snapshot push refused: source snapshot differs from current snapshot")
            return False
        # Public file: yesterday's top-3 (premium fields stripped) + full karne.
        public = demo_view(snap, max_candidates=len(snap.get("candidates", [])))
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

            hook_result = subprocess.run(shlex.split(hook), timeout=120, check=False)
            if hook_result.returncode != 0:
                # 2026-08-03 finding: this return code used to be discarded
                # entirely (check=False with no inspection), so a failed
                # git commit/push (e.g. a dirty working tree blocking the
                # commit) still made _push_snapshot_to_web report success —
                # Telegram and the web silently went out of sync.
                logger.error("web publish hook failed (exit %d): %s", hook_result.returncode, hook)
                return False
        deploy_hook = os.getenv("FINPILOT_VERCEL_DEPLOY_HOOK_URL", "").strip()
        if deploy_hook:
            request = urllib.request.Request(deploy_hook, data=b"", method="POST")
            with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
                if response.status < 200 or response.status >= 300:
                    logger.error("Vercel deploy hook returned HTTP %s", response.status)
                    return False
        elif os.getenv("FINPILOT_REQUIRE_VERCEL_DEPLOY", "1") == "1":
            logger.error("web snapshot written locally but Vercel deploy hook is not configured")
            return False
        return True
    except Exception as exc:
        logger.error("web snapshot push failed: %s", exc)
        return False


def job_weekly() -> dict:
    """Sunday — weekly summary draft into the queue."""
    if not distribution_enabled():
        return {"skipped": "distribution disabled"}
    today = _vienna_now().date()
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
    # Same tag-safe truncation as job_draft's admin preview — see comment there.
    import re as _re

    _weekly_preview = _re.sub(r"<[^>]+>", "", text)[:1200]
    notify_admin(
        f"🗓 Haftalık özet taslağı hazır (#{qid}).\n\n{_weekly_preview}\n\nONAYLA {qid} / RED {qid}"
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


# ── Event-driven draft trigger (manual/ad-hoc scan completion) ───────────────
# The 07:50 Vienna cron only catches automated mornings. When the daily scan
# is instead run manually at an arbitrary time — very common in practice —
# job_draft() never fires and that whole day's brief silently never gets
# queued (only a warning DM, no retry later). This hook is called from
# api/routers/scan.py right after a scan persists its distribution export,
# so a draft gets queued shortly after any sufficiently-large scan completes,
# regardless of wall-clock time.

_DEFAULT_MIN_UNIVERSE_FOR_DRAFT = 100


def maybe_trigger_draft_after_scan(universe: int) -> dict:
    """Best-effort: queue today's draft right after a manual scan finishes.

    Guards (any failure = silent no-op, never raises):
      - FINPILOT_ENABLE_DISTRIBUTION=1
      - universe >= FINPILOT_DIST_MIN_UNIVERSE_FOR_DRAFT (default 100) —
        skips tiny/manual test scans so they don't spam a draft.
      - today is a trading day.
      - no daily% entry already queued for today — avoids re-drafting every
        time the same day gets scanned more than once. Use
        scripts/dist_live_test.py draft to force a manual re-draft.
    """
    try:
        if not distribution_enabled():
            return {"skipped": "distribution disabled"}

        min_universe = int(
            os.getenv("FINPILOT_DIST_MIN_UNIVERSE_FOR_DRAFT", str(_DEFAULT_MIN_UNIVERSE_FOR_DRAFT))
        )
        if universe < min_universe:
            return {"skipped": f"universe {universe} < min {min_universe}"}

        today = _vienna_now().date()
        if not is_trading_day(today):
            return {"skipped": "not a trading day"}

        from distribution.store import ensure_tables, get_conn

        ensure_tables()
        with get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM broadcast_queue WHERE brief_date=? AND kind LIKE 'daily%'",
                (today.isoformat(),),
            ).fetchone()
        if row and row[0] > 0:
            return {"skipped": "already drafted today"}

        logger.info(
            "Event-driven draft trigger: scan universe=%d, queuing today's brief.", universe
        )
        return job_draft()
    except Exception as exc:  # pragma: no cover - defensive, never break the caller
        logger.warning("maybe_trigger_draft_after_scan failed (non-fatal): %s", exc)
        return {"error": str(exc)}


def maybe_run_shadow_scorecard_after_scan(universe: int) -> dict:
    """Best-effort: tarama sonrası gölge skor kartını arka planda güncelle.

    daily_shadow_update.py'yi ayrı süreçte (fire-and-forget) başlatır:
    price_cache tazele → shadow_scorecard (çoklu benchmark) → çok-pencere geçmişi.
    Env-gated (FINPILOT_ENABLE_SHADOW_SCORECARD=1). Hiçbir başarısızlık çağıranı bozmaz;
    scan HTTP yanıtını bloklamaz (ayrı süreç).
    """
    try:
        if os.getenv("FINPILOT_ENABLE_SHADOW_SCORECARD", "0") != "1":
            return {"skipped": "disabled"}
        min_universe = int(os.getenv("FINPILOT_DIST_MIN_UNIVERSE_FOR_DRAFT", "100"))
        if universe < min_universe:
            return {"skipped": f"universe {universe} < {min_universe}"}

        import subprocess  # noqa: PLC0415
        import sys  # noqa: PLC0415

        script = Path("daily_shadow_update.py")
        if not script.exists():
            return {"skipped": "daily_shadow_update.py not found"}
        log_path = Path("data/shadow/daily_update.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logf = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 - Popen'a devrediliyor
        subprocess.Popen([sys.executable, str(script)], stdout=logf, stderr=logf)  # noqa: S603
        logger.info("shadow scorecard update launched (universe=%d)", universe)
        return {"launched": True}
    except Exception as exc:  # pragma: no cover - defensive, never break the caller
        logger.warning("maybe_run_shadow_scorecard_after_scan failed (non-fatal): %s", exc)
        return {"error": str(exc)}


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

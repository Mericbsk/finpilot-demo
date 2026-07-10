"""E6/E7 — Yedekleme, bütünlük denetimi ve arşiv süreklilik alarmı.

job_backup()        — Pazar 20:00: DB'leri backups/YYYY-MM-DD/'ye kopyala,
                      kopyalar üzerinde PRAGMA integrity_check, 14 günden
                      eskileri sil, sonucu DM'le.
verify_backup()     — restore provası: yedeği aç, tablo/kayıt say.
job_archive_check() — her gün 22:00: işlem günüyse bugünün scan export'u ve
                      yayın kaydı düşmüş mü? Düşmediyse DM (sessiz ölüm yok).
"""

from __future__ import annotations

import logging
import os
import shutil
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

BACKUP_ROOT = Path(os.getenv("FINPILOT_BACKUP_DIR", "backups"))
_DB_SOURCES = [
    Path(os.getenv("FINPILOT_DB_PATH", "data/finpilot.db")),
    Path(os.getenv("FINPILOT_DIST_DB", "data/distribution.db")),
]
RETENTION_DAYS = 14


def _integrity(db_path: Path) -> str:
    """PRAGMA integrity_check sonucu ('ok' beklenir)."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=10)
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            return str(row[0]) if row else "no result"
        finally:
            conn.close()
    except Exception as exc:
        return f"ERROR: {exc}"


def job_backup(notify: bool = True) -> dict:
    """Haftalık yedek + bütünlük denetimi + eski yedek temizliği."""
    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    dest = BACKUP_ROOT / today
    dest.mkdir(parents=True, exist_ok=True)

    results: dict[str, str] = {}
    for src in _DB_SOURCES:
        if not src.exists():
            results[src.name] = "missing (skipped)"
            continue
        target = dest / src.name
        try:
            # canlı SQLite'ı güvenli kopyala: sqlite backup API (kilit-farkında)
            src_conn = sqlite3.connect(src, timeout=15)
            dst_conn = sqlite3.connect(target)
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()
            results[src.name] = _integrity(target)
        except Exception as exc:
            results[src.name] = f"BACKUP FAILED: {exc}"

    pruned = _prune_old()

    ok = all(v == "ok" for v in results.values() if not v.startswith("missing"))
    summary = " · ".join(f"{k}: {v}" for k, v in results.items())
    msg = f"{'✅' if ok else '❌'} Haftalık yedek ({today}): {summary}" + (
        f" · {pruned} eski yedek silindi" if pruned else ""
    )
    logger.info(msg)
    if notify:
        try:
            from distribution.telegram_client import notify_admin

            notify_admin(msg)
        except Exception:  # pragma: no cover
            pass
    return {"ok": ok, "results": results, "pruned": pruned, "dest": str(dest)}


def _prune_old() -> int:
    if not BACKUP_ROOT.exists():
        return 0
    cutoff = datetime.now(tz=UTC) - timedelta(days=RETENTION_DAYS)
    removed = 0
    for d in BACKUP_ROOT.iterdir():
        if not d.is_dir():
            continue
        try:
            when = datetime.strptime(d.name, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            continue
        if when < cutoff:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    return removed


def verify_backup(backup_dir: Path | str | None = None) -> dict:
    """Restore provası: en son yedeği aç, tablo ve kayıt say (salt-okunur)."""
    root = Path(backup_dir) if backup_dir else BACKUP_ROOT
    dirs = sorted([d for d in root.iterdir() if d.is_dir()]) if root.exists() else []
    if not dirs:
        return {"ok": False, "error": "no backups found"}
    latest = dirs[-1]
    report: dict[str, dict] = {}
    for db in latest.glob("*.db"):
        try:
            conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
            try:
                tables = [
                    r[0]
                    for r in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                ]
                counts = {}
                for t in tables[:20]:
                    try:
                        counts[t] = conn.execute(
                            f"SELECT COUNT(*) FROM {t}"  # nosec B608 - t sqlite_master'dan  # noqa: S608
                        ).fetchone()[0]
                    except Exception:
                        counts[t] = "?"
                report[db.name] = {"tables": len(tables), "counts": counts}
            finally:
                conn.close()
        except Exception as exc:
            report[db.name] = {"error": str(exc)}
    ok = all("error" not in v for v in report.values()) and bool(report)
    return {"ok": ok, "backup": latest.name, "report": report}


def job_archive_check() -> dict:
    """E7 — 22:00: bugünün veri/yayın izleri düşmüş mü? (işlem günlerinde)."""
    from distribution.jobs import distribution_enabled
    from distribution.market_calendar import is_trading_day

    if not distribution_enabled():
        return {"skipped": "distribution disabled"}

    try:
        from zoneinfo import ZoneInfo

        now_v = datetime.now(tz=ZoneInfo("Europe/Vienna"))
    except Exception:  # pragma: no cover
        now_v = datetime.now(tz=UTC)
    today = now_v.date()
    if not is_trading_day(today):
        return {"skipped": "not a trading day"}

    problems: list[str] = []

    # 1) Scan export bugün yazıldı mı?
    from distribution.snapshot_builder import SCAN_EXPORT_LATEST

    dated = SCAN_EXPORT_LATEST.parent / f"scan_export_{today.isoformat()}.json"
    if not dated.exists():
        problems.append("bugünün scan export'u yok")

    # 2) Bugün bir daily brif 'sent' oldu mu (ya da bilinçli sessiz mi)?
    try:
        from distribution.store import ensure_tables, get_conn

        ensure_tables()
        with get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM broadcast_queue WHERE brief_date=? "
                "AND kind LIKE 'daily%' AND status='sent'",
                (today.isoformat(),),
            ).fetchone()
        if row[0] == 0:
            problems.append("bugün yayınlanmış brif yok (onaysız kaldıysa bu beklenen davranıştır)")
    except Exception as exc:
        problems.append(f"kuyruk okunamadı: {exc}")

    if problems:
        try:
            from distribution.telegram_client import notify_admin

            notify_admin("🌙 22:00 arşiv kontrolü: " + " · ".join(problems))
        except Exception:  # pragma: no cover
            pass
        return {"ok": False, "problems": problems}
    return {"ok": True}

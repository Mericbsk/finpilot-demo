"""Archive bridge — writes each published day's public candidates into
signals_archive and watches archive continuity.

Why: the old archive chain (watchlist API POST /archive → JSON → migrate
script) died with the always-on API architecture (last write 2026-05-22).
This module gives the manual publish flow its own direct, dependency-free
archive step so the karne/resolver pipeline keeps receiving data.

Rules:
  * idempotent — re-publishing the same day never duplicates rows
    (deterministic id = sha256(symbol|date));
  * archived rows start as resolved_status='new' and are later labelled by
    scripts/resolve_open_signals.py (dual-label standard);
  * a continuity check warns LOUDLY when the archive stops growing — the
    silent-death class that went unnoticed for two months must stay dead.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "finpilot.db"

MAX_SILENT_TRADING_DAYS = 2  # archive not growing for this many trading days → alarm


def _candidate_id(symbol: str, date_str: str) -> str:
    digest = hashlib.sha256(f"{symbol}|{date_str}".encode()).hexdigest()[:12]
    return f"sig_{digest}"


def archive_snapshot_candidates(
    snap: dict[str, Any],
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Insert the snapshot's public candidates into signals_archive.

    Returns {"archived": n, "skipped": n, "date": ...}. Raises on DB errors —
    an archive failure must be visible, never silent.
    """
    path = Path(db_path) if db_path else DEFAULT_DB
    date_str = str(snap.get("date") or date.today().isoformat())
    candidates = snap.get("candidates") or []
    ts = datetime.now(tz=UTC).isoformat()

    archived = skipped = 0
    con = sqlite3.connect(path)
    try:
        for cand in candidates:
            symbol = str(cand.get("ticker") or cand.get("symbol") or "").upper()
            if not symbol:
                continue
            row_id = _candidate_id(symbol, date_str)
            enrich = _watchlist_enrichment(con, symbol, date_str)
            metrics = cand.get("metrics") or {}
            resolver_fields = {
                # keys scripts/resolve_open_signals.py reads from payload_json
                "signal_date": date_str,
                "entry_price": enrich.get("entry_price") or metrics.get("price"),
                "stop_loss": enrich.get("stop_loss") or metrics.get("stop_loss"),
                "take_profit": enrich.get("take_profit") or metrics.get("take_profit"),
                "conviction_tier": enrich.get("conviction_tier") or cand.get("grade"),
            }
            payload = json.dumps(
                {"source": "publish_archive_bridge", "date": date_str, **resolver_fields, **cand},
                ensure_ascii=False,
                default=str,
            )
            cur = con.execute(
                "INSERT OR IGNORE INTO signals_archive "
                "(id, symbol, ts, score, finpilot_score, payload_json, resolved_status) "
                "VALUES (?, ?, ?, ?, ?, ?, 'new')",
                (
                    row_id,
                    symbol,
                    ts,
                    _as_float(enrich.get("score") or metrics.get("conviction_prob")),
                    _as_float(enrich.get("finpilot_score")),
                    payload,
                ),
            )
            if cur.rowcount:
                archived += 1
            else:
                skipped += 1
        con.commit()
    finally:
        con.close()
    logger.info("archive bridge: %d archived, %d already present (%s)", archived, skipped, date_str)
    return {"archived": archived, "skipped": skipped, "date": date_str}


def _watchlist_enrichment(con: sqlite3.Connection, symbol: str, date_str: str) -> dict[str, Any]:
    """Pull entry/SL/TP/score for the same symbol+day from watchlist_signals.

    The public snapshot candidate is compliance-stripped; the watchlist row
    carries the numeric fields the resolver needs. Best-effort: returns {}
    when the table or row is missing.
    """
    try:
        row = con.execute(
            "SELECT entry_price, stop_loss, take_profit, score, conviction_tier "
            "FROM watchlist_signals WHERE symbol=? AND signal_date=? "
            "ORDER BY id DESC LIMIT 1",
            (symbol, date_str),
        ).fetchone()
    except sqlite3.Error:
        return {}
    if not row:
        return {}
    return {
        "entry_price": row[0],
        "stop_loss": row[1],
        "take_profit": row[2],
        "score": row[3],
        "conviction_tier": row[4],
    }


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check_archive_continuity(
    db_path: Path | str | None = None,
    max_gap_days: int = MAX_SILENT_TRADING_DAYS,
) -> str | None:
    """Return a human-readable warning when the archive looks stalled, else None.

    Uses calendar days with a weekend allowance: gap > (max_gap_days + 2)
    calendar days counts as stalled regardless of weekday.
    """
    path = Path(db_path) if db_path else DEFAULT_DB
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            row = con.execute("SELECT MAX(ts) FROM signals_archive").fetchone()
        finally:
            con.close()
    except sqlite3.Error as exc:
        return f"signals_archive okunamadı: {exc}"
    last_ts = (row or [None])[0]
    if not last_ts:
        return "signals_archive tamamen boş"
    try:
        last_day = datetime.fromisoformat(str(last_ts)).date()
    except ValueError:
        return f"signals_archive ts alanı bozuk: {last_ts!r}"
    gap = (date.today() - last_day).days
    if gap > max_gap_days + 2:  # +2 = weekend allowance
        return (
            f"signals_archive {gap} gündür büyümüyor (son kayıt {last_day}). "
            "Arşiv köprüsü kopmuş olabilir — publish zincirini kontrol et."
        )
    return None

"""SQLite store for the distribution layer.

Deliberately a SEPARATE database file (data/distribution.db) — the audit
flagged finpilot.db multi-writer lock risk; the distribution layer must not
add another writer to it. WAL mode is enabled for scheduler+bot concurrency.
"""

from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Any

_DB_PATH = Path(os.getenv("FINPILOT_DIST_DB", "data/distribution.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS broadcast_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,              -- daily_free | daily_premium | weekly | correction | holiday
    brief_date TEXT NOT NULL,        -- YYYY-MM-DD
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected | sent | expired
    created_at INTEGER NOT NULL,
    decided_at INTEGER,
    decided_by TEXT,
    sent_at INTEGER,
    error TEXT,
    snapshot_id TEXT,
    snapshot_date TEXT,
    snapshot_universe INTEGER,
    candidate_hash TEXT,
    scan_id TEXT
);
CREATE TABLE IF NOT EXISTS tg_delivery_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    queue_id INTEGER,
    chat_id TEXT NOT NULL,
    telegram_message_id INTEGER,
    snapshot_id TEXT,
    channel TEXT,
    ok INTEGER NOT NULL,
    detail TEXT,
    ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS tg_users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    first_seen INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    source TEXT DEFAULT '',
    premium_interest INTEGER DEFAULT 0,   -- /premium tık sayısı
    premium_status TEXT DEFAULT 'none',   -- none | active | cancelled
    stripe_customer TEXT
);
CREATE TABLE IF NOT EXISTS tg_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    text TEXT NOT NULL,
    ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS demo_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    q1_what_is_it TEXT,
    q2_best_worst TEXT,
    q3_would_pay TEXT,        -- yes | maybe | no
    q3_why TEXT,
    micro TEXT,               -- JSON: mikro anket cevapları
    source TEXT DEFAULT '',
    ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS waitlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    source TEXT DEFAULT 'landing',
    utm TEXT DEFAULT '',
    created_at INTEGER NOT NULL,
    invited_at INTEGER,
    invite_code TEXT
);
CREATE TABLE IF NOT EXISTS beta_invites (
    code TEXT PRIMARY KEY,
    email TEXT,
    created_at INTEGER NOT NULL,
    used_at INTEGER
);
CREATE TABLE IF NOT EXISTS premium_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,             -- checkout_completed | cancelled | refund | invite_sent | kicked
    stripe_customer TEXT,
    email TEXT,
    tg_user_id TEXT,
    detail TEXT,
    ts INTEGER NOT NULL
);
"""


def get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, timeout=10)
    # DELETE (rollback) journal, NOT WAL: WAL's -wal/-shm sidecars desync under
    # OneDrive sync / antivirus locks and corrupt the DB (07-03, 07-15 events).
    # The manual single-writer flow does not need WAL concurrency. See
    # scripts/harden_db.py and FinPilot_Bolum3_StabiliteAudit_2026-07-24.md.
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def ensure_tables() -> None:
    with get_conn() as conn:
        conn.executescript(_SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(tg_delivery_log)")}
        if "telegram_message_id" not in columns:
            conn.execute("ALTER TABLE tg_delivery_log ADD COLUMN telegram_message_id INTEGER")
        queue_columns = {row[1] for row in conn.execute("PRAGMA table_info(broadcast_queue)")}
        for name, sql_type in (
            ("snapshot_id", "TEXT"),
            ("snapshot_date", "TEXT"),
            ("snapshot_universe", "INTEGER"),
            ("candidate_hash", "TEXT"),
            ("scan_id", "TEXT"),
        ):
            if name not in queue_columns:
                conn.execute(f"ALTER TABLE broadcast_queue ADD COLUMN {name} {sql_type}")
        delivery_columns = {row[1] for row in conn.execute("PRAGMA table_info(tg_delivery_log)")}
        if "snapshot_id" not in delivery_columns:
            conn.execute("ALTER TABLE tg_delivery_log ADD COLUMN snapshot_id TEXT")
        if "channel" not in delivery_columns:
            conn.execute("ALTER TABLE tg_delivery_log ADD COLUMN channel TEXT")


def now() -> int:
    return int(time.time())


# ── convenience helpers used by bot / api ────────────────────────────────────


def upsert_tg_user(user_id: str, username: str = "", source: str = "") -> None:
    ensure_tables()
    ts = now()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO tg_users(user_id, username, first_seen, last_seen, source)
               VALUES(?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET last_seen=?, username=COALESCE(NULLIF(?, ''), username)""",
            (user_id, username, ts, ts, source, ts, username),
        )


def log_tg_feedback(user_id: str, text: str) -> None:
    ensure_tables()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tg_feedback(user_id, text, ts) VALUES(?,?,?)",
            (user_id, text, now()),
        )


def bump_premium_interest(user_id: str) -> int:
    ensure_tables()
    with get_conn() as conn:
        conn.execute(
            "UPDATE tg_users SET premium_interest = premium_interest + 1 WHERE user_id=?",
            (user_id,),
        )
        row = conn.execute(
            "SELECT premium_interest FROM tg_users WHERE user_id=?", (user_id,)
        ).fetchone()
    return int(row[0]) if row else 1


def log_premium_event(
    event: str,
    stripe_customer: str = "",
    email: str = "",
    tg_user_id: str = "",
    detail: str = "",
) -> None:
    ensure_tables()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO premium_events(event, stripe_customer, email, tg_user_id, detail, ts)"
            " VALUES(?,?,?,?,?,?)",
            (event, stripe_customer, email, tg_user_id, detail, now()),
        )


def log_delivery(
    queue_id: int | None,
    chat_id: str,
    ok: bool,
    detail: str = "",
    telegram_message_id: int | None = None,
    snapshot_id: str | None = None,
    channel: str = "",
) -> None:
    ensure_tables()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO tg_delivery_log(queue_id, chat_id, telegram_message_id, snapshot_id, channel, ok, detail, ts)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (
                queue_id,
                chat_id,
                telegram_message_id,
                snapshot_id,
                channel,
                1 if ok else 0,
                detail[:500],
                now(),
            ),
        )


def add_demo_feedback(payload: dict[str, Any]) -> int:
    ensure_tables()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO demo_feedback(session_id, q1_what_is_it, q2_best_worst,"
            " q3_would_pay, q3_why, micro, source, ts) VALUES(?,?,?,?,?,?,?,?)",
            (
                payload.get("session_id", ""),
                payload.get("q1", ""),
                payload.get("q2", ""),
                payload.get("q3", ""),
                payload.get("q3_why", ""),
                payload.get("micro", ""),
                payload.get("source", ""),
                now(),
            ),
        )
        return int(cur.lastrowid or 0)


def add_waitlist(email: str, source: str = "landing", utm: str = "") -> bool:
    """Returns True if newly added, False if duplicate."""
    ensure_tables()
    try:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO waitlist(email, source, utm, created_at) VALUES(?,?,?,?)",
                (email.strip().lower(), source, utm, now()),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def waitlist_count() -> int:
    ensure_tables()
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM waitlist").fetchone()
    return int(row[0])

"""Broadcast approval queue.

Flow: draft -> queue(pending) -> admin DM'd -> admin replies
"ONAYLA <id>" / "RED <id>" -> approved/rejected -> publisher sends approved
items at the scheduled publish time. No approval == no publication.
"""

from __future__ import annotations

from typing import Any

from distribution import lint
from distribution.store import ensure_tables, get_conn, now


def queue_draft(kind: str, brief_date: str, text: str) -> int:
    """Lint-check and enqueue a draft. Raises ValueError if lint fails."""
    lint.assert_publishable(text)
    ensure_tables()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO broadcast_queue(kind, brief_date, text, status, created_at)"
            " VALUES(?,?,?,'pending',?)",
            (kind, brief_date, text, now()),
        )
        return int(cur.lastrowid or 0)


def get_pending() -> list[dict[str, Any]]:
    ensure_tables()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, kind, brief_date, text, created_at FROM broadcast_queue"
            " WHERE status='pending' ORDER BY id"
        ).fetchall()
    return [
        {"id": r[0], "kind": r[1], "brief_date": r[2], "text": r[3], "created_at": r[4]}
        for r in rows
    ]


def get_approved_unsent() -> list[dict[str, Any]]:
    ensure_tables()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, kind, brief_date, text FROM broadcast_queue"
            " WHERE status='approved' AND sent_at IS NULL ORDER BY id"
        ).fetchall()
    return [{"id": r[0], "kind": r[1], "brief_date": r[2], "text": r[3]} for r in rows]


def decide(queue_id: int, approve: bool, decided_by: str) -> bool:
    ensure_tables()
    status = "approved" if approve else "rejected"
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE broadcast_queue SET status=?, decided_at=?, decided_by=?"
            " WHERE id=? AND status='pending'",
            (status, now(), decided_by, queue_id),
        )
    return cur.rowcount > 0


def mark_sent(queue_id: int, error: str = "") -> None:
    ensure_tables()
    with get_conn() as conn:
        if error:
            conn.execute("UPDATE broadcast_queue SET error=? WHERE id=?", (error[:500], queue_id))
        else:
            conn.execute(
                "UPDATE broadcast_queue SET status='sent', sent_at=? WHERE id=?",
                (now(), queue_id),
            )


def expire_stale(older_than_hours: int = 20) -> int:
    """Expire pending drafts older than N hours (yesterday's unapproved brief
    must never be published today)."""
    ensure_tables()
    cutoff = now() - older_than_hours * 3600
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE broadcast_queue SET status='expired' WHERE status='pending' AND created_at<?",
            (cutoff,),
        )
    return cur.rowcount


def get_last_sent(kind_prefix: str = "daily") -> dict[str, Any] | None:
    ensure_tables()
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, kind, brief_date, text, sent_at FROM broadcast_queue"
            " WHERE status='sent' AND kind LIKE ? ORDER BY sent_at DESC LIMIT 1",
            (kind_prefix + "%",),
        ).fetchone()
    if not row:
        return None
    return {"id": row[0], "kind": row[1], "brief_date": row[2], "text": row[3], "sent_at": row[4]}


def drop(queue_id: int, by: str = "admin") -> bool:
    """Pending YA DA approved (gönderilmemiş) taslağı iptal et."""
    ensure_tables()
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE broadcast_queue SET status='rejected', decided_at=?, decided_by=?"
            " WHERE id=? AND status IN ('pending','approved') AND sent_at IS NULL",
            (now(), by, queue_id),
        )
    return cur.rowcount > 0

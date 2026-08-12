"""VS-01 Phase 2 (+ Phase 8 content expansion) — export real, resolved FinPilot
signals as FinSense Cases.

Sibling of `Finsense/academy/export_lessons.py`'s export pattern, applied to a
new data type. See docs/strategy/FinSense_Vertical_Slice_Specification_v1_2026-08-11.md
§2 (Case source) and §2.3 (Case #001 selection criteria).

Design (LOCK-02, LOCK-03 — Contract):
  - Reads `signals_archive` in `data/finpilot.db` READ-ONLY. Never writes back to it.
  - `actual_direction` / `actual_return_pct` are copied verbatim from FinPilot's own
    barrier resolver (`resolved_status_barrier` / `resolved_pct_barrier`) — this
    script does not compute or reinterpret the outcome.
  - The case `snapshot` is built ONLY from fields knowable at signal time
    (entry price, score, regime, sentiment, risk/reward, technical reason) —
    no fields from *after* the signal are included.
  - Case selection remains manual and explicit (a fixed registry of signal ids
    below), not a scan or a "pick the best one" heuristic — see §2.3:
    automation comes later, after a human test on a handful of cases, not
    before. Phase 8 (2026-08-12) added 4 more cases to CASE_REGISTRY on top of
    Case #001 — still 5 total, still hand-picked, still short of the "20 case"
    automation threshold that was explicitly deferred in the Phase 8 plan.

Usage:
    python scripts/export_resolved_cases.py            # writes ALL registered cases to DB + JSON artifacts
    python scripts/export_resolved_cases.py --check     # dry run, prints only
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from auth.database import Database  # noqa: E402

SIGNALS_DB = _ROOT / "data" / "finpilot.db"
CASE_ARTIFACT_DIR = _ROOT / "data" / "finsense_cases"

# The real barrier-resolution window used by FinPilot's own resolver
# (see scripts/resolve_open_signals.py: "TP / SL / 21-trading-day expiry").
# fs_cases.horizon_days mirrors this — FinSense does not invent its own horizon.
BARRIER_HORIZON_TRADING_DAYS = 21

# ---------------------------------------------------------------------------
# Case registry — manually selected (§2.3 criteria), not scanned/auto-picked.
# Each entry: (case_number, signal_id, one-line rationale). All five share the
# same quality bar as Case #001: full BUY-signal payload (entry/stop/target/
# risk-reward), cleanly barrier-resolved (win or loss, not expired/pending),
# moderate — not outlier — return, and a recognizable enough company that a
# non-specialist can engage with the case without needing domain expertise.
# Deliberately mixed win/loss (3 UP outcomes, 2 DOWN) and mixed sectors, so
# Phase 8 testers don't all see the same direction or the same industry.
# ---------------------------------------------------------------------------
CASE_001_SIGNAL_ID = "sig_13babfa21bdb"  # Goldman Sachs, 2026-05-22, resolved_win +1.90%

CASE_REGISTRY: list[tuple[int, str, str]] = [
    (1, CASE_001_SIGNAL_ID, "GS — financials, resolved_win +1.90%, original VS-01 case"),
    (2, "sig_129fa1c99101", "V (Visa) — payments, resolved_loss -0.38%, clean small loss"),
    (3, "sig_a3127cfe2567", "WMT (Walmart) — retail, resolved_loss -0.40%, clean small loss"),
    (4, "sig_2cea4c1ac31e", "XOM (ExxonMobil) — energy, resolved_win +1.99%"),
    (5, "sig_e2730df15470", "MAR (Marriott) — hospitality, resolved_win +1.71%"),
]


def _load_signal(signal_id: str) -> sqlite3.Row:
    if not SIGNALS_DB.exists():
        raise FileNotFoundError(f"signals_archive DB not found at {SIGNALS_DB}")
    conn = sqlite3.connect(str(SIGNALS_DB))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT id, symbol, ts, score, resolved_status_barrier, resolved_pct_barrier, "
            "payload_json FROM signals_archive WHERE id = ?",
            (signal_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise ValueError(f"signal {signal_id} not found in signals_archive")
    if row["resolved_status_barrier"] not in ("resolved_win", "resolved_loss"):
        raise ValueError(
            f"signal {signal_id} is not cleanly barrier-resolved "
            f"(status={row['resolved_status_barrier']!r}) — §2.3 requires "
            "'outcome kesin çözülmüş'"
        )
    return row


def build_case(case_number: int = 1, signal_id: str = CASE_001_SIGNAL_ID) -> tuple[dict, dict]:
    """Returns (case_dict, outcome_dict) built from one real resolved signal."""
    row = _load_signal(signal_id)
    payload = json.loads(row["payload_json"] or "{}")

    asset = row["symbol"]
    event_ts = row["ts"]
    case_id = f"case-{case_number:03d}-{asset.lower()}-{event_ts[:10]}"

    # --- Snapshot: T0-only, no post-event data (LOCK-03) ---
    snapshot = {
        "asset": asset,
        "event_timestamp": event_ts,
        "price_at_event": payload.get("entry_price"),
        "signal_score": row["score"],
        "signal_type": payload.get("signal"),
        "regime": payload.get("regime"),
        "sentiment": payload.get("sentiment"),
        "risk_reward": payload.get("risk_reward"),
        "technical_context": payload.get("explanation"),
        "stop_loss": payload.get("stop_loss"),
        "take_profit": payload.get("take_profit"),
    }

    context = (
        f"On {event_ts[:10]}, FinPilot's scanner flagged {asset} with a "
        f"{payload.get('signal', 'BUY')} signal. The read was a "
        f"{payload.get('regime', 'n/a')} regime with {str(payload.get('sentiment', 'n/a')).lower()} "
        f"sentiment, a risk/reward ratio of {payload.get('risk_reward')} "
        f"(stop-loss ${payload.get('stop_loss')}, take-profit ${payload.get('take_profit')} "
        f"against an entry near ${payload.get('entry_price')}). "
        f"Technical read: {payload.get('explanation')}. No specific news catalyst was recorded — "
        "this was a technical, trend-following read."
    )

    outcome_rule = {
        "type": "finpilot_barrier",
        "entry_price": payload.get("entry_price"),
        "stop_loss": payload.get("stop_loss"),
        "take_profit": payload.get("take_profit"),
        "expiry_trading_days": BARRIER_HORIZON_TRADING_DAYS,
    }

    case = {
        "id": case_id,
        "source_signal_id": row["id"],
        "asset": asset,
        "event_timestamp": event_ts,
        "snapshot": snapshot,
        "context": context,
        "horizon_days": BARRIER_HORIZON_TRADING_DAYS,
        "outcome_rule": outcome_rule,
        "resolution_method": "finpilot_barrier",
        # "open" = still accepting new predictions from FinSense users (VS-01's
        # whole point: the user predicts on a case whose real-world outcome is
        # already known to FinPilot but not yet revealed to them). "status" here
        # describes prediction-acceptance, not outcome-availability — whether the
        # outcome itself is known lives separately in fs_outcomes (LOCK-03/§0).
        "status": "open",
    }

    # --- Outcome: copied verbatim from FinPilot's resolver (LOCK-02) ---
    actual_direction = "UP" if row["resolved_status_barrier"] == "resolved_win" else "DOWN"
    # NOTE (honesty, not fabrication): signals_archive does not store the exact
    # intraday timestamp the barrier was hit — only that it resolved before the
    # 21-trading-day expiry. resolved_at below is therefore a documented
    # UPPER-BOUND approximation (event_timestamp + horizon), not a claimed exact
    # fact. It is used only for internal PENDING/RESOLVED bookkeeping; the outcome
    # reveal screen shows direction/return, never this timestamp as if precise.
    event_dt = datetime.fromisoformat(event_ts.replace("Z", "+00:00"))
    approx_resolved_at = event_dt + timedelta(days=BARRIER_HORIZON_TRADING_DAYS)

    outcome = {
        "case_id": case_id,
        "actual_direction": actual_direction,
        "actual_return_pct": row["resolved_pct_barrier"],
        "resolution_method": "finpilot_barrier",
        "resolved_at": approx_resolved_at.isoformat(),
        "resolved_at_is_approximate": True,  # not persisted as a DB column — audit note only
    }

    return case, outcome


def load_into_db(case: dict, outcome: dict) -> None:
    db = Database()
    db.initialize()
    now = datetime.now(UTC).isoformat()
    with db.connection() as conn:
        existing = conn.execute("SELECT id FROM fs_cases WHERE id = ?", (case["id"],)).fetchone()
        if existing:
            print(f"fs_cases already has {case['id']} — skipping insert (idempotent).")
        else:
            conn.execute(
                "INSERT INTO fs_cases (id, source_signal_id, asset, event_timestamp, "
                "snapshot, context, horizon_days, outcome_rule, resolution_method, "
                "status, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    case["id"],
                    case["source_signal_id"],
                    case["asset"],
                    case["event_timestamp"],
                    json.dumps(case["snapshot"], ensure_ascii=False),
                    case["context"],
                    case["horizon_days"],
                    json.dumps(case["outcome_rule"], ensure_ascii=False),
                    case["resolution_method"],
                    case["status"],
                    now,
                ),
            )
            print(f"Inserted fs_cases row: {case['id']}")

        existing_outcome = conn.execute(
            "SELECT case_id FROM fs_outcomes WHERE case_id = ?", (outcome["case_id"],)
        ).fetchone()
        if existing_outcome:
            print(f"fs_outcomes already has {outcome['case_id']} — skipping insert (idempotent).")
        else:
            conn.execute(
                "INSERT INTO fs_outcomes (case_id, actual_direction, actual_return_pct, "
                "resolution_method, resolved_at) VALUES (?,?,?,?,?)",
                (
                    outcome["case_id"],
                    outcome["actual_direction"],
                    outcome["actual_return_pct"],
                    outcome["resolution_method"],
                    outcome["resolved_at"],
                ),
            )
            print(f"Inserted fs_outcomes row: {outcome['case_id']}")


def write_artifact(case: dict, outcome: dict) -> Path:
    CASE_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CASE_ARTIFACT_DIR / f"{case['id']}.json"
    out_path.write_text(
        json.dumps({"case": case, "outcome": outcome}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out_path


def main(argv: list[str]) -> int:
    check_only = "--check" in argv

    for case_number, signal_id, rationale in CASE_REGISTRY:
        print(f"\n{'=' * 70}\nCase #{case_number:03d} — {rationale}\n{'=' * 70}")
        case, outcome = build_case(case_number, signal_id)

        print("=== Case ===")
        print(json.dumps(case, indent=2, ensure_ascii=False, default=str))
        print("=== Outcome ===")
        print(json.dumps(outcome, indent=2, ensure_ascii=False, default=str))

        if check_only:
            print(f"\n--check: dry run, case {case['id']} not written.")
            continue

        artifact_path = write_artifact(case, outcome)
        print(f"\nWrote artifact: {artifact_path}")
        load_into_db(case, outcome)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Snapshot data contract (versioned).

The snapshot is the single artefact produced once per trading day and
consumed by the web demo, the free brief and the premium brief.
"""

from __future__ import annotations

from typing import Any

SCHEMA_VERSION = 2  # v2: +concept, +edition_no, +context_line (Ledger landing, additive/optional)

GRADES = ("A", "B", "C")

# Required keys, with type checks. ``candidates`` entries validated separately.
_TOP_LEVEL_REQUIRED: dict[str, type] = {
    "schema": int,
    "snapshot_id": str,
    "candidate_hash": str,
    "date": str,  # YYYY-MM-DD
    "generated_at": str,  # ISO timestamp
    "universe": int,
    "scan_result_count": int,
    "candidates": list,
    "karne": (dict, type(None)),  # type: ignore[dict-item]
}

_CANDIDATE_REQUIRED: dict[str, type] = {
    "ticker": str,
    "grade": str,
    "prob_band": str,  # e.g. "~60%" — human band, never false precision
    "badges": list,
    "rationale": str,
    "premium_only": bool,
}


def validate_snapshot(snap: dict[str, Any]) -> list[str]:
    """Return a list of human-readable problems; empty list == valid."""
    errors: list[str] = []
    for key, typ in _TOP_LEVEL_REQUIRED.items():
        if key not in snap:
            errors.append(f"missing top-level key: {key}")
        elif not isinstance(snap[key], typ):
            errors.append(f"bad type for {key}: {type(snap[key]).__name__}")

    if snap.get("schema") != SCHEMA_VERSION:
        errors.append(f"schema version mismatch: {snap.get('schema')} != {SCHEMA_VERSION}")

    if "scan_id" in snap and snap["scan_id"] is not None and not isinstance(snap["scan_id"], str):
        errors.append(f"bad type for scan_id: {type(snap['scan_id']).__name__}")

    for i, cand in enumerate(snap.get("candidates", [])):
        if not isinstance(cand, dict):
            errors.append(f"candidate[{i}] is not a dict")
            continue
        for key, typ in _CANDIDATE_REQUIRED.items():
            if key not in cand:
                errors.append(f"candidate[{i}] missing: {key}")
            elif not isinstance(cand[key], typ):
                errors.append(f"candidate[{i}] bad type for {key}")
        grade = cand.get("grade")
        if grade is not None and grade not in GRADES:
            errors.append(f"candidate[{i}] invalid grade: {grade}")

    # Karne is optional (may be missing on data-quality bad days) but when
    # present must carry the daily totals used by the free brief teaser line.
    karne = snap.get("karne")
    if isinstance(karne, dict):
        if "toplam_aday_bugun" not in karne:
            errors.append("karne missing toplam_aday_bugun")

    return errors


def free_view(snap: dict[str, Any], max_candidates: int = 2) -> dict[str, Any]:
    """Free-tier projection: first ``max_candidates`` non-premium candidates.

    The full candidate count stays visible via karne.toplam_aday_bugun —
    transparency, not artificial scarcity.
    """
    out = dict(snap)
    visible = [c for c in snap.get("candidates", []) if not c.get("premium_only")]
    out["candidates"] = [_strip_premium_fields(c) for c in visible[:max_candidates]]
    return out


def demo_view(snap: dict[str, Any], max_candidates: int = 3) -> dict[str, Any]:
    """Web-demo projection: yesterday's TOP-N (premium fields stripped).

    The demo shows the frozen top-3 with hindsight; the free Telegram brief
    shows fewer, same-day — different products.
    """
    out = dict(snap)
    cands = [_strip_premium_fields(c) for c in snap.get("candidates", [])[:max_candidates]]
    for c in cands:
        c["premium_only"] = False
    out["candidates"] = cands
    out["web_context"] = [_strip_premium_fields(item) for item in snap.get("web_context", [])]
    return out


def _strip_premium_fields(cand: dict[str, Any]) -> dict[str, Any]:
    c = dict(cand)
    c.pop("risk_note", None)
    c.pop("factor_detail", None)
    metrics = c.get("metrics")
    if isinstance(metrics, dict):
        c["metrics"] = {
            key: value
            for key, value in metrics.items()
            if key not in {"risk_reward", "stop_loss", "take_profit", "stop_loss_percent"}
        }
    return c

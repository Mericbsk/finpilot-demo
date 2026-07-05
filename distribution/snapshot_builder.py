"""Build the daily distribution snapshot from scan results.

Input:  the enriched scan-result rows (written by api/routers/scan.py hook to
        data/distribution/scan_export_latest.json) — NOT data/daily_reports
        (legacy BUY/stop/TP language, no tier/conviction fields).
Output: versioned snapshot dict (schema.py) — the single artefact consumed by
        web demo + free brief + premium brief.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

UTC = UTC

from distribution.rationale import build_rationale, extract_badges, prob_band
from distribution.schema import SCHEMA_VERSION, validate_snapshot

EXPORT_DIR = Path(os.getenv("FINPILOT_DIST_DIR", "data/distribution"))
SCAN_EXPORT_LATEST = EXPORT_DIR / "scan_export_latest.json"

_GRADE_ORDER = {"A": 0, "B": 1, "C": 2}
FREE_CANDIDATES = 2  # first N candidates are visible in the free tier
MAX_CANDIDATES = 10


def config_sha() -> str:
    """Stamp of active feature flags (+ git sha when available)."""
    flags = sorted(f"{k}={v}" for k, v in os.environ.items() if k.startswith("FINPILOT_ENABLE"))
    base = ";".join(flags)
    try:
        git = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.strip()
    except Exception:
        git = ""
    return hashlib.sha256(f"{git}|{base}".encode()).hexdigest()[:12] + (f"@{git}" if git else "")


def _grade_of(row: dict[str, Any]) -> str | None:
    """Map a scan row to a public Grade — the SINGLE user-facing label."""
    conv = str(row.get("conviction_tier") or "").strip().upper()
    if conv in ("A", "B", "C"):
        return conv
    tier = str(row.get("tier") or "").strip().upper()
    if tier == "CONFIRM":
        return "B"
    if tier == "TRIGGER":
        return "C"
    return None


def _sort_key(row: dict[str, Any]) -> tuple:
    grade = _grade_of(row) or "Z"
    prob = float(row.get("conviction_prob") or 0.0)
    score = float(row.get("composite_score") or row.get("score") or 0.0)
    return (_GRADE_ORDER.get(grade, 9), -prob, -score)


def _risk_note(row: dict[str, Any]) -> str:
    notes: list[str] = []
    try:
        atr = float(row.get("atr_pct") or 0.0)
        if atr >= 6:
            notes.append("volatilite çok yüksek (geniş günlük aralık)")
    except (TypeError, ValueError):
        pass
    if float(row.get("squeeze_factor") or 0) >= 0.5:
        notes.append("squeeze senaryoları iki yönlü sert hareket üretebilir")
    price = row.get("price")
    try:
        if price is not None and float(price) < 5:
            notes.append("düşük fiyatlı hisse — likidite/spread riski")
    except (TypeError, ValueError):
        pass
    return (
        "; ".join(notes) if notes else "standart izleme riski; pozisyon disiplini okuyucuya aittir"
    )


def build_snapshot(
    scan_rows: list[dict[str, Any]],
    universe: int,
    karne: dict[str, Any] | None = None,
    date_str: str | None = None,
    lang: str = "tr",
) -> dict[str, Any]:
    date_str = date_str or datetime.now(tz=UTC).strftime("%Y-%m-%d")

    graded = [r for r in scan_rows if _grade_of(r)]
    graded.sort(key=_sort_key)
    graded = graded[:MAX_CANDIDATES]

    candidates: list[dict[str, Any]] = []
    grade_totals: dict[str, int] = {}
    for r in scan_rows:
        g = _grade_of(r)
        if g:
            grade_totals[g] = grade_totals.get(g, 0) + 1

    for i, row in enumerate(graded):
        ticker = str(row.get("symbol") or row.get("ticker") or "").upper()
        if not ticker:
            continue
        grade = _grade_of(row) or "C"
        badges = extract_badges(row)
        cand: dict[str, Any] = {
            "ticker": ticker,
            "company": str(row.get("company") or row.get("name") or ""),
            "grade": grade,
            "prob_band": prob_band(float(row.get("conviction_prob") or 0.0)),
            "badges": badges,
            "rationale": build_rationale(ticker, grade, badges, lang=lang),
            "premium_only": i >= FREE_CANDIDATES,
            "risk_note": _risk_note(row),
            "factor_detail": {
                k: row.get(k)
                for k in (
                    "conviction_prob",
                    "tier",
                    "tier_score",
                    "squeeze_factor",
                    "catalyst_factor",
                    "rvol_acceleration",
                    "contraction_factor",
                    "atr_pct",
                    "price",
                )
                if row.get(k) is not None
            },
        }
        candidates.append(cand)

    if karne is None:
        karne_out: dict[str, Any] | None = None
    else:
        karne_out = dict(karne)
        karne_out.setdefault("toplam_aday_bugun", grade_totals)
    if karne_out is None and grade_totals:
        karne_out = {"toplam_aday_bugun": grade_totals, "by_grade": {}, "window": ""}

    snap: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "date": date_str,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "config_sha": config_sha(),
        "universe": int(universe),
        "candidates": candidates,
        "karne": karne_out,
        "warnings": [],
    }

    if not candidates:
        snap["warnings"].append("no graded candidates today")
    if karne is None:
        snap["warnings"].append("karne unavailable — using daily totals only")

    problems = validate_snapshot(snap)
    if problems:
        raise ValueError("snapshot invalid: " + "; ".join(problems))
    return snap


def load_scan_export(path: Path | None = None) -> tuple[list[dict[str, Any]], int, str]:
    """Read the scan export written by the /scan endpoint hook.

    Returns (rows, universe, date_str). Raises FileNotFoundError when missing.
    """
    p = path or SCAN_EXPORT_LATEST
    data = json.loads(Path(p).read_text(encoding="utf-8"))
    rows = data.get("results", [])
    universe = int(data.get("universe") or len(rows))
    date_str = str(data.get("date") or datetime.now(tz=UTC).strftime("%Y-%m-%d"))
    return rows, universe, date_str


def save_snapshot(snap: dict[str, Any], out_dir: Path | None = None) -> Path:
    out = out_dir or EXPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    dated = out / f"snapshot_{snap['date']}.json"
    dated.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "snapshot_latest.json").write_text(
        json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return dated

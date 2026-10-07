"""Separate partial-scan snapshot artifacts for explicitly reviewed editions."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from distribution.scan_contract import expected_universe, result_symbols
from distribution.schema import validate_snapshot
from distribution.snapshot_builder import (
    EXPORT_DIR,
    build_snapshot,
    read_json_object,
    write_snapshot,
)

PARTIAL_SNAPSHOT_DIR = EXPORT_DIR / "partial_snapshots"
PARTIAL_EXPORT_DIR = EXPORT_DIR
_SCAN_ID_RE = re.compile(r"^[0-9a-f]{24}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_date(date_str: str) -> bool:
    if not _DATE_RE.fullmatch(date_str):
        return False
    try:
        date.fromisoformat(date_str)
        return True
    except ValueError:
        return False


def partial_export_path(date_str: str, scan_id: str) -> Path:
    if not _valid_date(date_str) or not _SCAN_ID_RE.fullmatch(scan_id):
        raise ValueError("invalid partial export date or scan_id")
    return PARTIAL_EXPORT_DIR / f"scan_export_{date_str}_partial_{scan_id}.json"


def partial_snapshot_path(date_str: str, scan_id: str, lang: str) -> Path:
    if not _valid_date(date_str) or not _SCAN_ID_RE.fullmatch(scan_id):
        raise ValueError("invalid partial snapshot date or scan_id")
    if lang not in {"tr", "en"}:
        raise ValueError("partial snapshot language must be 'tr' or 'en'")
    return PARTIAL_SNAPSHOT_DIR / f"snapshot_{date_str}_partial_{scan_id}_{lang}.json"


def build_partial_export(
    rows: list[dict[str, Any]],
    *,
    requested_universe: int,
    date_str: str,
    scan_id: str | None = None,
    source_artifacts: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    symbols = result_symbols(rows)
    if not rows or len(symbols) != len(rows):
        raise ValueError("partial scan rows must be non-empty and have unique symbols")
    expected = expected_universe()
    if requested_universe <= 0 or requested_universe > expected:
        raise ValueError("requested_universe must be positive and no larger than expected")
    actual_scan_id = hashlib.sha256("|".join(sorted(symbols)).encode()).hexdigest()[:24]
    if scan_id is not None and scan_id != actual_scan_id:
        raise ValueError("scan_id does not match the result symbol set")
    export = {
        "date": date_str,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "run_id": actual_scan_id,
        "scan_id": actual_scan_id,
        "scan_scope": "partial",
        "scan_complete": False,
        "universe": requested_universe,
        "expected_universe": expected,
        "requested_universe": requested_universe,
        "result_count": len(rows),
        "result_coverage_pct": round(len(symbols) / expected * 100, 1),
        "source_artifacts": source_artifacts or [],
        "results": rows,
    }
    problems = validate_partial_export(export, scan_id=actual_scan_id)
    if problems:
        raise ValueError("partial export invalid: " + "; ".join(problems))
    return export


def validate_partial_export(export: dict[str, Any], scan_id: str | None = None) -> list[str]:
    problems: list[str] = []
    if export.get("scan_scope") != "partial":
        problems.append("scan_scope is not partial")
    date_str = str(export.get("date") or "")
    if not _valid_date(date_str):
        problems.append("partial export date is invalid")
    if export.get("scan_complete") is not False:
        problems.append("partial export must remain scan_complete=false")
    rows = export.get("results")
    if not isinstance(rows, list) or not rows:
        problems.append("partial export results are empty or invalid")
        rows = []
    symbols = result_symbols(rows)
    if len(symbols) != len(rows):
        problems.append("partial export symbols are not unique")
    actual_scan_id = hashlib.sha256("|".join(sorted(symbols)).encode()).hexdigest()[:24]
    if export.get("scan_id") != actual_scan_id or (scan_id and scan_id != actual_scan_id):
        problems.append("partial export scan_id does not match result symbols")

    expected = expected_universe()
    requested = export.get("requested_universe")
    if type(requested) is not int or not 0 < requested <= expected:
        problems.append("partial export requested_universe is invalid")
    if export.get("universe") != requested:
        problems.append("partial export universe differs from requested_universe")
    if export.get("expected_universe") != expected:
        problems.append(f"partial export expected_universe must be {expected}")
    if export.get("result_count") != len(rows):
        problems.append("partial export result_count does not match results")
    if type(requested) is int and len(rows) > requested:
        problems.append("partial export results exceed requested_universe")
    if round(len(symbols) / expected * 100, 1) != export.get("result_coverage_pct"):
        problems.append("partial export coverage does not match result symbols")
    return problems


def save_partial_export(export: dict[str, Any]) -> Path:
    problems = validate_partial_export(export)
    if problems:
        raise ValueError("partial export invalid: " + "; ".join(problems))
    path = partial_export_path(str(export["date"]), str(export["scan_id"]))
    _atomic_write_json(path, export)
    return path


def load_partial_export(date_str: str, scan_id: str) -> dict[str, Any]:
    export = read_json_object(partial_export_path(date_str, scan_id))
    problems = validate_partial_export(export, scan_id=scan_id)
    if problems:
        raise ValueError("partial export invalid: " + "; ".join(problems))
    if export.get("date") != date_str:
        raise ValueError("partial export date differs from queue")
    return export


def build_partial_snapshots(
    rows: list[dict[str, Any]],
    *,
    requested_universe: int,
    date_str: str,
    scan_id: str | None = None,
    karne: dict[str, Any] | None = None,
    source_export: str | None = None,
) -> dict[str, dict[str, Any]]:
    symbols = result_symbols(rows)
    if not rows or len(symbols) != len(rows):
        raise ValueError("partial scan rows must be non-empty and have unique symbols")
    expected = expected_universe()
    if requested_universe <= 0 or requested_universe > expected:
        raise ValueError("requested_universe must be positive and no larger than expected")
    actual_scan_id = hashlib.sha256("|".join(sorted(symbols)).encode()).hexdigest()[:24]
    if scan_id is not None and scan_id != actual_scan_id:
        raise ValueError("scan_id does not match the result symbol set")

    snapshots: dict[str, dict[str, Any]] = {}
    for lang in ("tr", "en"):
        snapshot = build_snapshot(
            rows,
            universe=expected,
            karne=karne,
            date_str=date_str,
            lang=lang,
            scan_id=actual_scan_id,
        )
        snapshot.update(
            {
                "publication_scope": "partial",
                "lang": lang,
                "expected_universe": expected,
                "requested_universe": requested_universe,
                "result_coverage_pct": round(len(symbols) / expected * 100, 1),
                "requested_coverage_pct": round(requested_universe / expected * 100, 1),
                "source_export": source_export,
            }
        )
        snapshot["snapshot_id"] = hashlib.sha256(
            f"partial|{date_str}|{expected}|{requested_universe}|{actual_scan_id}|"
            f"{snapshot['candidate_hash']}".encode()
        ).hexdigest()[:24]
        problems = validate_snapshot(snapshot)
        if problems:
            raise ValueError("partial snapshot invalid: " + "; ".join(problems))
        snapshots[lang] = snapshot

    if snapshots["tr"]["snapshot_id"] != snapshots["en"]["snapshot_id"]:
        raise ValueError("Turkish and English partial snapshots do not share identity")
    return snapshots


def validate_partial_snapshot(snapshot: dict[str, Any], scan_id: str | None = None) -> list[str]:
    problems = validate_snapshot(snapshot)
    if snapshot.get("publication_scope") != "partial":
        problems.append("publication_scope is not partial")
    if snapshot.get("date") is None or not _valid_date(str(snapshot.get("date"))):
        problems.append("partial snapshot date is invalid")
    if scan_id is not None and snapshot.get("scan_id") != scan_id:
        problems.append("scan_id differs")

    expected = expected_universe()
    if snapshot.get("expected_universe") != expected or snapshot.get("universe") != expected:
        problems.append(f"expected_universe must be {expected}")
    requested = snapshot.get("requested_universe")
    if not isinstance(requested, int) or not 0 < requested <= expected:
        problems.append("requested_universe is invalid")
    result_count = snapshot.get("scan_result_count")
    if not isinstance(result_count, int) or result_count <= 0:
        problems.append("scan_result_count is invalid")
    elif isinstance(requested, int) and result_count > requested:
        problems.append("scan_result_count exceeds requested_universe")
    elif round(result_count / expected * 100, 1) != snapshot.get("result_coverage_pct"):
        problems.append("result_coverage_pct does not match scan_result_count")
    if isinstance(requested, int) and round(requested / expected * 100, 1) != snapshot.get(
        "requested_coverage_pct"
    ):
        problems.append("requested_coverage_pct does not match requested_universe")
    candidate_tickers = sorted(
        str(candidate.get("ticker") or "").upper()
        for candidate in snapshot.get("candidates", [])
        if isinstance(candidate, dict)
    )
    candidate_hash = hashlib.sha256("|".join(candidate_tickers).encode()).hexdigest()
    if candidate_hash != snapshot.get("candidate_hash"):
        problems.append("candidate_hash does not match candidates")
    if isinstance(requested, int):
        expected_snapshot_id = hashlib.sha256(
            f"partial|{snapshot.get('date')}|{expected}|{requested}|{snapshot.get('scan_id')}|"
            f"{snapshot.get('candidate_hash')}".encode()
        ).hexdigest()[:24]
        if snapshot.get("snapshot_id") != expected_snapshot_id:
            problems.append("snapshot_id does not match partial snapshot metadata")
    return problems


def save_partial_snapshot(snapshot: dict[str, Any], lang: str) -> Path:
    problems = validate_partial_snapshot(snapshot)
    if problems:
        raise ValueError("partial snapshot invalid: " + "; ".join(problems))
    if snapshot.get("lang") != lang:
        raise ValueError("partial snapshot language differs from requested path")
    path = partial_snapshot_path(str(snapshot["date"]), str(snapshot["scan_id"]), lang)
    write_snapshot(path, snapshot)
    return path


def load_partial_snapshot(date_str: str, scan_id: str, lang: str) -> dict[str, Any]:
    snapshot = read_json_object(partial_snapshot_path(date_str, scan_id, lang))
    problems = validate_partial_snapshot(snapshot, scan_id=scan_id)
    if problems:
        raise ValueError("partial snapshot invalid: " + "; ".join(problems))
    if snapshot.get("date") != date_str:
        raise ValueError("partial snapshot date differs from queue")
    return snapshot


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)
    read_json_object(path)

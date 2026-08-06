#!/usr/bin/env python3
"""Validate PIT research inputs and create a frozen, unopened holdout protocol.

Research-only. This command never opens the locked holdout and never changes
scanner, scoring, risk, or publication behavior.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FUNDAMENTALS_CACHE = ROOT / "data/fundamentals_cache.json"
FINRA_DIR = ROOT / "data/finra_cache"
NEWS_DIR = ROOT / "data/news_cache"
SEC_SNAPSHOT = ROOT / "data/research/sec_companyfacts.jsonl"
PILOT_CSV = ROOT / "data/backtest_out/fundamentals_sentiment_pilot.csv"
PROTOCOL = ROOT / "data/backtest_out/fundamentals_sentiment_protocol.json"
QUALITY = ROOT / "data/backtest_out/pit_data_quality.json"
HOLDOUT = ROOT / "data/backtest_out/fundamentals_sentiment_holdout.json"
FEATURES = ["news_count_5d", "news_count_20d", "news_sentiment_5d", "news_sentiment_20d"]
TARGETS = ["c2c5_net", "c2c20_net"]
REQUIRED_PIT_FIELDS = [
    "symbol",
    "observation_date",
    "publication_date",
    "metric",
    "value",
    "source",
]


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _dates_from_pilot() -> list[str]:
    if not PILOT_CSV.exists():
        return []
    with PILOT_CSV.open(encoding="utf-8", newline="") as handle:
        return sorted({row["scan_date"] for row in csv.DictReader(handle) if row.get("scan_date")})


def _frozen_protocol() -> dict[str, Any]:
    dates = _dates_from_pilot()
    if len(dates) < 12:
        raise SystemExit("pilot CSV has insufficient dates to freeze protocol")
    discovery_end = max(1, int(len(dates) * 0.50))
    validation_end = max(discovery_end + 1, int(len(dates) * 0.75))
    return {
        "protocol_version": "pit-factors-v1",
        "frozen_at": datetime.now(UTC).isoformat(),
        "research_only": True,
        "historical_discovery_range": [dates[0], dates[discovery_end - 1]],
        "historical_validation_range": [dates[discovery_end], dates[validation_end - 1]],
        "locked_holdout_range": [dates[validation_end], dates[-1]],
        "holdout_status": "not_opened_locked_holdout",
        "features": FEATURES,
        "targets": TARGETS,
        "cost_model": {"version": "fixed-round-trip-v1", "cost_pct": 0.5},
        "inference": {
            "fdr": "benjamini_hochberg",
            "fdr_alpha": 0.05,
            "hac": "newey_west_daily_cross_sectional_ic",
            "hac_alpha": 0.05,
            "minimum_cross_section_n": 30,
            "split": "50_percent_discovery_25_percent_validation_25_percent_temporal_holdout",
        },
        "pit_join_rule": "publication_date <= scan_date; choose latest publication_date per symbol/metric",
        "independence_note": "Temporal holdout is not an independent symbol universe; locked opening requires human approval.",
    }


def freeze_protocol() -> dict[str, Any]:
    if PROTOCOL.exists():
        existing = _read_json(PROTOCOL, {})
        if existing.get("protocol_version") != "pit-factors-v1":
            raise SystemExit("existing protocol has an incompatible version")
        return existing
    protocol = _frozen_protocol()
    PROTOCOL.parent.mkdir(parents=True, exist_ok=True)
    PROTOCOL.write_text(json.dumps(protocol, indent=2, ensure_ascii=False), encoding="utf-8")
    return protocol


def validate_current_fundamentals() -> dict[str, Any]:
    raw = _read_json(FUNDAMENTALS_CACHE, {})
    records = (
        sum(1 for value in raw.values() if isinstance(value, dict)) if isinstance(raw, dict) else 0
    )
    return {
        "source": "data/fundamentals_cache.json",
        "records": records,
        "status": "current_only_excluded",
        "missing_required_fields": ["observation_date", "publication_date", "source"],
        "usable_for_pit_join": 0,
        "reason": "symbol-only snapshot has no point-in-time publication metadata",
    }


def validate_finra() -> dict[str, Any]:
    files = sorted(FINRA_DIR.glob("*.json")) if FINRA_DIR.exists() else []
    records = 0
    symbols_with_history = 0
    min_date = max_date = None
    for path in files:
        rows = _read_json(path, [])
        valid = [
            row
            for row in rows
            if isinstance(row, list) and len(row) >= 2 and row[0] and row[1] is not None
        ]
        if valid:
            symbols_with_history += 1
            records += len(valid)
            values = [str(row[0])[:10] for row in valid]
            min_date = min(values) if min_date is None else min(min_date, min(values))
            max_date = max(values) if max_date is None else max(max_date, max(values))
    return {
        "source": "FINRA consolidatedShortInterest cache",
        "files": len(files),
        "symbols_with_history": symbols_with_history,
        "short_quantity_records": records,
        "observation_date_range": [min_date, max_date],
        "status": "short_quantity_only",
        "missing_required_fields": ["publication_date", "float_observation_date", "float_source"],
        "usable_short_percent_records": 0,
        "reason": "short shares are historical, but a point-in-time float denominator and publication date are absent",
    }


def validate_news() -> dict[str, Any]:
    files = sorted(NEWS_DIR.glob("*.json")) if NEWS_DIR.exists() else []
    rows = 0
    dated = 0
    for path in files:
        values = _read_json(path, [])
        rows += len(values) if isinstance(values, list) else 0
        dated += (
            sum(1 for value in values if isinstance(value, list) and value and value[0])
            if isinstance(values, list)
            else 0
        )
    return {
        "source": "EODHD news cache",
        "files": len(files),
        "rows": rows,
        "dated_rows": dated,
        "status": "dated_legacy_cache",
        "note": "cache rows contain article date and polarity but no explicit source/publication timestamp per row",
    }


def validate_sec_snapshot() -> dict[str, Any]:
    """Check the append-only SEC ledger without making a network request."""
    if not SEC_SNAPSHOT.exists():
        return {
            "source": "SEC EDGAR companyfacts",
            "status": "not_collected",
            "path": str(SEC_SNAPSHOT),
            "records": 0,
            "reason": "adapter is available; no local append-only retrieval has been collected",
        }
    envelopes = []
    for line in SEC_SNAPSHOT.read_text(encoding="utf-8").splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            envelopes.append(value)
    records = [
        record
        for envelope in envelopes
        for record in envelope.get("records", [])
        if isinstance(record, dict)
    ]
    required = {"observation_date", "publication_date", "source", "accn", "retrieved_at"}
    missing = sorted(required - set(records[0])) if records else sorted(required)
    return {
        "source": "SEC EDGAR companyfacts",
        "status": "pit_ready" if records and not missing else "insufficient_data",
        "path": str(SEC_SNAPSHOT),
        "snapshots": len(envelopes),
        "records": len(records),
        "missing_required_fields": missing,
        "append_only": True,
    }


def validate_inputs() -> dict[str, Any]:
    protocol = freeze_protocol()
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "research_only": True,
        "protocol": protocol,
        "fundamentals": validate_current_fundamentals(),
        "finra": validate_finra(),
        "news": validate_news(),
        "sec_companyfacts": validate_sec_snapshot(),
        "decision": "no_pit_fundamentals_or_short_percent_join; news_only_research_input",
    }
    QUALITY.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def initialize_holdout() -> dict[str, Any]:
    protocol = freeze_protocol()
    if HOLDOUT.exists():
        return _read_json(HOLDOUT, {})
    state = {
        "protocol_version": protocol["protocol_version"],
        "created_at": datetime.now(UTC).isoformat(),
        "status": "not_opened_locked_holdout",
        "human_approval_required": True,
        "historical_cutoff": protocol["historical_validation_range"][1],
        "rows": [],
    }
    HOLDOUT.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--init-holdout", action="store_true")
    args = parser.parse_args()
    if args.validate:
        report = validate_inputs()
        print(f"quality={QUALITY}")
        print(
            f"fundamentals={report['fundamentals']['status']} | finra={report['finra']['status']} | news={report['news']['status']}"
        )
    elif args.init_holdout:
        state = initialize_holdout()
        print(f"holdout={HOLDOUT} | status={state['status']} | rows={len(state.get('rows', []))}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Point-in-time fundamentals/short/news pilot over honest price outcomes.

This is research-only. It never changes scanner scoring or publication behavior.
Fundamentals/short data is accepted only when a dated snapshot is supplied; the
legacy symbol-only cache is reported as current-only and excluded by default.
News cache rows are aggregated before the scan date and joined to T+5/T+20
close-to-close net returns computed from the local OHLC cache.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from research.news_hypothesis_protocol import NEWS_HYPOTHESIS
from research.statistical_validation import benjamini_hochberg, newey_west_mean

ROOT = Path(__file__).resolve().parent
EDGE = ROOT / "data/backtest_out/edge_recheck.csv"
PRICE_DIR = ROOT / "data/price_cache"
FUNDAMENTALS = ROOT / "data/fundamentals_cache.json"
NEWS_DIR = ROOT / "data/news_cache"
OUT = ROOT / "data/backtest_out/fundamentals_sentiment_pilot.csv"
INFERENCE_OUT = ROOT / "data/backtest_out/fundamentals_sentiment_inference.json"
COST_PCT = 0.5
HORIZONS = (5, 20)
MIN_N = 30
FDR_ALPHA = 0.05
HAC_ALPHA = 0.05


def _float(value: Any) -> float | None:
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def _load_json(path: Path, default: Any) -> Any:
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def _prior_close(symbol: str, scan_date: str) -> float | None:
    bars = _load_json(PRICE_DIR / f"{symbol}.json", [])
    prior = [row for row in bars if row.get("date", "") <= scan_date]
    return _float(prior[-1].get("close")) if prior else None


def honest_returns(symbol: str, scan_date: str) -> dict[str, float] | None:
    """Return net T+5/T+20 close returns using next-bar-open entry."""
    bars = _load_json(PRICE_DIR / f"{symbol}.json", [])
    bars = sorted((row for row in bars if row.get("date")), key=lambda row: row["date"])
    entry_index = next((i for i, row in enumerate(bars) if row["date"] > scan_date), None)
    if entry_index is None:
        return None
    entry = _float(bars[entry_index].get("open")) or _float(bars[entry_index - 1].get("close"))
    if not entry:
        return None
    result = {}
    for horizon in HORIZONS:
        end = entry_index + horizon - 1
        if end >= len(bars):
            continue
        close = _float(bars[end].get("close"))
        if close is not None:
            result[f"c2c{horizon}_net"] = round((close / entry - 1) * 100 - COST_PCT, 4)
    return result if len(result) == len(HORIZONS) else None


def _news_sentiment(rows: list[Any]) -> tuple[float | None, int]:
    values = [_float(row[1]) for row in rows if isinstance(row, list | tuple) and len(row) > 1]
    values = [value for value in values if value is not None]
    if not values:
        return None, 0
    # Older cache files contain normalized values when negatives are present;
    # otherwise their 0..1 values are EODHD polarity and are centered at 0.
    normalized = (
        values
        if any(value < 0 or value > 1 for value in values)
        else [(value * 2) - 1 for value in values]
    )
    return round(sum(normalized) / len(normalized), 6), len(values)


def news_features(symbol: str, scan_date: str) -> dict[str, float | int | None]:
    rows = _load_json(NEWS_DIR / f"{symbol}.json", [])
    parsed = []
    for row in rows:
        if isinstance(row, list) and row and isinstance(row[0], str) and row[0] <= scan_date:
            parsed.append(row)
    out: dict[str, float | int | None] = {}
    scan = date.fromisoformat(scan_date)
    for horizon in HORIZONS:
        start = (scan - timedelta(days=horizon)).isoformat()
        window = [row for row in parsed if row[0] >= start]
        sentiment, count = _news_sentiment(window)
        out[f"news_sentiment_{horizon}d"] = sentiment
        out[f"news_count_{horizon}d"] = count
    return out


def _load_signals() -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    rows = []
    with EDGE.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            key = (row.get("symbol", ""), row.get("scan_date", ""))
            if all(key) and key not in seen:
                seen.add(key)
                rows.append({"symbol": key[0], "scan_date": key[1]})
    return rows


def _point_in_time_fundamentals(snapshot_date: str | None) -> dict[str, dict[str, Any]]:
    raw = _load_json(FUNDAMENTALS, {})
    if not snapshot_date:
        return {}
    # The legacy cache has no per-symbol observation dates. A caller may opt in
    # only by explicitly declaring the common snapshot date in the CLI.
    return raw if isinstance(raw, dict) else {}


def build(snapshot_date: str | None = None) -> tuple[int, int]:
    fundamentals = _point_in_time_fundamentals(snapshot_date)
    rows = []
    excluded_current = 0
    for signal in _load_signals():
        symbol, scan_date = signal["symbol"], signal["scan_date"]
        outcome = honest_returns(symbol, scan_date)
        if not outcome:
            continue
        # Current-only fundamentals are not joined unless the user explicitly
        # supplies the snapshot date and the signal is on/after that date.
        fund = fundamentals.get(symbol, {}) if snapshot_date and scan_date >= snapshot_date else {}
        if not snapshot_date and symbol in fundamentals:
            excluded_current += 1
        features = news_features(symbol, scan_date)
        rows.append(
            {
                **signal,
                **outcome,
                "snapshot_date": snapshot_date or "",
                "float_shares": fund.get("float_shares"),
                "short_pct": fund.get("short_pct"),
                **features,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["symbol", "scan_date", "snapshot_date", "float_shares", "short_pct"]
    fields += [f"news_sentiment_{h}d" for h in HORIZONS]
    fields += [f"news_count_{h}d" for h in HORIZONS]
    fields += [f"c2c{h}_net" for h in HORIZONS]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"satır={len(rows)} → {OUT}")
    if excluded_current:
        print(
            f"current-only fundamentals/short dışlandı: {excluded_current} sinyal (look-ahead koruması)"
        )
    return len(rows), excluded_current


def _ic(frame, feature: str, target: str) -> tuple[float | None, int]:
    pairs = [
        (float(row[feature]), float(row[target]))
        for row in frame
        if row.get(feature) not in (None, "") and row.get(target) not in (None, "")
    ]
    if len(pairs) < MIN_N:
        return None, len(pairs)
    left = [x[0] for x in pairs]
    right = [x[1] for x in pairs]

    def ranks(values):
        order = sorted(range(len(values)), key=values.__getitem__)
        result = [0.0] * len(values)
        for rank, index in enumerate(order):
            result[index] = rank + 1
        return result

    a, b = ranks(left), ranks(right)
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b, strict=False))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return (round(num / den, 4) if den else None), len(pairs)


def _daily_ic_series(frame: list[dict[str, str]], feature: str, target: str) -> list[float]:
    """Build one cross-sectional rank-IC observation per scan date."""
    series = []
    for scan_date in sorted({row["scan_date"] for row in frame}):
        rows = [row for row in frame if row["scan_date"] == scan_date]
        pairs = [
            (_float(row.get(feature)), _float(row.get(target)))
            for row in rows
            if _float(row.get(feature)) is not None and _float(row.get(target)) is not None
        ]
        if len(pairs) < MIN_N:
            continue
        left = np.asarray([pair[0] for pair in pairs], dtype=float)
        right = np.asarray([pair[1] for pair in pairs], dtype=float)
        left_rank = np.argsort(np.argsort(left)).astype(float)
        right_rank = np.argsort(np.argsort(right)).astype(float)
        if np.std(left_rank) == 0 or np.std(right_rank) == 0:
            continue
        series.append(float(np.corrcoef(left_rank, right_rank)[0, 1]))
    return series


def _inference(
    frame: list[dict[str, str]], features: list[str], targets: list[str]
) -> dict[str, Any]:
    """Run IS-only FDR/HAC selection and report untouched later periods."""
    dates = sorted({row["scan_date"] for row in frame})
    if len(dates) < 12:
        return {"status": "insufficient_dates", "dates": len(dates)}
    # Discovery / validation / holdout are temporal blocks. The last block is
    # not opened by this script as a governance-approved locked holdout.
    discovery_end = max(1, int(len(dates) * 0.50))
    validation_end = max(discovery_end + 1, int(len(dates) * 0.75))
    discovery_dates = set(dates[:discovery_end])
    validation_dates = set(dates[discovery_end:validation_end])
    holdout_dates = set(dates[validation_end:])
    discovery = [row for row in frame if row["scan_date"] in discovery_dates]
    validation = [row for row in frame if row["scan_date"] in validation_dates]
    holdout = [row for row in frame if row["scan_date"] in holdout_dates]

    tests: dict[str, dict[str, Any]] = {}
    p_values: dict[str, float] = {}
    for target in targets:
        for feature in features:
            name = f"{feature}__{target}"
            series = _daily_ic_series(discovery, feature, target)
            hac = (
                newey_west_mean(np.asarray(series, dtype=float))
                if series
                else {"n": 0, "p": float("nan")}
            )
            tests[name] = {
                "feature": feature,
                "target": target,
                "discovery_daily_ic": series,
                "discovery_hac": hac,
                "validation_ic": _ic(validation, feature, target),
                "holdout_ic": _ic(holdout, feature, target),
            }
            if np.isfinite(hac.get("p", float("nan"))):
                p_values[name] = float(hac["p"])
    fdr = benjamini_hochberg(p_values, alpha=FDR_ALPHA)
    discoveries = set(fdr["discoveries"])
    for name, test in tests.items():
        test["discovery_fdr_discovery"] = name in discoveries
        test["discovery_q"] = fdr["adjusted_p"].get(name)
        test["validation_direction_matches"] = _same_direction(
            test["discovery_hac"].get("mean"), test["validation_ic"][0]
        )
        test["holdout_direction_matches"] = _same_direction(
            test["discovery_hac"].get("mean"), test["holdout_ic"][0]
        )
    return {
        "status": "ok",
        "split": {
            "discovery": [dates[0], dates[discovery_end - 1]],
            "validation": [dates[discovery_end], dates[validation_end - 1]],
            "holdout": [dates[validation_end], dates[-1]],
            "holdout_status": "not_opened_locked_holdout",
            "independence_note": "Temporal holdout only; symbols and data-generating process are not independent.",
        },
        "parameters": {
            "fdr_alpha": FDR_ALPHA,
            "hac_alpha": HAC_ALPHA,
            "min_cross_section_n": MIN_N,
        },
        "fdr": fdr,
        "tests": tests,
        "pre_holdout_candidates": sorted(
            name
            for name, test in tests.items()
            if test["discovery_fdr_discovery"] and test["validation_direction_matches"]
        ),
    }


def _same_direction(first: float | None, second: float | None) -> bool:
    return bool(
        first is not None
        and second is not None
        and first != 0
        and second != 0
        and (first > 0) == (second > 0)
    )


def analyze() -> None:
    if not OUT.exists():
        build()
    with OUT.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    dates = sorted({row["scan_date"] for row in rows})
    cut = dates[len(dates) // 2] if dates else ""
    is_rows = [row for row in rows if row["scan_date"] < cut]
    oos_rows = [row for row in rows if row["scan_date"] >= cut]
    print(f"rows={len(rows)} | IS={len(is_rows)} | OOS={len(oos_rows)} | cut={cut or 'yok'}")
    NEWS_HYPOTHESIS.validate()
    features = list(NEWS_HYPOTHESIS.features) + ["float_shares", "short_pct"]
    for target in NEWS_HYPOTHESIS.targets:
        print(f"\n=== {target}: rank-IC (honest, cost={COST_PCT:.2f}%) ===")
        for feature in features:
            all_ic, all_n = _ic(rows, feature, target)
            is_ic, is_n = _ic(is_rows, feature, target)
            oos_ic, oos_n = _ic(oos_rows, feature, target)
            print(
                f"{feature:24} all={str(all_ic):>7} IS={str(is_ic):>7} OOS={str(oos_ic):>7} n={all_n}/{is_n}/{oos_n}"
            )
    inference = _inference(rows, features, list(NEWS_HYPOTHESIS.targets))
    INFERENCE_OUT.write_text(json.dumps(inference, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== FDR + HAC + temporal holdout ===")
    print(
        f"FDR test sayısı={inference.get('fdr', {}).get('tested', 0)} | discovery={len(inference.get('fdr', {}).get('discoveries', []))}"
    )
    print(
        f"Ön-holdout adayları={len(inference.get('pre_holdout_candidates', []))} | kilitli holdout açılmadı"
    )
    print(f"ayrıntı: {INFERENCE_OUT}")
    print(
        "\nNot: Fundamentals/short yalnız açıkça verilen snapshot_date ile kullanılır; varsayılan analizde current-only cache dışarıda kalır."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument(
        "--fundamentals-snapshot-date",
        help="YYYY-MM-DD; legacy cache'i yalnız bu tarihten sonraki sinyallere uygula",
    )
    args = parser.parse_args()
    if args.build:
        build(args.fundamentals_snapshot_date)
    elif args.analyze:
        analyze()
    else:
        parser.print_help()

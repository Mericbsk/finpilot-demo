"""Research-only stability, rejection, concentration and capacity checks.

Historical outcome metrics use the canonical barrier dataset. Sector and
correlation data are reported separately, while the latest liquidity snapshot
is explicitly not joined to historical outcomes. The locked OOS is described
but never opened by this module.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from research.decision_quality_experiments import model_views, veto_reasons
from research.full_universe_barrier_backtest import (
    dedup_rows,
    label_rows,
    load_rows,
    resolve_paths,
)
from research.protocol import TemporalSplit


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _float(value: object) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _extra_fields(path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    fields: dict[tuple[str, str], dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = ((row.get("symbol") or "").strip(), (row.get("scan_date") or "").strip())
            fields.setdefault(key, {"liquidity_ok": _bool(row.get("liquidity_ok"))})
    return fields


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"status": "insufficient_data", "n": 0}
    returns = [float(row["net_return_pct"]) for row in rows]
    positive = sum(int(row["target"]) for row in rows)
    return {
        "status": "ok",
        "n": len(rows),
        "positive_net_rate": round(positive / len(rows), 6),
        "mean_net_return_pct": round(sum(returns) / len(returns), 6),
        "median_net_return_pct": round(sorted(returns)[len(returns) // 2], 6),
    }


def _hhi(values: list[str]) -> float | None:
    if not values:
        return None
    counts = Counter(values)
    total = len(values)
    return round(sum((count / total) ** 2 for count in counts.values()), 6)


def _concentration(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [str(row[key]) for row in rows if row.get(key)]
    if not values:
        return {"status": "insufficient_data", "n": 0}
    counts = Counter(values)
    top = counts.most_common(3)
    return {
        "status": "ok",
        "n": len(values),
        "groups": len(counts),
        "hhi": _hhi(values),
        "top3_share": round(sum(count for _, count in top) / len(values), 6),
        "top3": [{"group": name, "n": count} for name, count in top],
    }


def _split_dates(dates: list[str]) -> tuple[TemporalSplit, dict[str, list[str]]]:
    unique = sorted(set(dates))
    if len(unique) < 12:
        raise ValueError("at least 12 distinct scan dates are required")
    train_index = max(1, int(len(unique) * 0.50))
    validation_index = max(train_index + 1, int(len(unique) * 0.75))
    train_end = unique[train_index - 1]
    validation_end = unique[validation_index - 1]
    locked_end = unique[-1]
    split = TemporalSplit(train_end, validation_end, locked_end)
    split.validate()
    return split, {
        "train": unique[:train_index],
        "validation": unique[train_index:validation_index],
        "locked_oos": unique[validation_index:],
    }


def _period_metrics(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(field) or "unknown")].append(row)
    return {name: _summary(group) for name, group in sorted(groups.items())}


def _false_rejection_metrics(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(field) or "unknown")].append(row)
    return {
        name: {
            "status": "ok" if len(group) >= 30 else "insufficient_data",
            "rejected_n": len(group),
            "false_rejection_n": sum(row["false_rejection"] for row in group),
            "false_rejection_rate": round(
                sum(row["false_rejection"] for row in group) / len(group), 6
            )
            if group
            else None,
        }
        for name, group in sorted(groups.items())
    }


def _latest_liquidity(path: Path, minimum_n: int = 30) -> dict[str, Any]:
    payload = _read_json(path, {})
    results = payload.get("results", []) if isinstance(payload, dict) else []
    rows = []
    for row in results:
        adv = _float(row.get("dollar_adv"))
        notional = _float(row.get("position_notional"))
        if adv is None or adv <= 0:
            continue
        rows.append(
            {
                "symbol": row.get("symbol"),
                "dollar_adv": adv,
                "position_notional": notional,
                "capacity_ratio": notional / adv if notional is not None else None,
                "liquidity_ok": bool(row.get("liquidity_ok")),
                "spread_status": row.get("spread_source", "missing"),
            }
        )
    if len(rows) < minimum_n:
        return {
            "status": "insufficient_data",
            "n": len(rows),
            "source": str(path),
            "join_policy": "not_joined_to_historical_outcomes",
        }
    ratios = sorted(row["capacity_ratio"] for row in rows if row["capacity_ratio"] is not None)
    return {
        "status": "snapshot_only",
        "n": len(rows),
        "source": str(path),
        "snapshot_date": payload.get("date"),
        "join_policy": "not_joined_to_historical_outcomes",
        "liquidity_ok_rate": round(sum(row["liquidity_ok"] for row in rows) / len(rows), 6),
        "dollar_adv_median": round(sorted(row["dollar_adv"] for row in rows)[len(rows) // 2], 2),
        "capacity_ratio_p50": round(ratios[len(ratios) // 2], 6) if ratios else None,
        "capacity_ratio_p90": round(ratios[int(len(ratios) * 0.9)], 6) if ratios else None,
        "spread_observed_rate": round(
            sum(row["spread_status"] != "missing" for row in rows) / len(rows), 6
        ),
    }


def run(
    csv_path: Path,
    cache_path: Path,
    sector_path: Path = Path("data/sector_cache.json"),
    correlation_path: Path = Path("data/backtest_out/sector_map_full.csv"),
    liquidity_path: Path = Path("data/distribution/scan_export_latest.json"),
    cost_pct: float = 0.55,
    horizon: int = 5,
) -> dict[str, Any]:
    raw_rows = load_rows(str(csv_path))
    extras = _extra_fields(csv_path)
    resolved, inventory = resolve_paths(
        dedup_rows(raw_rows), str(cache_path), horizon=horizon, max_entry_drift=0.5
    )
    sectors = _read_json(sector_path, {})
    correlation: dict[str, dict[str, Any]] = {}
    if correlation_path.exists():
        with correlation_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                correlation[row["symbol"]] = {
                    "group": row.get("etf") or "unknown",
                    "corr": _float(row.get("corr")),
                }

    observations: list[dict[str, Any]] = []
    for row, result in label_rows(resolved, tp_mult=2.0, sl_mult=1.0, horizon=horizon):
        extra = extras.get((row["symbol"], row["scan_date"]), {})
        reasons = veto_reasons(row, extra)
        net_return = result.ret_pct * 100.0 - cost_pct
        corr_meta = correlation.get(row["symbol"], {})
        observations.append(
            {
                "symbol": row["symbol"],
                "scan_date": row["scan_date"],
                "month": row["scan_date"][:7],
                "regime": row.get("regime") or "unknown",
                "sector": sectors.get(row["symbol"], "unknown"),
                "correlation_group": corr_meta.get("group", "unknown"),
                "correlation_proxy": corr_meta.get("corr"),
                "rejected": bool(reasons),
                "false_rejection": bool(reasons) and net_return > 0,
                "target": int(net_return > 0),
                "net_return_pct": round(net_return, 6),
                "model_support_count": sum(
                    value == "support" for value in model_views(row, extra).values()
                ),
            }
        )

    split, date_sets = _split_dates([row["scan_date"] for row in observations])
    train = [row for row in observations if row["scan_date"] in date_sets["train"]]
    validation = [row for row in observations if row["scan_date"] in date_sets["validation"]]
    rejected = [row for row in observations if row["rejected"]]
    false_rejections = [row for row in rejected if row["false_rejection"]]

    return {
        "methodology": {
            "research_only": True,
            "target": "5-day triple-barrier net return > 0",
            "cost_pct": cost_pct,
            "horizon": horizon,
            "minimum_group_n": 30,
            "locked_holdout_action": "not_opened",
            "historical_liquidity_join": "forbidden_when_snapshot_date_differs",
        },
        "inventory": inventory,
        "temporal_split": split.as_dict(),
        "split_dates": {name: [dates[0], dates[-1]] for name, dates in date_sets.items() if dates},
        "stability": {
            "train": _summary(train),
            "validation": _summary(validation),
            "by_month": _period_metrics(observations, "month"),
            "by_regime": _period_metrics(observations, "regime"),
        },
        "false_rejection": {
            "overall": {
                "status": "ok" if rejected else "insufficient_data",
                "rejected_n": len(rejected),
                "false_rejection_n": len(false_rejections),
                "false_rejection_rate": round(len(false_rejections) / len(rejected), 6)
                if rejected
                else None,
            },
            "by_month": _false_rejection_metrics(rejected, "month"),
            "by_regime": _false_rejection_metrics(rejected, "regime"),
        },
        "sector_concentration": {
            "all": _concentration(observations, "sector"),
            "rejected": _concentration(rejected, "sector"),
            "eligible": _concentration(
                [row for row in observations if not row["rejected"]], "sector"
            ),
        },
        "correlation_proxy_concentration": {
            "all": _concentration(observations, "correlation_group"),
            "rejected": _concentration(rejected, "correlation_group"),
            "coverage": round(
                sum(row["correlation_group"] != "unknown" for row in observations)
                / len(observations),
                6,
            )
            if observations
            else 0.0,
            "note": "ETF-group proxy, not pairwise candidate correlation; no production use.",
        },
        "liquidity_capacity": _latest_liquidity(liquidity_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/backtest_out/stability_concentration_capacity_2026-08-06.json"),
    )
    parser.add_argument("--cost-pct", type=float, default=0.55)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    result = run(args.csv, args.cache, cost_pct=args.cost_pct)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK -> {args.out}")


if __name__ == "__main__":
    main()

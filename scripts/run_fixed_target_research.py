"""Run the pre-registered fixed-target return research protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.full_universe_barrier_backtest import (  # noqa: E402
    dedup_rows,
    load_rows,
    resolve_paths,
)
from research.protocol import CostModel, FERRecord, TemporalSplit  # noqa: E402
from research.statistical_validation import (  # noqa: E402
    benjamini_hochberg,
    cpcv_pbo,
    deflated_sharpe,
    hansen_spa,
    newey_west_mean,
    white_reality_check,
)
from scanner.labeling import triple_barrier_label  # noqa: E402
from scripts.run_full_universe_research import candidate_definitions  # noqa: E402

TARGETS = (0.03, 0.05, 0.07, 0.10)
FIXED_STOPS = (0.02, 0.03, 0.05)
ATR_STOPS = (1.0, 1.5, 2.0)
HORIZONS = (1, 3, 5, 10, 20)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _finite(values: list[float] | np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array[np.isfinite(array)]


def _period_stats(
    values: np.ndarray, dates: list[str], end: str, start: str | None = None
) -> dict[str, float | int]:
    mask = np.array([date <= end and (start is None or date > start) for date in dates], dtype=bool)
    clean = _finite(values[mask])
    return {
        "n": int(clean.size),
        "status": "ok" if clean.size else "insufficient_data",
        "mean_net_return_pct": float(np.mean(clean) * 100) if clean.size else float("nan"),
        "median_net_return_pct": float(np.median(clean) * 100) if clean.size else float("nan"),
    }


def _config_key(
    candidate: str, target: float, stop_name: str, stop_value: float, horizon: int
) -> str:
    return f"{candidate}|tp={target:.2%}|{stop_name}={stop_value:g}|h={horizon}"


def _label_returns(
    rows: list[dict[str, Any]], target: float, stop_name: str, stop_value: float, horizon: int
) -> dict[str, np.ndarray]:
    returns = np.full(len(rows), np.nan, dtype=float)
    labels = np.full(len(rows), "missing", dtype=object)
    for index, row in enumerate(rows):
        path = row["forward"][:horizon]
        if len(path) < horizon:
            continue
        stop = stop_value if stop_name == "fixed_stop" else stop_value * row["atr_pct"] / 100.0
        label = triple_barrier_label(
            [bar["close"] for bar in path],
            entry_price=row["entry"],
            tp_pct=target,
            sl_pct=stop,
            max_horizon=horizon,
            forward_highs=[bar["high"] for bar in path],
            forward_lows=[bar["low"] for bar in path],
        )
        returns[index] = label.ret_pct
        labels[index] = label.label
    return {"returns": returns, "labels": labels}


def _daily_matrix(
    returns: np.ndarray,
    selected: np.ndarray,
    row_dates: list[str],
    unique_dates: list[str],
) -> np.ndarray:
    grouped: dict[str, list[float]] = defaultdict(list)
    for value, is_selected, date_value in zip(returns, selected, row_dates, strict=True):
        if is_selected and np.isfinite(value):
            grouped[date_value].append(float(value))
    return np.array(
        [
            float(np.mean(grouped[date_value])) if grouped.get(date_value) else np.nan
            for date_value in unique_dates
        ],
        dtype=float,
    )


def _summarize(
    values: np.ndarray,
    labels: np.ndarray,
    dates: list[str],
    train_end: str,
    validation_end: str,
    cost_bps: tuple[float, ...],
    trials: int,
) -> dict[str, Any]:
    clean = _finite(values)
    counts = {name: int(np.sum(labels == name)) for name in ("tp", "sl", "time", "missing")}
    gross = {
        "n": int(clean.size),
        "mean_return_pct": float(np.mean(clean) * 100) if clean.size else float("nan"),
        "cost_sensitivity": {
            str(bps): {
                "mean_net_return_pct": float(np.mean(clean - bps / 10000) * 100)
                if clean.size
                else float("nan"),
                "median_net_return_pct": float(np.median(clean - bps / 10000) * 100)
                if clean.size
                else float("nan"),
                "positive_mean_and_median": bool(
                    clean.size
                    and np.mean(clean - bps / 10000) > 0
                    and np.median(clean - bps / 10000) > 0
                ),
            }
            for bps in cost_bps
        },
        "median_return_pct": float(np.median(clean) * 100) if clean.size else float("nan"),
        "tp_rate": counts["tp"] / clean.size if clean.size else float("nan"),
        "sl_rate": counts["sl"] / clean.size if clean.size else float("nan"),
        "time_rate": counts["time"] / clean.size if clean.size else float("nan"),
        "hac_newey_west": newey_west_mean(clean),
        "deflated_sharpe": deflated_sharpe(clean, trials=trials),
        "label_counts": counts,
    }
    return {
        "gross": gross,
        "train": _period_stats(values, dates, train_end),
        "validation": _period_stats(values, dates, validation_end, train_end),
        "cost_sensitivity": {
            str(bps): {
                "mean_net_return_pct": float(np.mean(clean - bps / 10000) * 100)
                if clean.size
                else float("nan"),
                "median_net_return_pct": float(np.median(clean - bps / 10000) * 100)
                if clean.size
                else float("nan"),
                "positive_mean_and_median": bool(
                    clean.size
                    and np.mean(clean - bps / 10000) > 0
                    and np.median(clean - bps / 10000) > 0
                ),
            }
            for bps in cost_bps
        },
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    csv_path = args.root / args.csv
    cache_path = args.root / args.cache
    raw_rows = load_rows(str(csv_path))
    canonical = dedup_rows(raw_rows)
    resolved, path_stats = resolve_paths(
        canonical, str(cache_path), max(HORIZONS), args.max_entry_drift
    )
    candidates = candidate_definitions()
    candidate_masks = {
        name: np.array([predicate(row) for row in resolved], dtype=bool)
        for name, predicate in candidates.items()
    }
    dates = [row["scan_date"] for row in resolved]
    unique_dates = sorted(set(dates))
    month_coverage = {
        month: sum(date_value.startswith(month) for date_value in dates)
        for month in sorted({date_value[:7] for date_value in dates})
    }
    split_coverage = {
        "train_rows": sum(date_value <= args.train_end for date_value in dates),
        "validation_rows": sum(
            args.train_end < date_value <= args.validation_end for date_value in dates
        ),
        "locked_oos_rows_unopened": sum(date_value > args.validation_end for date_value in dates),
    }
    cost_bps = tuple(sorted(set(args.cost_bps)))
    configurations: dict[str, Any] = {}
    p_values: dict[str, float] = {}
    daily_columns: list[np.ndarray] = []
    daily_names: list[str] = []
    total_configs = (
        len(candidates) * len(TARGETS) * (len(FIXED_STOPS) + len(ATR_STOPS)) * len(HORIZONS)
    )

    for target in TARGETS:
        for stop_name, stop_values in (("fixed_stop", FIXED_STOPS), ("atr_stop", ATR_STOPS)):
            for stop_value in stop_values:
                for horizon in HORIZONS:
                    labeled = _label_returns(resolved, target, stop_name, stop_value, horizon)
                    for candidate, selected in candidate_masks.items():
                        key = _config_key(candidate, target, stop_name, stop_value, horizon)
                        values = np.where(selected, labeled["returns"], np.nan)
                        summary = _summarize(
                            values,
                            np.where(selected, labeled["labels"], "missing"),
                            dates,
                            args.train_end,
                            args.validation_end,
                            cost_bps,
                            total_configs,
                        )
                        configurations[key] = {
                            "candidate": candidate,
                            "target_pct": target * 100,
                            "stop_type": stop_name,
                            "stop_value": stop_value,
                            "horizon": horizon,
                            **summary,
                        }
                        p_values[key] = float(summary["gross"]["hac_newey_west"]["p"])
                        daily_names.append(key)
                        daily_columns.append(_daily_matrix(values, selected, dates, unique_dates))

    daily_matrix = np.column_stack(daily_columns) if daily_columns else np.empty((0, 0))
    split = TemporalSplit(args.train_end, args.validation_end, args.locked_oos_end)
    split_status: dict[str, Any] = {"status": "ok"}
    try:
        split.validate()
    except ValueError as exc:
        split_status = {"status": "insufficient_data", "reason": str(exc)}
    cost_status = {
        "status": "insufficient_data",
        "reason": "observed spread/impact cost fields are unavailable",
    }
    try:
        cost = CostModel(args.cost_model_version, None, None, None, None)
        FERRecord(
            experiment_id=args.experiment_id,
            hypothesis=args.hypothesis,
            economic_rationale=args.economic_rationale,
            data_snapshot=f"sha256:{sha256_file(csv_path)}",
            date_range=f"{min(dates)}..{max(dates)}" if dates else "",
            split=split,
            factors=tuple(candidates),
            pairwise_tests=0,
            triple_tests=0,
            max_interaction_order=1,
            cost_model=cost,
            n_trials=total_configs,
            status="insufficient_data",
        ).validate()
        cost_status = {"status": "ok"}
    except ValueError as exc:
        cost_status["reason"] = str(exc)

    holdout_path = args.root / args.holdout_state
    holdout_status = {
        "status": "already_opened" if holdout_path.exists() else "not_opened",
        "state_path": str(holdout_path),
        "runner_action": "read_only",
        "opening_requires_human_approval": True,
    }
    fdr = benjamini_hochberg(p_values, alpha=args.fdr_alpha)
    discoveries = set(fdr["discoveries"])
    eligible = [
        key
        for key, item in configurations.items()
        if key in discoveries
        and item["gross"]["mean_return_pct"] > 0
        and item["gross"]["median_return_pct"] > 0
        and item["train"]["mean_net_return_pct"] > 0
        and item["train"]["median_net_return_pct"] > 0
        and item["train"]["n"] >= args.min_period_n
        and item["validation"]["mean_net_return_pct"] > 0
        and item["validation"]["median_net_return_pct"] > 0
        and item["validation"]["n"] >= args.min_period_n
        and item["gross"]["deflated_sharpe"]["dsr"] >= args.min_dsr
    ]
    cost_eligible = [
        key
        for key in eligible
        if any(
            configurations[key]["cost_sensitivity"][str(bps)]["positive_mean_and_median"]
            for bps in cost_bps
        )
    ]
    pbo = cpcv_pbo(
        daily_matrix, unique_dates, args.cpcv_groups, args.cpcv_test_groups, args.purge_days
    )
    report = {
        "research_only": True,
        "experiment_id": args.experiment_id,
        "protocol": {
            "fixed_targets_pct": [target * 100 for target in TARGETS],
            "fixed_stops_pct": [stop * 100 for stop in FIXED_STOPS],
            "atr_stops": list(ATR_STOPS),
            "horizons_bars": list(HORIZONS),
            "configuration_count": total_configs,
            "cost_scenarios_bps": list(cost_bps),
        },
        "dataset": {
            "csv": str(csv_path),
            "csv_sha256": sha256_file(csv_path),
            "raw_rows": len(raw_rows),
            "canonical_rows": len(canonical),
            "path_resolved_rows": len(resolved),
            "date_range": {
                "min": min(dates) if dates else None,
                "max": max(dates) if dates else None,
            },
            "month_coverage": month_coverage,
            "split_coverage": split_coverage,
            "path_stats": path_stats,
            "cost_status": cost_status,
        },
        "gates": {
            "temporal_split": split_status,
            "fer": cost_status,
            "locked_holdout": holdout_status,
        },
        "fdr": fdr,
        "cpcv_pbo": pbo,
        "white_reality_check": white_reality_check(
            daily_matrix, args.bootstrap_repetitions, args.block_size
        ),
        "hansen_spa": hansen_spa(daily_matrix, args.bootstrap_repetitions, args.block_size),
        "qualification": {
            "gross_and_period_stable": eligible,
            "cost_positive": cost_eligible,
            "final_verdict": "none_qualified_locked_holdout_not_opened"
            if not cost_eligible
            else "pending_locked_holdout",
        },
        "configurations": configurations,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    protocol = report["protocol"]
    dataset = report["dataset"]
    qualification = report["qualification"]
    configurations = report["configurations"]
    ranked = sorted(
        configurations.items(),
        key=lambda pair: pair[1]["gross"]["median_return_pct"],
        reverse=True,
    )[:25]
    lines = [
        "# Fixed-Target Full-Universe Research",
        "",
        f"- Experiment: `{report['experiment_id']}`",
        "- Scope: research-only; no production rule change",
        f"- Configurations: `{protocol['configuration_count']}`",
        f"- Targets: `{protocol['fixed_targets_pct']}%`",
        f"- Fixed stops: `{protocol['fixed_stops_pct']}%`; ATR stops: `{protocol['atr_stops']}x ATR`",
        f"- Horizons: `{protocol['horizons_bars']}` bars",
        f"- Data: `{dataset['raw_rows']}` raw, `{dataset['canonical_rows']}` canonical, `{dataset['path_resolved_rows']}` path-resolved",
        f"- Date range: `{dataset['date_range']['min']}..{dataset['date_range']['max']}`",
        f"- Month coverage: `{dataset['month_coverage']}`",
        f"- Split coverage: `{dataset['split_coverage']}`",
        "- Observed transaction costs: `insufficient_data`; cost values below are scenarios, not observations",
        "",
        "## Gates",
        "",
        f"- FDR discoveries: `{len(report['fdr']['discoveries'])}`",
        f"- CPCV/PBO: `{report['cpcv_pbo']['pbo']}` across `{len(report['cpcv_pbo']['paths'])}` paths",
        f"- White Reality Check p: `{report['white_reality_check']['p']}`",
        f"- Hansen SPA p: `{report['hansen_spa']['p']}`",
        f"- Gross + train/validation stable: `{len(qualification['gross_and_period_stable'])}`",
        f"- Cost-positive: `{len(qualification['cost_positive'])}`",
        f"- Locked holdout: `{report['gates']['locked_holdout']['status']}`; not opened by runner",
        "",
        "## Highest-Median Configurations",
        "",
        "| Configuration | n | Mean % | Median % | Train median % | Validation median % | HAC p | DSR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, item in ranked:
        gross = item["gross"]
        lines.append(
            f"| `{key}` | {gross['n']} | {gross['mean_return_pct']:.3f} | {gross['median_return_pct']:.3f} | "
            f"{item['train']['median_net_return_pct']:.3f} | {item['validation']['median_net_return_pct']:.3f} | "
            f"{gross['hac_newey_west']['p']:.6f} | {gross['deflated_sharpe']['dsr']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Final Interpretation",
            "",
            f"- Gross and period-stable configurations: `{qualification['gross_and_period_stable']}`",
            f"- Configurations positive after declared cost scenarios: `{qualification['cost_positive']}`",
            "- A locked holdout result is not claimed because the one-time holdout was not opened.",
            "- Missing observed spread, slippage, impact, and point-in-time execution fields remain blocking conditions.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--csv", type=Path, default=Path("data/backtest_out/full_universe_enriched.csv")
    )
    parser.add_argument("--cache", type=Path, default=Path("data/price_cache"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--economic-rationale", required=True)
    parser.add_argument("--train-end", required=True)
    parser.add_argument("--validation-end", required=True)
    parser.add_argument("--locked-oos-end", required=True)
    parser.add_argument(
        "--holdout-state", type=Path, default=Path("data/backtest_out/locked_holdout_opened.json")
    )
    parser.add_argument("--max-entry-drift", type=float, default=0.50)
    parser.add_argument("--cost-bps", type=float, nargs="+", default=(10.0, 25.0, 50.0, 100.0))
    parser.add_argument("--cost-model-version", default="research-cost-v1")
    parser.add_argument("--fdr-alpha", type=float, default=0.05)
    parser.add_argument("--min-dsr", type=float, default=0.95)
    parser.add_argument("--min-period-n", type=int, default=50)
    parser.add_argument("--cpcv-groups", type=int, default=6)
    parser.add_argument("--cpcv-test-groups", type=int, default=2)
    parser.add_argument("--purge-days", type=int, default=20)
    parser.add_argument("--bootstrap-repetitions", type=int, default=200)
    parser.add_argument("--block-size", type=int, default=5)
    args = parser.parse_args()
    report = run(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report), encoding="utf-8")
    json_out = args.json_out or args.out.with_suffix(".json")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"report={args.out}")
    print(f"json={json_out}")


if __name__ == "__main__":
    main()

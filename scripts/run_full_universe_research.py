"""Run the requested statistical research methods on the full universe."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.full_universe_barrier_backtest import (  # noqa: E402
    dedup_rows,
    label_rows,
    load_bars,
    load_rows,
    resolve_paths,
)
from research.protocol import CostModel, FERRecord, TemporalSplit  # noqa: E402
from research.statistical_validation import (  # noqa: E402
    benjamini_hochberg,
    cpcv_pbo,
    deflated_sharpe,
    gaussian_hmm_two_state,
    hansen_spa,
    newey_west_mean,
    white_reality_check,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_definitions() -> dict[str, Any]:
    """Return the pre-registered candidate family; do not add post hoc rules."""
    definitions = {
        "all": lambda row: True,
        "entry_ok": lambda row: row["entry_ok"],
    }
    for threshold in (3, 4, 5, 6, 7):
        definitions[f"ATR>={threshold}"] = (
            lambda row, threshold=threshold: row["atr_pct"] >= threshold
        )
    for threshold in (34, 40, 47, 52, 58):
        definitions[f"composite>={threshold}"] = (
            lambda row, threshold=threshold: row["composite"] is not None
            and row["composite"] >= threshold
        )
    for atr in (4, 6):
        for composite in (34, 40, 47):
            definitions[f"ATR>={atr}+composite>={composite}"] = (
                lambda row, atr=atr, composite=composite: row["atr_pct"] >= atr
                and row["composite"] is not None
                and row["composite"] >= composite
            )
    for atr in (4, 6):
        for rvol in (1.5, 2.0):
            definitions[f"ATR>={atr}+RVOL>={rvol:g}"] = (
                lambda row, atr=atr, rvol=rvol: row["atr_pct"] >= atr
                and row["rvol"] is not None
                and row["rvol"] >= rvol
            )
    for atr in (4, 6):
        for gap in (2, 3):
            definitions[f"ATR>={atr}+gap>{gap}"] = (
                lambda row, atr=atr, gap=gap: row["atr_pct"] >= atr
                and row["gap"] is not None
                and row["gap"] > gap
            )
    return definitions


def build_candidate_matrix(
    labeled: list[tuple[dict[str, Any], Any]],
) -> tuple[list[str], list[str], np.ndarray]:
    available_predicates = candidate_definitions()
    names = list(available_predicates)
    dates = [row["scan_date"] for row, _ in labeled]
    matrix = np.full((len(labeled), len(names)), np.nan, dtype=float)
    for row_index, (row, result) in enumerate(labeled):
        for candidate_index, name in enumerate(names):
            if available_predicates[name](row):
                matrix[row_index, candidate_index] = float(result.ret_pct)
    return names, dates, matrix


def candidate_summaries(
    names: list[str],
    matrix: np.ndarray,
    trials: int,
    cost_bps: tuple[float, ...],
) -> tuple[dict[str, Any], dict[str, float]]:
    summaries: dict[str, Any] = {}
    p_values: dict[str, float] = {}
    for index, name in enumerate(names):
        values = matrix[:, index]
        clean = values[np.isfinite(values)]
        inference = newey_west_mean(clean)
        summaries[name] = {
            "n": int(clean.size),
            "mean_return_pct": float(np.mean(clean) * 100) if clean.size else float("nan"),
            "median_return_pct": float(np.median(clean) * 100) if clean.size else float("nan"),
            "hac_newey_west": inference,
            "deflated_sharpe": deflated_sharpe(clean, trials=trials),
            "cost_sensitivity": {
                str(bps): {
                    "mean_return_pct": float(np.mean(clean - bps / 10000) * 100)
                    if clean.size
                    else float("nan"),
                    "median_return_pct": float(np.median(clean - bps / 10000) * 100)
                    if clean.size
                    else float("nan"),
                    "positive_mean": bool(np.mean(clean - bps / 10000) > 0)
                    if clean.size
                    else False,
                    "positive_median": bool(np.median(clean - bps / 10000) > 0)
                    if clean.size
                    else False,
                }
                for bps in cost_bps
            },
        }
        p_values[name] = float(inference["p"])
    return summaries, p_values


def period_candidate_summary(
    names: list[str],
    matrix: np.ndarray,
    dates: list[str],
    end_date: str,
    start_date: str | None = None,
) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    period_mask = np.array(
        [date <= end_date and (start_date is None or date > start_date) for date in dates],
        dtype=bool,
    )
    for index, name in enumerate(names):
        values = matrix[period_mask, index]
        clean = values[np.isfinite(values)]
        summary[name] = {
            "n": int(clean.size),
            "mean_return_pct": float(np.mean(clean) * 100) if clean.size else float("nan"),
            "median_return_pct": float(np.median(clean) * 100) if clean.size else float("nan"),
        }
    return summary


def run(args: argparse.Namespace) -> dict[str, Any]:
    csv_path = args.root / args.csv
    cache_path = args.root / args.cache
    rows = load_rows(str(csv_path))
    canonical = dedup_rows(rows)
    resolved, path_stats = resolve_paths(
        canonical, str(cache_path), args.horizon, args.max_entry_drift
    )
    labeled = label_rows(resolved, args.tp_mult, args.sl_mult, args.horizon)
    names, dates, matrix = build_candidate_matrix(labeled)
    cost_bps = tuple(sorted(set(args.cost_bps)))
    summaries, p_values = candidate_summaries(names, matrix, trials=len(names), cost_bps=cost_bps)
    train_summary = period_candidate_summary(names, matrix, dates, args.train_end)
    validation_summary = period_candidate_summary(
        names, matrix, dates, args.validation_end, args.train_end
    )

    split = TemporalSplit(args.train_end, args.validation_end, args.locked_oos_end)
    split_status: dict[str, Any] = {"status": "ok"}
    try:
        split.validate()
    except ValueError as exc:
        split_status = {"status": "insufficient_data", "reason": str(exc)}

    cost = CostModel(args.cost_model_version, None, None, None, None)
    fer_status = {
        "status": "insufficient_data",
        "reason": "observed spread/impact cost fields are unavailable",
    }
    try:
        FERRecord(
            experiment_id=args.experiment_id,
            hypothesis=args.hypothesis,
            economic_rationale=args.economic_rationale,
            data_snapshot=f"sha256:{sha256_file(csv_path)}",
            date_range=f"{min(dates)}..{max(dates)}" if dates else "",
            split=split,
            factors=tuple(names),
            pairwise_tests=0,
            triple_tests=0,
            max_interaction_order=1,
            cost_model=cost,
            n_trials=len(names),
            status="insufficient_data",
        ).validate()
        fer_status = {"status": "ok"}
    except ValueError as exc:
        fer_status["reason"] = str(exc)

    holdout_path = args.root / args.holdout_state
    holdout_status = {
        "status": "already_opened" if holdout_path.exists() else "not_opened",
        "state_path": str(holdout_path),
        "runner_action": "read_only",
    }

    hmm_bars = load_bars(str(cache_path), args.hmm_symbol)
    close_values = np.array(
        [float(bar["close"]) for bar in hmm_bars if bar.get("close")], dtype=float
    )
    hmm_returns = np.diff(np.log(close_values)) if close_values.size > 1 else np.array([])
    report = {
        "research_only": True,
        "experiment_id": args.experiment_id,
        "dataset": {
            "csv": str(csv_path),
            "csv_sha256": sha256_file(csv_path),
            "cache": str(cache_path),
            "raw_rows": len(rows),
            "canonical_rows": len(canonical),
            "path_resolved_rows": len(resolved),
            "labeled_rows": len(labeled),
            "date_range": {
                "min": min(dates) if dates else None,
                "max": max(dates) if dates else None,
            },
            "canonical_policy": "earliest row per symbol-day",
            "path_stats": path_stats,
            "label": f"{args.horizon}-bar triple barrier, TP={args.tp_mult}x ATR, SL={args.sl_mult}x ATR",
            "cost_status": "insufficient_data",
            "cost_sensitivity_scenarios_bps": list(cost_bps),
        },
        "gates": {
            "temporal_split": split_status,
            "fer": fer_status,
            "locked_holdout": holdout_status,
        },
        "candidates": summaries,
        "periods": {"train": train_summary, "validation": validation_summary},
        "qualification": qualification_summary(
            summaries, names, matrix, dates, train_summary, validation_summary, args
        ),
        "program_wide_fdr": benjamini_hochberg(p_values, alpha=args.fdr_alpha),
        "cpcv_pbo": cpcv_pbo(
            matrix, dates, args.cpcv_groups, args.cpcv_test_groups, args.purge_days
        ),
        "white_reality_check": white_reality_check(
            matrix, args.bootstrap_repetitions, args.block_size
        ),
        "hansen_spa": hansen_spa(matrix, args.bootstrap_repetitions, args.block_size),
        "hmm_regime_full": {
            "symbol": args.hmm_symbol,
            "bars": len(hmm_bars),
            "returns": len(hmm_returns),
            "result": gaussian_hmm_two_state(hmm_returns),
        },
    }
    return report


def qualification_summary(
    summaries: dict[str, Any],
    names: list[str],
    matrix: np.ndarray,
    dates: list[str],
    train_summary: dict[str, dict[str, float | int]],
    validation_summary: dict[str, dict[str, float | int]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    fdr = benjamini_hochberg(
        {name: summaries[name]["hac_newey_west"]["p"] for name in names},
        alpha=args.fdr_alpha,
    )
    fdr_discoveries = set(fdr["discoveries"])
    qualified = []
    for index, name in enumerate(names):
        values = matrix[:, index]
        clean = values[np.isfinite(values)]
        if clean.size < args.min_candidate_n:
            continue
        item = summaries[name]
        if (
            item["mean_return_pct"] > 0
            and item["median_return_pct"] > 0
            and train_summary[name]["mean_return_pct"] > 0
            and train_summary[name]["median_return_pct"] > 0
            and validation_summary[name]["mean_return_pct"] > 0
            and validation_summary[name]["median_return_pct"] > 0
            and name in fdr_discoveries
            and item["hac_newey_west"]["p"] <= args.hac_alpha
            and item["deflated_sharpe"]["dsr"] >= args.min_dsr
        ):
            qualified.append(name)
    return {
        "criteria": {
            "gross_positive_mean": True,
            "gross_positive_median": True,
            "train_positive_mean_and_median": True,
            "validation_positive_mean_and_median": True,
            "cost_positive": False,
            "fdr_alpha": args.fdr_alpha,
            "hac_alpha": args.hac_alpha,
            "max_pbo": args.max_pbo,
            "min_dsr": args.min_dsr,
            "min_candidate_n": args.min_candidate_n,
            "locked_holdout": "not_opened",
        },
        "pre_holdout_qualified_gross": qualified,
        "cost_gate": "blocked_missing_observed_cost_fields",
        "pbo_gate": "program-level only; candidate-level PBO paths are retained in cpcv_pbo",
        "locked_holdout_gate": "blocked_until_human_approval",
    }


def render_markdown(report: dict[str, Any]) -> str:
    dataset = report["dataset"]
    gates = report["gates"]
    fdr = report["program_wide_fdr"]
    lines = [
        "# Full-Universe Statistical Research",
        "",
        f"- Experiment: `{report['experiment_id']}`",
        "- Scope: research-only; no production rule or publication change",
        f"- Raw rows: `{dataset['raw_rows']}`",
        f"- Canonical rows: `{dataset['canonical_rows']}`",
        f"- Path-resolved rows: `{dataset['path_resolved_rows']}`",
        f"- Date range: `{dataset['date_range']['min']}..{dataset['date_range']['max']}`",
        f"- Label: `{dataset['label']}`",
        "- Net-cost verdict: `insufficient_data` because observed spread/impact are unavailable",
        f"- Cost scenarios tested (not observed): `{dataset['cost_sensitivity_scenarios_bps']} bps`",
        "",
        "## Gates",
        "",
        f"- Temporal split: `{gates['temporal_split']['status']}`",
        f"- FER: `{gates['fer']['status']}`",
        f"- Locked holdout: `{gates['locked_holdout']['status']}`; runner is read-only",
        "",
        "## Requested Methods",
        "",
        f"- CPCV paths: `{len(report['cpcv_pbo']['paths'])}`; PBO: `{report['cpcv_pbo']['pbo']}`",
        f"- White Reality Check p-value: `{report['white_reality_check']['p']}`",
        f"- Hansen SPA p-value: `{report['hansen_spa']['p']}`",
        f"- Program-wide FDR tests: `{fdr['tested']}`; discoveries: `{fdr['discoveries']}`",
        "- HAC/Newey-West: calculated per candidate in the JSON companion",
        "- DSR: calculated per candidate in the JSON companion",
        f"- HMM Regime Full: `{report['hmm_regime_full']['result'].get('status')}`",
        f"- Pre-holdout gross candidates passing mean/median/FDR/HAC/DSR gates: `{report['qualification']['pre_holdout_qualified_gross']}`",
        "",
        "## Candidate Summary",
        "",
        "| Candidate | n | Mean return % | Median return % | HAC p | DSR |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, item in report["candidates"].items():
        hac = item["hac_newey_west"]
        dsr = item["deflated_sharpe"]
        lines.append(
            f"| `{name}` | {item['n']} | {item['mean_return_pct']:.4f} | "
            f"{item['median_return_pct']:.4f} | {hac['p']:.6f} | {dsr['dsr']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "These are full-universe research statistics on path-aware labels, not a production approval.",
            "The candidate matrix uses zero return for an unselected row only in bootstrap reality checks;",
            "the per-candidate HAC/DSR results use selected observations only.",
            "Missing spread, impact, point-in-time event data, and the unopened locked holdout remain blocking conditions.",
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
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--tp-mult", type=float, default=5.0)
    parser.add_argument("--sl-mult", type=float, default=1.5)
    parser.add_argument("--max-entry-drift", type=float, default=0.50)
    parser.add_argument("--cpcv-groups", type=int, default=6)
    parser.add_argument("--cpcv-test-groups", type=int, default=2)
    parser.add_argument("--purge-days", type=int, default=5)
    parser.add_argument("--bootstrap-repetitions", type=int, default=200)
    parser.add_argument("--block-size", type=int, default=5)
    parser.add_argument("--fdr-alpha", type=float, default=0.05)
    parser.add_argument("--hmm-symbol", default="SPY")
    parser.add_argument("--cost-model-version", default="research-cost-v1")
    parser.add_argument("--cost-bps", type=float, nargs="+", default=(10.0, 25.0, 50.0, 100.0))
    parser.add_argument("--min-candidate-n", type=int, default=200)
    parser.add_argument("--hac-alpha", type=float, default=0.05)
    parser.add_argument("--min-dsr", type=float, default=0.95)
    parser.add_argument("--max-pbo", type=float, default=0.10)
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
